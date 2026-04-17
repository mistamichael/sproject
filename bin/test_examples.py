"""
Diagnose-Skript: Alle Beispiele laden und Task-Tabelle prüfen
=============================================================

Testet den kompletten Datenpfad:
  load_project() -> tasks_to_rows() -> ProjectEditorApp._task_rows

Starten:
    python bin/test_examples.py
    python bin/test_examples.py --gui    # zusätzlich NiceGUI-App auf Port 8082
"""

import sys
import argparse
from pathlib import Path

# Projektverzeichnis in den Suchpfad aufnehmen
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from lib.models import load_project
from gui.editor import ProjectEditorApp, tasks_to_rows


# ---------------------------------------------------------------------------
# Headless-Test
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"id", "name", "duration", "successors_str", "row_type"}

EXAMPLES_DIR = ROOT / "examples"


def test_file(path: Path) -> dict:
    """Lädt eine JSON-Datei und prüft die erzeugten Rows."""
    result = {
        "file": path.name,
        "ok": False,
        "project_name": "",
        "task_count": 0,
        "row_count": 0,
        "missing_fields": [],
        "error": "",
    }
    try:
        project = load_project(path)
        result["project_name"] = project.project or "(kein Name)"
        result["task_count"] = len(project.tasks)

        rows = tasks_to_rows(project.tasks)
        result["row_count"] = len(rows)

        # Prüfe Pflichtfelder in jeder Row
        missing = set()
        for row in rows:
            for field in REQUIRED_FIELDS:
                if field not in row:
                    missing.add(field)
        result["missing_fields"] = sorted(missing)
        result["ok"] = len(rows) > 0 and not missing

    except Exception as exc:
        result["error"] = str(exc)

    return result


def run_headless_tests() -> list[dict]:
    """Führt den headless Test für alle Beispiele aus."""
    files = sorted(EXAMPLES_DIR.glob("*.json"))
    if not files:
        print(f"[WARNUNG] Keine JSON-Dateien in {EXAMPLES_DIR}")
        return []

    results = []
    max_name = max(len(f.name) for f in files)

    print()
    print("=" * 70)
    print("  HEADLESS TEST: load_project() + tasks_to_rows()")
    print("=" * 70)
    print(f"  {'Datei':<{max_name}}  {'Status':<8}  {'Tasks':>5}  {'Rows':>5}  Details")
    print("-" * 70)

    for path in files:
        r = test_file(path)
        results.append(r)

        if r["error"]:
            status = "FEHLER"
            detail = r["error"][:50]
        elif not r["ok"]:
            status = "LEER"
            detail = f"rows={r['row_count']}, fehlende Felder: {r['missing_fields']}"
        else:
            status = "OK"
            detail = f"Projekt: {r['project_name']}"

        marker = "OK" if r["ok"] else "!!"
        print(f"  [{marker}] {r['file']:<{max_name}}  {status:<8}  "
              f"{r['task_count']:>5}  {r['row_count']:>5}  {detail}")

    print("-" * 70)
    ok_count = sum(1 for r in results if r["ok"])
    print(f"  Ergebnis: {ok_count}/{len(results)} Dateien OK")
    print("=" * 70)
    print()
    return results


# ---------------------------------------------------------------------------
# NiceGUI-Test-App (optionaler --gui-Modus)
# ---------------------------------------------------------------------------

