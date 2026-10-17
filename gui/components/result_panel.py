"""
Ergebnis-Panel
==============

Zeigt einen berechneten Schedule im Tab "Ergebnis": Projektdauer, kritischer
Pfad, alle Aufgaben, Kosten sowie Gantt- und Ressourcen-Diagramm.
"""

from typing import Callable, Dict, Optional

import dearpygui.dearpygui as dpg

from gui.colors import resource_color_map
from gui.gui_config import load_gui_config
from gui.i18n import t
from lib.report_data import collect_deadline_violations, tracking_summary
from lib.scenarios import comparison_rows
from lib.schedule import Schedule

_CFG = load_gui_config()
_COLORS = _CFG.section("colors")
_PARENT = "result_container"


def hide_result() -> None:
    """Blendet den Ergebnis-Tab aus, leert ihn und wechselt zur Eingabe."""
    if dpg.does_item_exist("tab_result"):
        dpg.configure_item("tab_result", show=False)
    if dpg.does_item_exist(_PARENT):
        dpg.delete_item(_PARENT, children_only=True)
    if dpg.does_item_exist("main_tab_bar"):
        dpg.set_value("main_tab_bar", "tab_input")


def show_result(schedule: Schedule, export_actions: Dict[str, Callable[[], None]],
                scenario_outcomes: Optional[list] = None, simulation=None) -> None:
    """
    Füllt den Ergebnis-Tab und wechselt dorthin.

    Args:
        schedule:       berechnetes Ergebnis
        export_actions: Button-Beschriftung → Callback (Schnell-Exporte)
    """
    if not dpg.does_item_exist(_PARENT):
        return
    if dpg.does_item_exist("tab_result"):
        dpg.configure_item("tab_result", show=True)
    dpg.delete_item(_PARENT, children_only=True)

    result = schedule.cpm
    dpg.add_text(t("result.duration", duration=result.project_duration), parent=_PARENT,
                 color=_COLORS.get("result_duration", (100, 180, 255)))
    for label, value in tracking_summary(result):
        dpg.add_text(f"{label}: {value}", parent=_PARENT)
    for v in collect_deadline_violations(result):
        dpg.add_text(t("result.deadline_missed", task=f"{v.task_id} ({v.name})", deadline=v.deadline,
                       end=v.end, late=v.late),
                     parent=_PARENT, color=_COLORS.get("result_critical_path", (220, 80, 80)))
    dpg.add_spacer(parent=_PARENT, height=6)

    _critical_path(schedule)
    dpg.add_spacer(parent=_PARENT, height=6)
    _all_tasks(schedule)
    dpg.add_spacer(parent=_PARENT, height=6)
    _costs(schedule)
    _scenarios(scenario_outcomes or [])
    _simulation(simulation)
    _charts(schedule)

    dpg.add_spacer(parent=_PARENT, height=8)
    with dpg.group(horizontal=True, parent=_PARENT):
        for label, callback in export_actions.items():
            dpg.add_button(label=label, callback=callback)

    if dpg.does_item_exist("main_tab_bar"):
        dpg.set_value("main_tab_bar", "tab_result")


def _table(tag: str = ""):
    kwargs = {"tag": tag} if tag else {}
    return dpg.table(header_row=True, resizable=True, row_background=True,
                     borders_outerH=True, borders_innerV=True, borders_outerV=True, **kwargs)


def _columns(specs) -> None:
    widths = _CFG.section("result_table")
    for label_key, width_key, default in specs:
        if width_key:
            dpg.add_table_column(label=t(label_key), width_fixed=True,
                                 init_width_or_weight=widths.get(width_key, default))
        else:
            dpg.add_table_column(label=t(label_key), width_stretch=True)


def _critical_path(schedule: Schedule) -> None:
    result = schedule.cpm
    with dpg.collapsing_header(label=t("result.header.critical_path"), parent=_PARENT, default_open=True):
        dpg.add_text(" -> ".join(str(tid) for tid in result.critical_path),
                     color=_COLORS.get("result_critical_path", (220, 80, 80)), wrap=0)
        dpg.add_spacer(height=4)
        with _table("result_crit_table"):
            _columns([
                ("result.col.id", "col_id_width", 60), ("result.col.name", None, 0),
                ("result.col.duration", "col_faz_width", 70), ("result.col.faz", "col_faz_width", 70),
                ("result.col.fez", "col_fez_width", 70),
            ])
            for tid in result.critical_path:
                task = result.tasks.get(tid)
                if not task or task.is_system:
                    continue
                with dpg.table_row():
                    for value in (str(tid), task.name, f"{task.duration:.1f}", f"{task.faz:.1f}", f"{task.fez:.1f}"):
                        dpg.add_text(value)


