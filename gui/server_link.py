"""
Server-Verbindung
=================

Verbindet die GUI explizit mit dem einen sproject-Server (MCP über HTTP,
gestartet mit bin/mcp_server.* --port). Der Server hält das Projekt; GUI und
Claude Code sind beide Clients. So gibt es nie zwei Projekte nebeneinander.

Der MCP-Client läuft in einem Hintergrund-Thread mit eigener asyncio-Schleife.
Dear PyGui wird nur im Hauptthread angefasst: process() wird pro Frame aus der
Render-Schleife (gui/app.py) aufgerufen und erledigt höchstens einen Auftrag zugleich.

Abgleich (ca. jede Sekunde, nicht während ein Eingabefeld aktiv ist):
- GUI → Server: geänderter GUI-Stand → replace_project(data, base_revision)
- Server → GUI: get_revision() geändert → get_state() → editor.apply_external_project()
- Konflikt (beide geändert): der Server gewinnt, die Statuszeile meldet es.

Projektwechsel (das ganze Projekt wird ersetzt):
- Öffnet/legt die GUI ein anderes Projekt an, geht es OHNE base_revision an den Server –
  der sichert den bisherigen Stand und lehnt Claudes nächsten Aufruf mit einer Meldung ab.
- Ersetzt Claude das Projekt, zeigt die GUI einen Hinweis-Dialog mit dem Sicherungspfad.
- Gehen dabei (oder bei einem Konflikt) noch nicht übertragene GUI-Eingaben verloren,
  sichert die GUI sie vorher in $PV_WORK/backup.
"""

import asyncio
import json
import os
import subprocess
import threading
import time
from concurrent.futures import Future
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import dearpygui.dearpygui as dpg

from gui.i18n import t
from lib.api import write_backup
from lib.models import load_project_from_dict
from lib.paths import PROJECT_ROOT
from mcp_server.server import SERVER_NAME, port_in_use

if TYPE_CHECKING:
    from mcp import ClientSession

    from gui.editor import ProjectEditorApp

POLL_INTERVAL_S = 1.0
START_TIMEOUT_S = 15.0

# confirm(nachricht, bei_ja, bei_nein) – Rückfrage; inform(nachricht) – Hinweis (in der GUI modale Dialoge)
Confirm = Callable[[str, Callable[[], None], Callable[[], None]], None]
Inform = Callable[[str], None]


class ServerError(Exception):
    """Der Server hat einen Werkzeugaufruf abgelehnt (fachlicher Fehler, Verbindung besteht weiter)."""