def run_gui_tests() -> None:
    """Startet eine NiceGUI-App, die alle Beispiele der Reihe nach lädt."""
    from nicegui import ui

    EXAMPLES = sorted(EXAMPLES_DIR.glob("*.json"))

    @ui.page("/")
    async def index():
        ui.label("Test: Alle Beispiele laden").classes("text-2xl font-bold mb-4")
        ui.label(
            "Jede Datei wird automatisch geladen. "
            "Die Tabelle darf NICHT leer bleiben."
        ).classes("text-sm text-gray-500 mb-4")

        status_label = ui.label("Bereit.").classes("text-sm text-gray-500 mb-2")

        # --- Ergebnis-Tabelle (eine Zeile pro Beispiel) ---
        result_rows: list[dict] = []

        results_grid = ui.aggrid({
            "columnDefs": [
                {"field": "file",    "headerName": "Datei",   "flex": 2},
                {"field": "status",  "headerName": "Status",  "width": 90},
                {"field": "rows",    "headerName": "Rows",    "width": 70},
                {"field": "detail",  "headerName": "Detail",  "flex": 3},
            ],
            "rowData": result_rows,
            "domLayout": "autoHeight",
            "rowClassRules": {
                "bg-red-50":   "data.status === 'LEER' || data.status === 'FEHLER'",
                "bg-green-50": "data.status === 'OK'",
            },
            "rowHeight": 32,
        }).classes("w-full mb-6")

        ui.separator().classes("my-4")

        # --- Live-Vorschau der zuletzt geladenen Task-Tabelle ---
        ui.label("Live-Vorschau (zuletzt geladene Datei):").classes(
            "text-base font-semibold mb-2"
        )

        preview_label = ui.label("(noch nichts geladen)").classes(
            "text-sm text-gray-400 mb-2"
        )

        @ui.refreshable
        def preview_grid() -> None:
            if not preview_app._task_rows:
                ui.label("Keine Zeilen – Tabelle ist LEER!").classes(
                    "text-red-600 font-bold py-4 text-center"
                )
                return
            ui.label(
                f"{len(preview_app._task_rows)} Zeilen geladen"
            ).classes("text-green-600 font-semibold mb-1")
            ui.aggrid({
                "columnDefs": [
                    {"field": "id",             "headerName": "#",          "width": 60},
                    {"field": "name",           "headerName": "Name",       "flex": 3},
                    {"field": "duration",       "headerName": "Dauer",      "width": 90},
                    {"field": "successors_str", "headerName": "Nachfolger", "flex": 2},
                    {"field": "row_type",       "headerName": "Typ",        "width": 90},
                ],
                "rowData": list(preview_app._task_rows),
                "domLayout": "autoHeight",
                "rowHeight": 34,
            }).classes("w-full")

        preview_app = ProjectEditorApp()
        preview_grid()

        # --- Alle Beispiele sequenziell laden ---
        async def run_all():
            import asyncio

            status_label.text = "Starte Tests..."
            result_rows.clear()
            results_grid.options["rowData"] = result_rows
            results_grid.update()

            for path in EXAMPLES:
                status_label.text = f"Lade: {path.name} ..."
                await asyncio.sleep(0.05)   # kurz rendern lassen

                row = {"file": path.name, "status": "", "rows": 0, "detail": ""}
                try:
                    project = load_project(path)
                    preview_app._task_rows = tasks_to_rows(project.tasks)
                    row["rows"] = len(preview_app._task_rows)

                    if preview_app._task_rows:
                        row["status"] = "OK"
                        row["detail"] = f"{project.project}"
                    else:
                        row["status"] = "LEER"
                        row["detail"] = "tasks_to_rows() liefert leere Liste"

                except Exception as exc:
                    row["status"] = "FEHLER"
                    row["detail"] = str(exc)[:80]

                result_rows.append(row)
                results_grid.options["rowData"] = list(result_rows)
                results_grid.update()

                preview_label.text = f"Vorschau: {path.name}  ({row['rows']} Rows)"
                await preview_grid.refresh()
                await asyncio.sleep(0.4)   # sichtbar machen

            ok = sum(1 for r in result_rows if r["status"] == "OK")
            status_label.text = (
                f"Fertig. {ok}/{len(result_rows)} Dateien OK. "
                + ("Alles in Ordnung!" if ok == len(result_rows) else "PROBLEME gefunden!")
            )
            status_label.classes(
                "text-green-700 font-semibold" if ok == len(result_rows)
                else "text-red-600 font-semibold"
            )

        ui.button("Alle Beispiele testen", on_click=run_all).props(
            "color=primary"
        ).classes("mb-4")

        await run_all()   # beim Seitenaufruf sofort starten

    ui.run(
        title="sproject Diagnose – Alle Beispiele",
        port=8082,
        reload=False,
        show=True,
        favicon="🔬",
    )


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnose: Alle Beispiele laden und Task-Tabelle prüfen"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Zusätzlich NiceGUI-App auf Port 8082 starten",
    )
    args = parser.parse_args()

    # Immer headless testen
    results = run_headless_tests()

    if args.gui:
        print("Starte NiceGUI-Diagnose-App auf http://localhost:8082 ...")
        run_gui_tests()
    else:
        # Exit-Code: 1 wenn Fehler gefunden
        if any(not r["ok"] for r in results):
            sys.exit(1)
