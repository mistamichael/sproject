"""
sproject MCP-Server
===================

Stellt die Operationen aus lib/api.py (ProjectSession) als MCP-Werkzeuge bereit,
damit Claude Code, Claude Desktop oder ein Chatbot Projekte aufbauen und rechnen kann.

    python -m mcp_server --http --port 8765    # HTTP: http://127.0.0.1:8765/mcp (Normalfall)
    python -m mcp_server                       # stdio (nur für Skripte/Tests)

Im Normalfall läuft genau ein Server per HTTP; Claude Code (.mcp.json) und die GUI
(gui/server_link.py) sind Clients und teilen sich dessen Projekt. Die GUI erkennt
neue Stände an get_revision() und schreibt mit replace_project(..., base_revision).
"""

import argparse
import contextlib
import json
import socket
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

if __package__ in (None, ""):
    # Direkter Skript-Aufruf (python mcp_server/server.py): Projekt-Root in den Suchpfad
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import Context, FastMCP

from lib.api import ApiError, ProjectSession, switch_message
from lib.exporters import EXPORTERS
from lib.paths import PROJECT_ROOT, get_work_dir

T = TypeVar("T")
TaskId = Union[int, str]

EXAMPLES_DIR = PROJECT_ROOT / "examples"

INSTRUCTIONS = """\
sproject plant Projekte mit Netzplantechnik (CPM), Ressourcen, Kalender und Kosten.
Es gibt immer genau ein geöffnetes Projekt; alle Werkzeuge arbeiten darauf.

Ablauf: new_project oder load_project → Tasks (add_task) → Abhängigkeiten (add_dependency)
→ optional Ressourcen/Personen (upsert_item) → validate → calculate → save_project.
Große Mengen (z. B. eine ganze Excel-Liste) besser in einem Aufruf mit replace_project
oder patch_project({"tasks": [...]}) übergeben. Das Format zeigt die Ressource
sproject://schema; Vorlagen: list_examples / sproject://examples/<name>.

Regeln des Formats:
- Dauern als Text: "3d" (Arbeitstage), "4h", "30m", "2w"; reine Zahl = Tage.
- Abhängigkeiten stehen am VORGÄNGER: successors = Nachfolger-IDs (Ende-Anfang);
  successors_aa / successors_ee / successors_ae für Anfang-Anfang, Ende-Ende, Anfang-Ende.
- Task-IDs sind Zahlen (1, 2, 3 …); resources am Task verweisen auf resources[].id.
- Ressourcen: type person (mit person_id → persons[].id), machine, truck, oven, material.
- Datumsangaben: "YYYY-MM-DD" oder "YYYY-MM-DD HH:MM" (project_start, not_before, deadline).
- Ungültige Eingaben ändern nichts und liefern eine Fehlermeldung.

Gemeinsames Projekt: Auch die GUI kann mit diesem Server verbunden sein und sieht dasselbe Projekt.
new_project, load_project und replace_project (ohne base_revision) ERSETZEN das Projekt – auch das,
woran jemand in der GUI arbeitet. Der bisherige Stand wird vorher automatisch gesichert; die Antwort
enthält dann "warning" mit dem Pfad der Sicherung – gib diese Warnung an den Nutzer weiter.
Für Änderungen am bestehenden Projekt patch_project, add_task usw. verwenden.
Hat ein anderer Client (z. B. die GUI) das Projekt ersetzt, wird dein nächster Aufruf NICHT
ausgeführt und meldet das; prüfe dann mit get_overview und frage den Nutzer, wie es weitergeht.
"""


def _quiet(func: Callable[[], T]) -> T:
    """Führt func aus, ohne dass print() der Bibliothek das stdio-Protokoll stört."""
    with contextlib.redirect_stdout(sys.stderr):
        return func()


SERVER_NAME = "sproject"


def _client_id(ctx: Context) -> int:
    """Kennung des aufrufenden Clients (MCP-Sitzung); 0 außerhalb einer Anfrage (direkte Aufrufe)."""
    try:
        return id(ctx.session)
    except ValueError:
        return 0