class ServerLink:
    """Verbindung der GUI zum sproject-Server: disconnected → (starting →) connecting → connected."""

    def __init__(self, editor: "ProjectEditorApp", host: str = "127.0.0.1", port: int = 8765,
                 confirm: Optional[Confirm] = None, inform: Optional[Inform] = None,
                 on_status_change: Optional[Callable[[bool], None]] = None):
        self.editor = editor
        self.host = host
        self.port = port
        self.confirm: Confirm = confirm or (lambda _message, yes, _no: yes())   # ohne GUI: immer ja
        self.inform: Inform = inform or (lambda _message: None)
        self.backup_dir: Optional[Path] = None   # None = $PV_WORK/backup (lib.api.backup_dir)
        self.on_status_change = on_status_change
        self.state = "disconnected"
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._session: Optional["ClientSession"] = None
        self._closed: Optional[asyncio.Event] = None
        self._pending: Optional[Tuple[str, Future]] = None
        self._revision = 0                       # zuletzt bekannter Server-Stand
        self._generation = 0                     # zuletzt bekannter Wechselzähler des Servers
        self._editor_generation = 0              # editor.project_generation beim letzten Abgleich
        self._conflict_backup: Optional[str] = None
        self._synced: Optional[str] = None       # GUI-Stand (JSON), der diesem Server-Stand entspricht
        self._rejected: Optional[str] = None     # vom Server abgelehnter GUI-Stand (nicht erneut senden)
        self._push: Tuple[int, str] = (0, "")    # (base_revision, JSON) des laufenden Sendens
        self._deferred: Optional[Dict[str, Any]] = None   # Server-Stand, der auf Tipp-Pause wartet
        self._conflict = False                            # beim nächsten Übernehmen Konflikt melden
        self._next_poll = 0.0
        self._start_deadline = 0.0

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"

    @property
    def connected(self) -> bool:
        return self.state == "connected"

    # ------------------------------------------------------------------
    # Verbinden, Starten, Trennen
    # ------------------------------------------------------------------

    def server_running(self) -> bool:
        return port_in_use(self.host, self.port)

    def connect(self) -> bool:
        """Verbindung aufbauen. False, wenn unter host:port nichts lauscht (dann ggf. start_server())."""
        if self.state != "disconnected":
            return True
        if not self.server_running():
            self.editor._set_status(t("status.server_not_found", url=self.url))
            return False
        self._open()
        return True

    def start_server(self) -> None:
        """Startet bin/mcp_server.* --port als eigenen Prozess (läuft nach GUI-Ende weiter) und verbindet danach."""
        if os.name == "nt":
            cmd = ["cmd", "/c", str(PROJECT_ROOT / "bin" / "mcp_server.bat"), "--port", str(self.port)]
            subprocess.Popen(cmd, cwd=PROJECT_ROOT, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        else:
            cmd = ["bash", str(PROJECT_ROOT / "bin" / "mcp_server.sh"), "--port", str(self.port)]
            subprocess.Popen(cmd, cwd=PROJECT_ROOT, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.state = "starting"
        self._start_deadline = time.monotonic() + START_TIMEOUT_S
        self.editor._set_status(t("status.server_starting", url=self.url))

    def disconnect(self, status_key: Optional[str] = "status.server_disconnected", **kwargs: Any) -> None:
        """Trennt die Verbindung; der Server läuft weiter, die GUI arbeitet lokal weiter."""
        loop, closed, thread = self._loop, self._closed, self._thread
        if loop is not None and closed is not None and not loop.is_closed():
            loop.call_soon_threadsafe(closed.set)
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5)
        was_connected = self.state != "disconnected"
        self.state = "disconnected"
        self._loop = self._thread = self._session = self._closed = None
        self._pending = None
        self._deferred = None
        if status_key and was_connected:
            self.editor._set_status(t(status_key, **kwargs))
        self._notify()

    # ------------------------------------------------------------------
    # Hauptthread: einmal pro Frame
    # ------------------------------------------------------------------

    def process(self, now: Optional[float] = None) -> None:
        now = time.monotonic() if now is None else now
        if self.state == "starting":
            if self.server_running():
                self._open()
            elif now > self._start_deadline:
                self.state = "disconnected"
                self.editor._set_status(t("status.server_start_failed", port=self.port))
            return
        if self._pending is not None:
            kind, future = self._pending
            if not future.done():
                return
            self._pending = None
            try:
                result = future.result()
            except ServerError as e:
                self._on_server_error(kind, str(e))
            except BaseException as e:      # Verbindung weg (Server beendet, Netzwerk …)
                self.disconnect("status.server_lost", error=_short(e))
            else:
                self._on_result(kind, result)
            return
        if self.connected and now >= self._next_poll:
            self._next_poll = now + POLL_INTERVAL_S
            self._tick()

    def _tick(self) -> None:
        if self._input_active():
            return                                   # nicht beim Tippen synchronisieren
        if self._deferred is not None:
            state, self._deferred = self._deferred, None
            self._apply_pulled(state)
            return
        local = self._local_json()
        if local is not None and local != self._rejected:
            if self.editor.project_generation != self._editor_generation:
                # In der GUI wurde ein anderes Projekt geöffnet/angelegt → Projektwechsel auf dem Server
                self._editor_generation = self.editor.project_generation
                self._push = (self._revision, local)
                self._request("switch", "replace_project", {"data": json.loads(local)})
                return
            if local != self._synced:
                self._push = (self._revision, local)
                self._request("push", "replace_project",
                              {"data": json.loads(local), "base_revision": self._revision})
                return
        self._request("poll", "get_revision", {})

    def _on_result(self, kind: str, result: Any) -> None:
        if kind == "init":
            if result != SERVER_NAME:
                self.disconnect("status.server_not_sproject", url=self.url)
                return
            self._request("initial", "get_state", {})
        elif kind == "initial":
            self._on_initial_state(result)
        elif kind == "poll":
            if result != self._revision:
                self._request("pull", "get_state", {})
        elif kind == "pull":
            if self._input_active():
                self._deferred = result              # erst übernehmen, wenn nicht mehr getippt wird
            else:
                self._apply_pulled(result)
        elif kind == "push":
            base, sent = self._push
            self._revision = base + 1
            self._synced = sent
            self._rejected = None
        elif kind == "switch":
            self._synced = self._push[1]
            self._rejected = None
            self._request("resync", "get_state", {})
        elif kind == "resync":
            self._revision = result["revision"]          # eigener Wechsel: nur Zähler übernehmen
            replaced = result["generation"] != self._generation and result.get("last_switch")
            self._generation = result["generation"]
            if replaced:
                switch = result["last_switch"]
                text = t("text.server_switch", old=switch["old"], new=switch["new"], backup=switch["backup"])
                self.editor._set_status(t("status.server_replaced_by_gui", text=text))

    def _on_server_error(self, kind: str, message: str) -> None:
        if kind == "push" and "Konflikt" in message:
            self._conflict = True                    # Meldung erst nach dem Übernehmen (_apply)
            self._request("pull", "get_state", {})
        elif kind in ("push", "switch"):
            self._rejected = self._push[1]
            self.editor._set_status(t("status.server_rejected", error=message))
        else:
            self.disconnect("status.server_lost", error=message)

    def _on_initial_state(self, state: Dict[str, Any]) -> None:
        def connected() -> None:
            self.state = "connected"
            self._next_poll = 0.0
            self._notify()
            name = self.editor.project.project if self.editor.project else "–"
            self.editor._set_status(t("status.server_connected", url=self.url, name=name))

        self._revision = state["revision"]
        self._generation = state.get("generation", 0)
        self._editor_generation = self.editor.project_generation
        if state["project"] is None:
            # Server noch leer → GUI-Projekt wird beim ersten Abgleich übertragen
            self._synced = None
            connected()
            return

        def take_server_project(discard_local: bool = False) -> None:
            backup = self._backup_local() if discard_local else None
            self._apply(state)
            connected()
            if backup:
                self.editor._set_status(t("status.server_local_backup", path=backup))

        if self.editor.project is not None and self.editor.dirty:
            self.confirm(t("dialog.server.discard"), lambda: take_server_project(discard_local=True),
                         lambda: self.disconnect(status_key=None))
        else:
            take_server_project()

    def _apply_pulled(self, state: Dict[str, Any]) -> None:
        switch = state.get("last_switch")
        foreign_switch = switch is not None and switch["generation"] > self._generation
        local_backup = None
        if self._local_json() != self._synced:      # noch nicht übertragene GUI-Eingaben gingen verloren
            local_backup = self._backup_local()
            if not foreign_switch:
                self._conflict = True
                self._conflict_backup = local_backup
        self._apply(state)
        if foreign_switch and switch is not None:
            text = t("text.server_switch", old=switch["old"], new=switch["new"], backup=switch["backup"])
            self.editor._set_status(t("status.server_switched", text=text))
            message = t("dialog.server.switched", text=text)
            if local_backup:
                message += "\n\n" + t("dialog.server.local_backup", path=local_backup)
            self.inform(message)

    def _apply(self, state: Dict[str, Any]) -> None:
        if state["project"] is None:
            return
        path = Path(state["path"]) if state.get("path") else None
        self.editor.apply_external_project(load_project_from_dict(state["project"]), path)
        self._revision = state["revision"]
        self._generation = state.get("generation", self._generation)
        self._synced = self._local_json()            # GUI-Darstellung dieses Stands
        self._rejected = None
        if self._conflict:
            self._conflict = False
            backup, self._conflict_backup = self._conflict_backup, None
            self.editor._set_status(t("status.server_conflict") +
                                    (" " + t("status.server_local_backup", path=backup) if backup else ""))

    # ------------------------------------------------------------------
    # Hilfen
    # ------------------------------------------------------------------

    def _local_json(self) -> Optional[str]:
        """Aktueller GUI-Stand als kanonisches JSON (übernimmt vorher die Eingaben ins Modell)."""
        self.editor.sync_to_model()
        project = self.editor.project
        if project is None:
            return None
        data = project.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)
        return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def _backup_local(self) -> Optional[str]:
        """Sichert den aktuellen GUI-Stand (vor dem Verwerfen) – Pfad oder None."""
        if self.editor.project is None:
            return None
        try:
            return str(write_backup(self.editor.project, self.backup_dir))
        except OSError as e:
            self.editor._set_status(t("status.server_backup_failed", error=e))
            return None

    @staticmethod
    def _input_active() -> bool:
        try:
            item = dpg.get_focused_item()
            return bool(item) and bool(dpg.is_item_active(item))
        except Exception:
            return False

    def _notify(self) -> None:
        if self.on_status_change:
            self.on_status_change(self.connected)

    # ------------------------------------------------------------------
    # Hintergrund-Thread: MCP-Client
    # ------------------------------------------------------------------

    def _open(self) -> None:
        self.state = "connecting"
        self.editor._set_status(t("status.server_connecting", url=self.url))
        loop = asyncio.new_event_loop()
        ready: Future = Future()
        self._loop = loop
        self._thread = threading.Thread(target=self._run_loop, args=(loop, ready), name="sproject-link", daemon=True)
        self._thread.start()
        self._pending = ("init", ready)

    def _run_loop(self, loop: asyncio.AbstractEventLoop, ready: Future) -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._session_main(ready))
        finally:
            loop.close()

    async def _session_main(self, ready: Future) -> None:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        closed = asyncio.Event()
        self._closed = closed
        try:
            async with streamable_http_client(self.url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    info = await session.initialize()
                    self._session = session
                    ready.set_result(info.serverInfo.name)
                    await closed.wait()
        except BaseException as e:      # noqa: BLE001 – Fehler gehen über ready bzw. offene Aufrufe an process()
            if not ready.done():
                ready.set_exception(e)
        finally:
            self._session = None

    def _request(self, kind: str, tool: str, args: Dict[str, Any]) -> None:
        self._pending = (kind, self._call(tool, args))

    def _call(self, tool: str, args: Dict[str, Any]) -> Future:
        session, loop = self._session, self._loop
        if session is None or loop is None or loop.is_closed():
            failed: Future = Future()
            failed.set_exception(ConnectionError(t("status.server_disconnected")))
            return failed

        async def run() -> Any:
            from mcp.types import TextContent

            result = await session.call_tool(tool, args)
            if result.isError:
                raise ServerError(" ".join(c.text for c in result.content if isinstance(c, TextContent)) or tool)
            return (result.structuredContent or {}).get("result")

        return asyncio.run_coroutine_threadsafe(run(), loop)


def _short(error: BaseException) -> str:
    """Erste aussagekräftige Fehlermeldung (auch aus ExceptionGroups von anyio).

    Ohne BaseExceptionGroup (erst ab Python 3.11) – erkennt Gruppen am Attribut "exceptions".
    """
    inner = getattr(error, "exceptions", None)
    while isinstance(inner, tuple) and inner:
        error = inner[0]
        inner = getattr(error, "exceptions", None)
    return str(error) or type(error).__name__
