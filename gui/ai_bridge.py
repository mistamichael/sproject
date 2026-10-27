"""
KI-Brücke
=========

Startet den MCP-Server (mcp_server/) aus der laufenden GUI als HTTP-Dienst auf
127.0.0.1, damit Claude Code & Co. das geöffnete Projekt live bearbeiten können.

Der Server läuft in einem Hintergrund-Thread. Jeder Werkzeugaufruf wird in eine
Queue gestellt und im DPG-Hauptthread ausgeführt (process_pending() pro Frame):
dort werden zuerst die GUI-Eingaben ins Modell übernommen, nach einer Änderung
wird die GUI neu aufgebaut. Dear PyGui wird so nie aus einem Fremd-Thread berührt.
"""

import queue
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

from lib.api import ProjectSession
from lib.paths import get_cfg_dir

if TYPE_CHECKING:
    import uvicorn

    from gui.editor import ProjectEditorApp

CALL_TIMEOUT_S = 120


class _GuiSession(ProjectSession):
    """ProjectSession, die beim Speichern den Editor als gespeichert markiert."""

    def __init__(self, editor: "ProjectEditorApp"):
        super().__init__(cfg_dir=get_cfg_dir())
        self.editor = editor

    def save(self, path: Union[str, Path, None] = None) -> str:
        target = super().save(path)
        self.editor.mark_saved(Path(target))
        return target


class AiBridge:
    def __init__(self, editor: "ProjectEditorApp", host: str = "127.0.0.1", port: int = 8765):
        self.editor = editor
        self.host = host
        self.port = port
        self.session = _GuiSession(editor)
        self._jobs: "queue.Queue[Tuple[Callable[[], Any], Future]]" = queue.Queue()
        self._server: Optional["uvicorn.Server"] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self.running:
            return
        import uvicorn

        from mcp_server.server import build_server

        mcp = build_server(self.session, runner=self._run_in_gui, host=self.host, port=self.port)
        config = uvicorn.Config(mcp.streamable_http_app(), host=self.host, port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, name="mcp-server", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None

    # ------------------------------------------------------------------
    # Aufrufe zwischen den Threads
    # ------------------------------------------------------------------

    def _run_in_gui(self, func: Callable[[], Any]) -> Any:
        """Server-Thread: stellt func in die Queue und wartet auf das Ergebnis aus dem Hauptthread."""
        future: Future = Future()
        self._jobs.put((func, future))
        return future.result(timeout=CALL_TIMEOUT_S)

    def process_pending(self) -> None:
        """Hauptthread, einmal pro Frame: offene Werkzeugaufrufe ausführen."""
        while True:
            try:
                func, future = self._jobs.get_nowait()
            except queue.Empty:
                return
            if not future.set_running_or_notify_cancel():
                continue
            try:
                future.set_result(self._execute(func))
            except BaseException as e:      # Fehler gehen als Werkzeug-Fehler an den Client
                future.set_exception(e)

    def _execute(self, func: Callable[[], Any]) -> Any:
        editor = self.editor
        editor.sync_to_model()                 # ungespeicherte GUI-Eingaben sichtbar machen
        self.session.project = editor.project
        self.session.path = editor.last_save_path
        before = self.session.project
        try:
            return func()
        finally:
            if self.session.project is not before and self.session.project is not None:
                editor.apply_external_project(self.session.project, self.session.path)