def port_in_use(host: str, port: int) -> bool:
    """True, wenn auf host:port schon etwas lauscht (z. B. ein laufender sproject-Server)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def build_server(session: Optional[ProjectSession] = None,
                 host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    """MCP-Server für eine ProjectSession."""
    s = session or ProjectSession()
    mcp = FastMCP(SERVER_NAME, instructions=INSTRUCTIONS, host=host, port=port)
    seen: Dict[int, int] = {}           # MCP-Sitzung (Client) → zuletzt gesehener Wechselzähler
    switched_by: Dict[int, int] = {}    # Wechselzähler → MCP-Sitzung, die gewechselt hat

    def run(ctx: Context, func: Callable[[], T], guarded: bool = True) -> T:
        """
        Führt func für den aufrufenden Client aus. Hat seit seinem letzten Aufruf ein ANDERER
        Client das Projekt ersetzt, wird func nicht ausgeführt, sondern das gemeldet (einmalig).
        """
        client = _client_id(ctx)
        last, switch = seen.get(client), s.last_switch
        if (guarded and last is not None and switch is not None and switch["generation"] > last
                and switched_by.get(switch["generation"]) != client):
            seen[client] = s.generation
            raise ApiError("Achtung: Das Projekt wurde inzwischen von einem anderen Client (z. B. der GUI) "
                           f"ersetzt. {switch_message(switch)}. Dieser Aufruf wurde NICHT ausgeführt – "
                           "prüfe mit get_overview und rufe ihn dann erneut auf, "
                           "oder lade die Sicherung mit load_project.")
        before = s.generation
        result = _quiet(func)
        if s.generation != before:
            switched_by[s.generation] = client
            if s.last_switch is not None and s.last_switch["generation"] == s.generation:
                print(f"[sproject] {switch_message(s.last_switch)}", file=sys.stderr, flush=True)
        seen[client] = s.generation
        return result

    # --- Projekt -------------------------------------------------------

    @mcp.tool()
    def new_project(ctx: Context, name: str, project_start: Optional[str] = None,
                    unit: Optional[str] = None) -> Dict[str, Any]:
        """Legt ein neues, leeres Projekt an (ersetzt das geöffnete). project_start z. B. "2026-04-01"."""
        return run(ctx, lambda: s.new_project(name, project_start, unit), guarded=False)

    @mcp.tool()
    def load_project(ctx: Context, path: str) -> Dict[str, Any]:
        """Öffnet eine sproject-JSON-Datei (absoluter oder zum Projekt-Root relativer Pfad)."""
        return run(ctx, lambda: s.load(_resolve(path)), guarded=False)

    @mcp.tool()
    def save_project(ctx: Context, path: Optional[str] = None) -> str:
        """Speichert das Projekt als JSON. Ohne Pfad: zuletzt verwendeter Pfad.
        Relative Pfade landen im Arbeitsordner work/."""
        target = None if path is None else (Path(path) if Path(path).is_absolute() else get_work_dir() / path)
        return run(ctx, lambda: s.save(target))

    @mcp.tool()
    def get_overview(ctx: Context) -> Dict[str, Any]:
        """Kurzfassung des geöffneten Projekts: Stammdaten, Tasks mit Nachfolgern, Anzahl Ressourcen."""
        return run(ctx, s.overview)

    @mcp.tool()
    def get_project(ctx: Context) -> Dict[str, Any]:
        """Vollständiges Projekt als JSON (wie in der Datei)."""
        return run(ctx, s.get_project)

    @mcp.tool()
    def replace_project(ctx: Context, data: Dict[str, Any], base_revision: Optional[int] = None) -> Dict[str, Any]:
        """Ersetzt das ganze Projekt durch data (Format wie die JSON-Datei, siehe sproject://schema).
        base_revision (optional): nur ersetzen, wenn der Stand seitdem unverändert ist."""
        return run(ctx, lambda: s.replace_project(data, base_revision), guarded=False)

    @mcp.tool()
    def get_revision() -> int:
        """Änderungszähler des Projekts – steigt bei jeder Änderung (für Clients wie die GUI)."""
        return s.revision

    @mcp.tool()
    def get_state() -> Dict[str, Any]:
        """Revision, vollständiges Projekt-JSON (null ohne Projekt) und Dateipfad."""
        return _quiet(s.state)

    @mcp.tool()
    def patch_project(ctx: Context, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Setzt Felder auf oberster Ebene (project, project_start, unit, tasks, resources, persons …).
        null entfernt ein Feld. Listen werden komplett ersetzt."""
        return run(ctx, lambda: s.patch_project(fields))

    # --- Tasks ---------------------------------------------------------

    @mcp.tool()
    def add_task(ctx: Context, task: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt einen Task hinzu, z. B. {"name": "Fundament", "duration": "3d", "resources": ["R1"]}.
        Ohne id wird die nächste freie Zahl vergeben. Weitere Felder: successors, not_before,
        deadline, delay, cost, description; Loop-Tasks: loop_until, subtasks.
        Gibt den gespeicherten Task zurück – seine "id" ist für add_dependency nötig."""
        return run(ctx, lambda: s.get_task(s.add_task(task)))

    @mcp.tool()
    def get_task(ctx: Context, task_id: TaskId) -> Dict[str, Any]:
        """Ein Task mit allen Feldern (wie in der JSON-Datei)."""
        return run(ctx, lambda: s.get_task(task_id))

    @mcp.tool()
    def update_task(ctx: Context, task_id: TaskId, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Ändert Felder eines Tasks; null entfernt ein Feld."""
        return run(ctx, lambda: s.update_task(task_id, fields))

    @mcp.tool()
    def remove_task(ctx: Context, task_id: TaskId) -> List[TaskId]:
        """Löscht einen Task und alle Verweise darauf. Gibt die verbleibenden Task-IDs zurück."""
        return run(ctx, lambda: s.remove_task(task_id))

    @mcp.tool()
    def add_dependency(ctx: Context, predecessor: TaskId, successor: TaskId, dep_type: str = "EA") -> Dict[str, Any]:
        """Abhängigkeit Vorgänger → Nachfolger. dep_type: EA (Ende-Anfang, Standard), AA, EE, AE."""
        return run(ctx, lambda: s.add_dependency(predecessor, successor, dep_type))

    @mcp.tool()
    def remove_dependency(ctx: Context, predecessor: TaskId, successor: TaskId) -> Dict[str, Any]:
        """Entfernt alle Abhängigkeiten Vorgänger → Nachfolger."""
        return run(ctx, lambda: s.remove_dependency(predecessor, successor))

    @mcp.tool()
    def set_uncertainty(ctx: Context, task_id: TaskId, duration_range: Optional[List[str]] = None,
                        risk: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Unsicherheit für die Simulation: duration_range ["4d", "9d"],
        risk {"probability": 0.2, "delay": "3d", "note": "..."}; null entfernt."""
        return run(ctx, lambda: s.set_uncertainty(task_id, duration_range, risk))

    # --- Listen --------------------------------------------------------

    @mcp.tool()
    def upsert_item(ctx: Context, field: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt in field = resources | persons (Schlüssel id) oder scenarios (Schlüssel name)
        einen Eintrag hinzu oder ersetzt ihn.
        Person: {"id", "name", "role", "hourly_rate", "vacation": [{"from", "to", "description"}]}.
        Ressource: {"id", "name", "type", "person_id" | "hourly_rate", "color"}.
        Szenario: {"name", "changes": [{"task": 3, "duration_factor": 1.5}]}."""
        return run(ctx, lambda: s.upsert_item(field, item))

    @mcp.tool()
    def remove_item(ctx: Context, field: str, key: str) -> int:
        """Entfernt eine Ressource/Person (per id) oder ein Szenario (per name)."""
        return run(ctx, lambda: s.remove_item(field, key))

    @mcp.tool()
    def set_list(ctx: Context, field: str, items: List[Dict[str, Any]]) -> int:
        """Ersetzt resources, persons, resting_times oder scenarios komplett ([] entfernt die Liste).
        resting_times: [{"after_hours": 6, "duration": "30m", "note": "..."}]."""
        return run(ctx, lambda: s.set_list(field, items))

    # --- Prüfen, Rechnen, Exportieren ---------------------------------

    @mcp.tool()
    def validate(ctx: Context) -> List[str]:
        """Prüft das Projekt (unbekannte Verweise, Zyklen, Rechenfehler). Leere Liste = in Ordnung."""
        return run(ctx, s.validate)

    @mcp.tool()
    def calculate(ctx: Context, start_date: Optional[str] = None) -> Dict[str, Any]:
        """Berechnet den Plan: Start, Ende, Dauer, kritischer Pfad, Kosten, Deadline-Warnungen, Termine je Task."""
        return run(ctx, lambda: s.calculate(start_date))

    @mcp.tool()
    def compare_scenarios(ctx: Context) -> List[List[str]]:
        """Vergleicht den Basisplan mit allen Szenarien (Tabelle, erste Zeile = Kopf)."""
        return run(ctx, s.compare_scenarios)

    @mcp.tool()
    def simulate(ctx: Context, runs: int = 300, seed: Optional[int] = None) -> Dict[str, Any]:
        """Monte-Carlo-Simulation (duration_range, risk, Szenarien mit probability)."""
        return run(ctx, lambda: s.simulate(runs, seed))

    @mcp.tool(description=f"Exportiert Reports nach results/ (oder out_dir). Formate: {', '.join(EXPORTERS)}.")
    def export(ctx: Context, formats: List[str], out_dir: Optional[str] = None) -> List[str]:
        return run(ctx, lambda: s.export(formats, out_dir))

    @mcp.tool()
    def list_examples() -> List[str]:
        """Pfade der Beispielprojekte (Vorlagen für Format und Struktur)."""
        return [p.relative_to(PROJECT_ROOT).as_posix() for p in sorted(EXAMPLES_DIR.glob("*.json"))]

    # --- Ressourcen ----------------------------------------------------

    @mcp.resource("sproject://schema", mime_type="application/json")
    def schema() -> str:
        """JSON-Schema des Projektformats."""
        return json.dumps(ProjectSession.schema(), ensure_ascii=False, indent=1)

    @mcp.resource("sproject://examples/{name}", mime_type="application/json")
    def example(name: str) -> str:
        """Beispielprojekt aus examples/ (name mit oder ohne .json)."""
        path = EXAMPLES_DIR / (name if name.endswith(".json") else f"{name}.json")
        if path.parent != EXAMPLES_DIR or not path.exists():
            raise ValueError(f"Beispiel nicht gefunden: {name}")
        return path.read_text(encoding="utf-8")

    return mcp


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() or p.exists() else PROJECT_ROOT / p


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="sproject MCP-Server")
    parser.add_argument("--http", action="store_true", help="HTTP statt stdio (http://HOST:PORT/mcp)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--project", type=Path, help="Projektdatei beim Start öffnen")
    args = parser.parse_args(argv)

    url = f"http://{args.host}:{args.port}/mcp"
    if args.http and port_in_use(args.host, args.port):
        print(f"Port {args.port} ist belegt – läuft schon ein sproject-Server? ({url})", file=sys.stderr)
        return 1
    if args.http:
        print(f"sproject-Server: {url}\n"
              f"Claude Code:     .mcp.json im Projektordner (Port 8765) oder "
              f"claude mcp add --transport http sproject {url}\n"
              f"GUI:             Server -> Mit sproject-Server verbinden ...\n"
              f"Beenden mit Strg+C", flush=True)
    session = ProjectSession()
    if args.project:
        _quiet(lambda: session.load(args.project))
    build_server(session, host=args.host, port=args.port).run("streamable-http" if args.http else "stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