def _all_tasks(schedule: Schedule) -> None:
    result = schedule.cpm
    with dpg.collapsing_header(label=t("result.header.all_tasks"), parent=_PARENT, default_open=True):
        critical_rows = []
        with _table("result_table"):
            _columns([
                ("result.col.id", "col_id_width", 60), ("result.col.name", None, 0),
                ("result.col.duration", "col_faz_width", 70), ("result.col.faz", "col_faz_width", 70),
                ("result.col.fez", "col_fez_width", 70), ("result.col.saz", "col_saz_width", 70),
                ("result.col.sez", "col_sez_width", 70), ("result.col.buffer", "col_puffer_width", 70),
                ("result.col.critical", "col_krit_width", 45),
            ])
            visible = [(tid, task) for tid, task in result.tasks.items() if not task.is_system]
            for row_idx, (tid, task) in enumerate(visible):
                with dpg.table_row():
                    for value in (str(tid), task.name, f"{task.duration:.1f}", f"{task.faz:.1f}",
                                  f"{task.fez:.1f}", f"{task.saz:.1f}", f"{task.sez:.1f}",
                                  f"{task.puffer:.1f}", "*" if task.is_critical else ""):
                        dpg.add_text(value)
                if task.is_critical:
                    critical_rows.append(row_idx)
        for row_idx in critical_rows:
            dpg.highlight_table_row("result_table", row_idx, list(_COLORS.get("critical_row", (220, 80, 80, 80))))


def _costs(schedule: Schedule) -> None:
    costs = schedule.costs
    if not costs or not costs.entries:
        return
    with dpg.collapsing_header(label=t("result.header.resources_costs"), parent=_PARENT, default_open=True):
        with _table():
            dpg.add_table_column(label=t("result.cost.col.resource"), width_stretch=True)
            for key, width in [("type", 90), ("hours", 80), ("rate", 90), ("provisioning", 110),
                               ("labor", 100), ("total", 100)]:
                dpg.add_table_column(label=t(f"result.cost.col.{key}"), width_fixed=True, init_width_or_weight=width)
            for e in costs.entries:
                with dpg.table_row():
                    for value in (e.resource_name, e.resource_type, f"{e.hours_worked:.1f}",
                                  f"{e.hourly_rate:.2f}",
                                  f"{e.provisioning_costs:.2f}" if e.provisioning_costs else "—",
                                  f"{e.labor_costs:.2f}", f"{e.total_costs:.2f}"):
                        dpg.add_text(value)
        dpg.add_spacer(height=6)

        sum_color = _COLORS.get("result_duration", (100, 180, 255))
        for key, amount in [("person_costs", costs.total_person_costs),
                            ("machine_costs", costs.total_machine_costs),
                            ("provisioning_costs", costs.total_provisioning_costs),
                            ("fixed_costs", costs.total_fixed_costs)]:
            if amount > 0:
                dpg.add_text(f"{t('result.cost.' + key)}: {amount:.2f} €", color=sum_color)
        dpg.add_text(f"{t('result.cost.total_costs')}: {costs.total_costs:.2f} €",
                     color=_COLORS.get("result_critical_path", (220, 80, 80)))


def _scenarios(outcomes: list) -> None:
    """Vergleich Basisplan ↔ Szenarien (nur wenn das Projekt Szenarien enthält)."""
    if len(outcomes) < 2:
        return
    rows = comparison_rows(outcomes)
    with dpg.collapsing_header(label=t("result.header.scenarios"), parent=_PARENT, default_open=True):
        with _table():
            for title in rows[0]:
                dpg.add_table_column(label=title)
            for row in rows[1:]:
                with dpg.table_row():
                    for cell in row:
                        dpg.add_text(cell)
        dpg.add_spacer(height=6)


def _simulation(sim) -> None:
    """Kennzahlen und kritischste Tasks der Monte-Carlo-Simulation."""
    if sim is None:
        return
    from lib.simulation import summary_rows, top_critical

    with dpg.collapsing_header(label=t("result.header.simulation"), parent=_PARENT, default_open=True):
        for rows, header in [(summary_rows(sim), [t("result.col.metric"), t("result.col.value")]),
                             (top_critical(sim), ["Task", "Name", t("result.col.critical_share")])]:
            with _table():
                for title in header:
                    dpg.add_table_column(label=title)
                for row in rows:
                    with dpg.table_row():
                        for cell in row:
                            dpg.add_text(cell)
            dpg.add_spacer(height=6)


def _charts(schedule: Schedule) -> None:
    """Gantt- und Ressourcen-Diagramm (matplotlib → PNG → Texture), falls verfügbar."""
    try:
        from gui.gantt_chart import load_png_as_dpg_texture, render_gantt_png, render_resource_chart_png
    except ImportError:
        return

    colors = resource_color_map(schedule.project)
    charts = [("result.header.gantt", "_gantt_chart_tex",
               lambda: render_gantt_png(schedule.cpm, resource_colors=colors))]
    if schedule.project.resources:
        charts.append(("result.header.resource_chart", "_resource_chart_tex",
                       lambda: render_resource_chart_png(schedule.cpm, project=schedule.project,
                                                         resource_colors=colors)))
    for header, tex_tag, render in charts:
        png = render()
        if png and load_png_as_dpg_texture(png, tex_tag):
            with dpg.collapsing_header(label=t(header), parent=_PARENT, default_open=True):
                dpg.add_image(tex_tag)
