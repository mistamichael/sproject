"""
Exporters
=========

Registry aller Exportformate. CLI und GUI erzeugen Dateien ausschließlich über
export_schedule(), damit beide identische Ergebnisse liefern.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from .schedule import Schedule


@dataclass(frozen=True)
class ExportOptions:
    out_dir: Path
    file_stem: str                  # Basis-Dateiname, z. B. Name der Projektdatei
    cfg_dir: Optional[Path] = None
    lang: str = 'de'
    simulation_runs: int = 300        # Monte-Carlo-Läufe für das Format "simulation"
    seed: Optional[int] = None        # fester Zufallsstartwert (reproduzierbar)


def _check(ok: Optional[bool], fmt: str) -> None:
    if ok is False:
        raise RuntimeError(f"{fmt.upper()}-Export fehlgeschlagen (Details im Log)")


def _json(s: Schedule, o: ExportOptions) -> Path:
    from .json_export import export_cpm_to_json
    path = o.out_dir / f"{o.file_stem}_network_plan.json"
    _check(export_cpm_to_json(s.cpm, path, project_name=s.name, project=s.project,
                              cfg_dir=o.cfg_dir, gantt_data=s.gantt.export_to_dict()), 'json')
    return path


def _txt(s: Schedule, o: ExportOptions) -> Path:
    from .txt_export import export_cpm_to_txt
    path = o.out_dir / f"{o.file_stem}.txt"
    _check(export_cpm_to_txt(s.cpm, path, project_name=s.cpm.project_name, project=s.project,
                             cfg_dir=o.cfg_dir, lang=o.lang), 'txt')
    return path


def _md(s: Schedule, o: ExportOptions) -> Path:
    from .markdown_export import export_cpm_to_markdown
    path = o.out_dir / f"{o.file_stem}.md"
    _check(export_cpm_to_markdown(s.cpm, path, s.name, s.project, cfg_dir=o.cfg_dir, lang=o.lang), 'md')
    return path


def _html(s: Schedule, o: ExportOptions) -> Path:
    from .markdown_export import export_cpm_to_html
    path = o.out_dir / f"{o.file_stem}.html"
    _check(export_cpm_to_html(s.cpm, path, s.name, s.project, cfg_dir=o.cfg_dir, lang=o.lang), 'html')
    return path


def _zip(s: Schedule, o: ExportOptions) -> Path:
    from .markdown_export import export_cpm_to_svg_zip
    path = o.out_dir / f"{o.file_stem}_svgs.zip"
    _check(export_cpm_to_svg_zip(s.cpm, path, s.name, s.project, cfg_dir=o.cfg_dir, lang=o.lang), 'zip')
    return path


def _xlsx(s: Schedule, o: ExportOptions) -> Path:
    from .excel_reports import export_cpm_to_xlsx
    path = o.out_dir / f"{o.file_stem}.xlsx"
    export_cpm_to_xlsx(s.cpm, path, s.project, cfg_dir=o.cfg_dir, lang=o.lang)
    return path


def _plotly_html(s: Schedule, o: ExportOptions) -> Path:
    from .charts import build_figures, write_html
    return write_html(build_figures(s, o.lang), o.out_dir / f"{o.file_stem}_charts.html", s.name)


def _plotly_svg(s: Schedule, o: ExportOptions) -> Path:
    from .charts import build_figures, write_image
    figures = build_figures(s, o.lang)
    names = ["gantt", "resources"][:len(figures)]
    paths = [write_image(fig, o.out_dir / f"{o.file_stem}_{name}.svg") for fig, name in zip(figures, names)]
    return paths[0]


def _scenarios(s: Schedule, o: ExportOptions) -> Path:
    from .charts import build_scenario_figures, write_html
    from .scenarios import compare_scenarios
    source = s.source or s.project
    if not source.scenarios:
        raise ValueError("Das Projekt enthält keine Szenarien")
    outcomes = compare_scenarios(source, start_date=s.cpm.project_start, cfg_dir=o.cfg_dir)
    return write_html(build_scenario_figures(outcomes, s.name), o.out_dir / f"{o.file_stem}_scenarios.html", s.name)


def _simulation(s: Schedule, o: ExportOptions) -> Path:
    from .charts import build_simulation_figures, write_html
    from .simulation import simulate
    sim = simulate(s.source or s.project, runs=o.simulation_runs, seed=o.seed,
                   start_date=s.cpm.project_start, cfg_dir=o.cfg_dir)
    return write_html(build_simulation_figures(sim, s.name, o.lang),
                      o.out_dir / f"{o.file_stem}_simulation.html", s.name)


EXPORTERS: Dict[str, Callable[[Schedule, ExportOptions], Path]] = {
    'json': _json,
    'txt':  _txt,
    'md':   _md,
    'html': _html,
    'zip':  _zip,
    'xlsx': _xlsx,
    'plotly': _plotly_html,       # interaktives HTML (Gantt + Ressourcen)
    'plotly_svg': _plotly_svg,   # SVG-Bilder (kaleido + lokaler Chrome)
    'scenarios': _scenarios,     # Szenario-Vergleich als HTML
    'simulation': _simulation,   # Monte-Carlo-Simulation als HTML
}


def export_schedule(schedule: Schedule, formats: Iterable[str], options: ExportOptions) -> List[Path]:
    """
    Exportiert in alle angegebenen Formate und gibt die erzeugten Dateien zurück.

    Raises:
        ValueError:   bei unbekanntem Format (vor dem ersten Export)
        RuntimeError: wenn ein Export fehlschlägt
    """
    formats = list(formats)
    unknown = [f for f in formats if f not in EXPORTERS]
    if unknown:
        raise ValueError(f"Unbekannte Exportformate: {', '.join(unknown)} (erlaubt: {', '.join(EXPORTERS)})")
    options.out_dir.mkdir(parents=True, exist_ok=True)
    return [EXPORTERS[fmt](schedule, options) for fmt in formats]
