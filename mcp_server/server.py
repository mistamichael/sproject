"""
sproject MCP-Server
===================

Stellt die Operationen aus lib/api.py (ProjectSession) als MCP-Werkzeuge bereit,
damit Claude Code, Claude Desktop oder ein Chatbot Projekte aufbauen und rechnen kann.

    python -m mcp_server                       # stdio (Claude Code / Desktop)
    python -m mcp_server --http --port 8765    # HTTP: http://127.0.0.1:8765/mcp

build_server(session, runner) ist auch für die GUI gedacht: runner führt jeden
Aufruf aus (z. B. im DPG-Hauptthread) – ohne runner wird direkt aufgerufen.
"""

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

if __package__ in (None, ""):
    # Direkter Skript-Aufruf (python mcp_server/server.py): Projekt-Root in den Suchpfad
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from lib.api import ProjectSession
from lib.exporters import EXPORTERS
from lib.paths import PROJECT_ROOT, get_work_dir

T = TypeVar("T")
Runner = Callable[[Callable[[], Any]], Any]
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
"""


def _quiet(func: Callable[[], T]) -> T:
    """Führt func aus, ohne dass print() der Bibliothek das stdio-Protokoll stört."""
    with contextlib.redirect_stdout(sys.stderr):
        return func()


def build_server(session: Optional[ProjectSession] = None, runner: Optional[Runner] = None,
                 host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    """MCP-Server für eine ProjectSession; runner(func) führt jeden Werkzeugaufruf aus."""
    s = session or ProjectSession()
    run: Runner = runner or (lambda func: func())
    mcp = FastMCP("sproject", instructions=INSTRUCTIONS, host=host, port=port)

    def call(func: Callable[[], T]) -> T:
        return run(lambda: _quiet(func))

    # --- Projekt -------------------------------------------------------

    @mcp.tool()
    def new_project(name: str, project_start: Optional[str] = None,
                    unit: Optional[str] = None) -> Dict[str, Any]:
        """Legt ein neues, leeres Projekt an (ersetzt das geöffnete). project_start z. B. "2026-04-01"."""
        return call(lambda: s.new_project(name, project_start, unit))

    @mcp.tool()
    def load_project(path: str) -> Dict[str, Any]:
        """Öffnet eine sproject-JSON-Datei (absoluter oder zum Projekt-Root relativer Pfad)."""
        return call(lambda: s.load(_resolve(path)))

    @mcp.tool()
    def save_project(path: Optional[str] = None) -> str:
        """Speichert das Projekt als JSON. Ohne Pfad: zuletzt verwendeter Pfad.
        Relative Pfade landen im Arbeitsordner work/."""
        target = None if path is None else (Path(path) if Path(path).is_absolute() else get_work_dir() / path)
        return call(lambda: s.save(target))

    @mcp.tool()
    def get_overview() -> Dict[str, Any]:
        """Kurzfassung des geöffneten Projekts: Stammdaten, Tasks mit Nachfolgern, Anzahl Ressourcen."""
        return call(s.overview)

    @mcp.tool()
    def get_project() -> Dict[str, Any]:
        """Vollständiges Projekt als JSON (wie in der Datei)."""
        return call(s.get_project)

    @mcp.tool()
    def replace_project(data: Dict[str, Any]) -> Dict[str, Any]:
        """Ersetzt das ganze Projekt durch data (Format wie die JSON-Datei, siehe sproject://schema)."""
        return call(lambda: s.replace_project(data))

    @mcp.tool()
    def patch_project(fields: Dict[str, Any]) -> Dict[str, Any]:
        """Setzt Felder auf oberster Ebene (project, project_start, unit, tasks, resources, persons …).
        null entfernt ein Feld. Listen werden komplett ersetzt."""
        return call(lambda: s.patch_project(fields))

    # --- Tasks ---------------------------------------------------------

    @mcp.tool()
    def add_task(task: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt einen Task hinzu, z. B. {"name": "Fundament", "duration": "3d", "resources": ["R1"]}.
        Ohne id wird die nächste freie Zahl vergeben. Weitere Felder: successors, not_before,
        deadline, delay, cost, description; Loop-Tasks: loop_until, subtasks."""
        return call(lambda: s.add_task(task))

    @mcp.tool()
    def update_task(task_id: TaskId, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Ändert Felder eines Tasks; null entfernt ein Feld."""
        return call(lambda: s.update_task(task_id, fields))

    @mcp.tool()
    def remove_task(task_id: TaskId) -> List[TaskId]:
        """Löscht einen Task und alle Verweise darauf. Gibt die verbleibenden Task-IDs zurück."""
        return call(lambda: s.remove_task(task_id))

    @mcp.tool()
    def add_dependency(predecessor: TaskId, successor: TaskId, dep_type: str = "EA") -> Dict[str, Any]:
        """Abhängigkeit Vorgänger → Nachfolger. dep_type: EA (Ende-Anfang, Standard), AA, EE, AE."""
        return call(lambda: s.add_dependency(predecessor, successor, dep_type))

    @mcp.tool()
    def remove_dependency(predecessor: TaskId, successor: TaskId) -> Dict[str, Any]:
        """Entfernt alle Abhängigkeiten Vorgänger → Nachfolger."""
        return call(lambda: s.remove_dependency(predecessor, successor))

    @mcp.tool()
    def set_uncertainty(task_id: TaskId, duration_range: Optional[List[str]] = None,
                        risk: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Unsicherheit für die Simulation: duration_range ["4d", "9d"],
        risk {"probability": 0.2, "delay": "3d", "note": "..."}; null entfernt."""
        return call(lambda: s.set_uncertainty(task_id, duration_range, risk))

    # --- Listen --------------------------------------------------------

    @mcp.tool()
    def upsert_item(field: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt in field = resources | persons (Schlüssel id) oder scenarios (Schlüssel name)
        einen Eintrag hinzu oder ersetzt ihn.
        Person: {"id", "name", "role", "hourly_rate", "vacation": [{"from", "to", "description"}]}.
        Ressource: {"id", "name", "type", "person_id" | "hourly_rate", "color"}.
        Szenario: {"name", "changes": [{"task": 3, "duration_factor": 1.5}]}."""
        return call(lambda: s.upsert_item(field, item))

    @mcp.tool()
    def remove_item(field: str, key: str) -> int:
        """Entfernt eine Ressource/Person (per id) oder ein Szenario (per name)."""
        return call(lambda: s.remove_item(field, key))

    @mcp.tool()
    def set_list(field: str, items: List[Dict[str, Any]]) -> int:
        """Ersetzt resources, persons, resting_times oder scenarios komplett ([] entfernt die Liste).
        resting_times: [{"after_hours": 6, "duration": "30m", "note": "..."}]."""
        return call(lambda: s.set_list(field, items))

    # --- Prüfen, Rechnen, Exportieren ---------------------------------

    @mcp.tool()
    def validate() -> List[str]:
        """Prüft das Projekt (unbekannte Verweise, Zyklen, Rechenfehler). Leere Liste = in Ordnung."""
        return call(s.validate)

    @mcp.tool()
    def calculate(start_date: Optional[str] = None) -> Dict[str, Any]:
        """Berechnet den Plan: Start, Ende, Dauer, kritischer Pfad, Kosten, Deadline-Warnungen, Termine je Task."""
        return call(lambda: s.calculate(start_date))

    @mcp.tool()
    def compare_scenarios() -> List[List[str]]:
        """Vergleicht den Basisplan mit allen Szenarien (Tabelle, erste Zeile = Kopf)."""
        return call(s.compare_scenarios)

    @mcp.tool()
    def simulate(runs: int = 300, seed: Optional[int] = None) -> Dict[str, Any]:
        """Monte-Carlo-Simulation (duration_range, risk, Szenarien mit probability)."""
        return call(lambda: s.simulate(runs, seed))

    @mcp.tool(description=f"Exportiert Reports nach results/ (oder out_dir). Formate: {', '.join(EXPORTERS)}.")
    def export(formats: List[str], out_dir: Optional[str] = None) -> List[str]:
        return call(lambda: s.export(formats, out_dir))

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

    session = ProjectSession()
    if args.project:
        _quiet(lambda: session.load(args.project))
    build_server(session, host=args.host, port=args.port).run("streamable-http" if args.http else "stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
