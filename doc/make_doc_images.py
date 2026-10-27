"""
Doku-Bilder erzeugen
====================

Rechnet examples/software_simple.json und schreibt die Diagramme der README und der
Doku als SVG nach doc/img/ – je Sprache (de, en):

    python doc/make_doc_images.py

Benötigt kaleido mit einem lokalen Chrome (einmalig: plotly_get_chrome).
Die Simulation nutzt seed=1, damit die Bilder reproduzierbar sind.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.charts import build_figures, build_scenario_figures, build_simulation_figures, write_image  # noqa: E402
from lib.models import load_project  # noqa: E402
from lib.paths import get_cfg_dir  # noqa: E402
from lib.scenarios import compare_scenarios  # noqa: E402
from lib.schedule import build_schedule  # noqa: E402
from lib.simulation import simulate  # noqa: E402

OUT = ROOT / "doc" / "img"
EXAMPLE = ROOT / "examples" / "software_simple.json"
WIDTH = 1100


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = get_cfg_dir()
    project = load_project(EXAMPLE)
    schedule = build_schedule(project, cfg_dir=cfg)
    outcomes = compare_scenarios(project, cfg_dir=cfg)
    sim = simulate(project, runs=300, seed=1, cfg_dir=cfg)

    for lang in ("de", "en"):
        gantt, resources = build_figures(schedule, lang)[:2]
        hist, _table, criticality = build_simulation_figures(sim, schedule.name, lang)
        scenarios = build_scenario_figures(outcomes, schedule.name, lang)[0]
        images = {
            f"gantt_{lang}.svg": gantt,
            f"resources_{lang}.svg": resources,
            f"simulation_{lang}.svg": hist,
            f"criticality_{lang}.svg": criticality,
            f"scenarios_{lang}.svg": scenarios,
        }
        for name, fig in images.items():
            path = write_image(fig, OUT / name, width=WIDTH)
            print(f"{path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
