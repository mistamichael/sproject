"""
Aufgabentabelle (Herzstück) – Dear PyGui
=========================================

Baut die zentrale Task-Tabelle aus app.task_rows (gui.task_rows.TaskRow) auf.

Besonderheiten:
- rebuild_task_table() löscht den Container und erstellt die Tabelle neu
- Loop-Zeilen: amber-Hintergrund, Subtask-Zeilen: hellgrau
- Nachfolger und Ressourcen sind schreibgeschützt; Bearbeitung über + / -
"""

import re
from typing import Callable, List

import dearpygui.dearpygui as dpg

from gui.colors import resource_color_map
from gui.gui_config import load_gui_config
from gui.i18n import t
from moncapro.models.dependencies import DepType, Dependency, format_dependencies, parse_dependencies

_CFG = load_gui_config()
_COLORS = _CFG.section("colors")
_TT = _CFG.section("task_table")

_COLOR_LOOP = _COLORS.get("loop_row", (254, 243, 199, 110))
_COLOR_SUBTASK = _COLORS.get("subtask_row", (240, 240, 245, 90))
_EMPTY_COLOR = _COLORS.get("empty_text", (160, 160, 170))

_SUCC_ADD_TAG = "succ_add_modal"
_PICK_TAG = "task_pick_modal"

SUCC_TYPES = [d.value for d in DepType]

_RE_RESOURCE_TOKENS = re.compile(r'([A-Za-z_]\w*)')


def _on_enter_focus_next(sender, app_data, user_data) -> None:
    """Bei Enter: Fokus auf das gleichnamige Feld der nächsten Zeile."""
    if user_data and dpg.does_item_exist(user_data):
        dpg.focus_item(user_data)


def _render_resource_colored(rid: str, suffix: str, color_map: dict) -> None:
    """
    Rendert einen (ggf. zusammengesetzten) Ressourcen-String farbig, z. B.
    R_DEV1, R_PERS3&B1 oder R_PERS1&L1 | R_PERS2&L2. Trennzeichen bleiben neutral.
    """
    parts = [p for p in _RE_RESOURCE_TOKENS.split(rid) if p]
    if not parts:
        dpg.add_text(rid + suffix)
        return
    parts[-1] += suffix   # kein zusätzliches DPG-Spacing vor dem Komma
    for part in parts:
        color = color_map.get(part.rstrip(", "))
        dpg.add_text(part, color=color) if color else dpg.add_text(part)


# ---------------------------------------------------------------------------
# Abschnitts-Aufbau
# ---------------------------------------------------------------------------

def build_task_section(app) -> None:
    """Erstellt den Aufgaben-Abschnitt mit Toolbar und Tabellen-Container."""
    with dpg.collapsing_header(label=t("section.tasks"), tag="section_tasks_header", default_open=True):
        with dpg.group(horizontal=True):
            dpg.add_button(label=t("tt.add_task"), callback=lambda: app.add_task_row(False))
            dpg.add_button(label=t("tt.add_loop"), callback=lambda: app.add_task_row(True))
        dpg.add_spacer(height=3)
        dpg.add_text(t("tt.hint"), color=_COLORS.get("hint_text", (140, 140, 150)))
        dpg.add_spacer(height=3)
        with dpg.group(tag="task_table_container"):
            dpg.add_text(t("tt.empty"), color=_EMPTY_COLOR)


def _input(tag: str, value: str, next_tag, **kwargs) -> None:
    dpg.add_input_text(tag=tag, default_value=value, width=-1, on_enter=True,
                       callback=_on_enter_focus_next, user_data=next_tag, **kwargs)


def rebuild_task_table(app) -> None:
    """Löscht den Tabellen-Container und baut die Tabelle aus app.task_rows neu auf."""
    if not dpg.does_item_exist("task_table_container"):
        return
    dpg.delete_item("task_table_container", children_only=True)

    rows = app.task_rows
    if not rows:
        dpg.add_text(t("tt.empty"), parent="task_table_container", color=_EMPTY_COLOR)
        return

    color_map = resource_color_map(app.project)

    with dpg.table(parent="task_table_container", tag="task_table", header_row=True, resizable=True,
                   borders_outerH=True, borders_innerV=True, borders_outerV=True, row_background=True,
                   scrollX=False, policy=dpg.mvTable_SizingStretchProp):
        for label, fixed, key, default in [
            ("#", True, "col_id_width", 60), (t("col.name"), False, "col_name_weight", 0.28),
            (t("tt.col.duration"), True, "col_duration_width", 85),
            (t("tt.col.successors"), False, "col_successor_weight", 0.20),
            ("+", True, "col_succ_add_width", 32), ("-", True, "col_succ_rem_width", 32),
            (t("tt.col.resources"), False, "col_resource_weight", 0.20),
            ("+", True, "col_res_add_width", 32), ("-", True, "col_res_rem_width", 32),
            (t("tt.col.cost"), True, "col_cost_width", 75), (t("tt.col.actions"), True, "col_actions_width", 95),
        ]:
            if fixed:
                dpg.add_table_column(label=label, width_fixed=True, init_width_or_weight=_TT.get(key, default))
            else:
                dpg.add_table_column(label=label, width_stretch=True, init_width_or_weight=_TT.get(key, default))

        for i, row in enumerate(rows):
            def nxt(field: str) -> str | None:
                return f"task_{i + 1}_{field}" if i + 1 < len(rows) else None

            with dpg.table_row():
                _input(f"task_{i}_id", row.id, nxt("id"), no_spaces=True)
                _input(f"task_{i}_name", row.name, nxt("name"), hint="Loop-Task" if row.is_loop else "Task-Name")
                _input(f"task_{i}_duration", row.duration, nxt("duration"),
                       hint="10d / 4h / 30m", enabled=not row.is_loop)
                dpg.add_input_text(tag=f"task_{i}_successors_str", default_value=row.successors_str,
                                   width=-1, enabled=False, readonly=True)
                dpg.add_button(label="+", width=-1, enabled=not row.is_subtask,
                               callback=_open_add_successor, user_data=(app, i))
                dpg.add_button(label="-", width=-1, enabled=not row.is_subtask,
                               callback=_open_remove_successor, user_data=(app, i))

                res_ids = row.resource_list
                with dpg.group(horizontal=True):
                    if res_ids and color_map:
                        for k, rid in enumerate(res_ids):
                            _render_resource_colored(rid, "" if k == len(res_ids) - 1 else ", ", color_map)
                    else:
                        dpg.add_text(row.resources, color=_EMPTY_COLOR)
                dpg.add_button(label="+", width=-1, callback=_open_add_resource, user_data=(app, i))
                dpg.add_button(label="-", width=-1, enabled=bool(res_ids),
                               callback=_open_remove_resource, user_data=(app, i))

                _input(f"task_{i}_cost", row.cost, nxt("cost"), hint="0.0")

                with dpg.group(horizontal=True):
                    dpg.add_button(label="X", width=_TT.get("delete_btn_width", 28),
                                   callback=lambda s, a, u: u[0].delete_task_row(u[1]), user_data=(app, i))
                    if row.is_loop:
                        dpg.add_button(label="+Sub", width=_TT.get("subtask_btn_width", 40),
                                       callback=lambda s, a, u: u[0].add_subtask_to_loop(u[1]),
                                       user_data=(app, i))

    for i, row in enumerate(rows):
        if row.is_loop:
            dpg.highlight_table_row("task_table", i, _COLOR_LOOP)
        elif row.is_subtask:
            dpg.highlight_table_row("task_table", i, _COLOR_SUBTASK)


def _update_row(app, row_idx: int, **fields) -> None:
    """Übernimmt offene Eingaben, ändert die Zeile und baut die Tabelle neu auf."""
    app._read_task_rows_from_ui()
    if row_idx < len(app.task_rows):
        for name, value in fields.items():
            setattr(app.task_rows[row_idx], name, value)
        app.dirty = True
        rebuild_task_table(app)


# ---------------------------------------------------------------------------
# Gemeinsame Dialoge
# ---------------------------------------------------------------------------

def _info_dialog(tag: str, title: str, text: str, cfg_section: str) -> None:
    with dpg.window(label=title, tag=tag, modal=True, no_resize=True,
                    width=_CFG.resolve(cfg_section, "width", 300), height=_CFG.resolve(cfg_section, "height", 80),
                    pos=[_CFG.resolve(cfg_section, "pos_x", 450), _CFG.resolve(cfg_section, "pos_y", 320)]):
        dpg.add_text(text)
        dpg.add_button(label=t("dialog.about_close"), callback=lambda: dpg.delete_item(tag))


def _open_pick_dialog(title: str, prompt: str, labels: List[str], confirm_label: str,
                      on_confirm: Callable[[List[int]], None], empty_text: str, cfg_section: str) -> None:
    """Checkbox-Liste; on_confirm erhält die Indizes der markierten Einträge."""
    if dpg.does_item_exist(_PICK_TAG):
        dpg.delete_item(_PICK_TAG)
    if not labels:
        _info_dialog(_PICK_TAG, title, empty_text, f"{cfg_section}_empty")
        return

    cfg = _CFG.section(cfg_section)
    height = min(cfg.get("base_height", 80) + len(labels) * cfg.get("row_height", 26), cfg.get("max_height", 400))

    def _confirm() -> None:
        selected = [k for k in range(len(labels)) if dpg.get_value(f"pick_cb_{k}")]
        dpg.delete_item(_PICK_TAG)
        if selected:
            on_confirm(selected)

    with dpg.window(label=title, tag=_PICK_TAG, modal=True, no_resize=False, height=height,
                    width=_CFG.resolve(cfg_section, "width", 300),
                    pos=[_CFG.resolve(cfg_section, "pos_x", 450), _CFG.resolve(cfg_section, "pos_y", 300)]):
        dpg.add_text(prompt, color=_COLORS.get("dialog_prompt", (180, 180, 200)))
        dpg.add_spacer(height=4)
        for k, label in enumerate(labels):
            dpg.add_checkbox(tag=f"pick_cb_{k}", label=label, default_value=False)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(label=confirm_label, callback=_confirm)
            dpg.add_button(label=t("dialog.cancel"), callback=lambda: dpg.delete_item(_PICK_TAG))


# ---------------------------------------------------------------------------
# Nachfolger
# ---------------------------------------------------------------------------

def _open_add_successor(sender, app_data, user_data) -> None:
    """Dialog: Task-ID und Abhängigkeitstyp für einen neuen Nachfolger."""
    app, row_idx = user_data
    if dpg.does_item_exist(_SUCC_ADD_TAG):
        dpg.delete_item(_SUCC_ADD_TAG)

    own_id = app.task_rows[row_idx].id if row_idx < len(app.task_rows) else ""
    ids = list(dict.fromkeys(r.id for r in app.task_rows if r.id and r.id != own_id))
    if not ids:
        _info_dialog(_SUCC_ADD_TAG, t("tt.add_successor"), t("tt.no_other_tasks"), "dialog.successor_add_empty")
        return

    _sa = "dialog.successor_add"
    with dpg.window(label=t("tt.add_successor"), tag=_SUCC_ADD_TAG, modal=True, no_resize=True,
                    width=_CFG.resolve(_sa, "width", 320), height=_CFG.resolve(_sa, "height", 130),
                    pos=[_CFG.resolve(_sa, "pos_x", 450), _CFG.resolve(_sa, "pos_y", 300)]):
        with dpg.table(header_row=False, borders_outerH=False, borders_outerV=False,
                       borders_innerV=False, policy=dpg.mvTable_SizingFixedFit):
            dpg.add_table_column(width_fixed=True,
                                 init_width_or_weight=_CFG.section("successor_dialog_table").get("col_label_width", 90))
            dpg.add_table_column(width_stretch=True)
            with dpg.table_row():
                dpg.add_text("Task-ID:")
                dpg.add_combo(tag="succ_add_id", items=ids, default_value=ids[0], width=-1)
            with dpg.table_row():
                dpg.add_text(t("col.type") + ":")
                dpg.add_combo(tag="succ_add_type", items=SUCC_TYPES, default_value="EA", width=-1)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(label=t("button.add"), callback=lambda: _confirm_add_successor(app, row_idx))
            dpg.add_button(label=t("dialog.cancel"), callback=lambda: dpg.delete_item(_SUCC_ADD_TAG))


def _confirm_add_successor(app, row_idx: int) -> None:
    new_dep = parse_dependencies(f"{dpg.get_value('succ_add_id')}[{dpg.get_value('succ_add_type')}]")
    dpg.delete_item(_SUCC_ADD_TAG)
    if row_idx >= len(app.task_rows) or not new_dep:
        return
    deps = parse_dependencies(app.task_rows[row_idx].successors_str)
    if new_dep[0] not in deps:
        _update_row(app, row_idx, successors_str=format_dependencies(deps + new_dep))


def _open_remove_successor(sender, app_data, user_data) -> None:
    app, row_idx = user_data
    deps: List[Dependency] = parse_dependencies(app.task_rows[row_idx].successors_str)

    def _remove(selected: List[int]) -> None:
        remaining = [d for k, d in enumerate(deps) if k not in selected]
        _update_row(app, row_idx, successors_str=format_dependencies(remaining))

    _open_pick_dialog(t("tt.remove_successor"), t("tt.pick_remove"),
                      [f"{d.target}  [{d.type.value}]" for d in deps], t("tt.remove"), _remove,
                      t("tt.no_successors"), "dialog.successor_remove")


# ---------------------------------------------------------------------------
# Ressourcen
# ---------------------------------------------------------------------------

def _open_add_resource(sender, app_data, user_data) -> None:
    app, row_idx = user_data
    if row_idx >= len(app.task_rows):
        return
    current = app.task_rows[row_idx].resource_list
    all_ids = sorted(r.id for r in (app.project.resources or [])) if app.project else []
    available = [rid for rid in all_ids if rid not in current]

    def _add(selected: List[int]) -> None:
        _update_row(app, row_idx, resources=", ".join(current + [available[k] for k in selected]))

    _open_pick_dialog(t("tt.add_resource"), t("tt.pick_add"), available, t("button.add"), _add,
                      t("tt.all_assigned"), "dialog.resource_add")


def _open_remove_resource(sender, app_data, user_data) -> None:
    app, row_idx = user_data
    if row_idx >= len(app.task_rows):
        return
    current = app.task_rows[row_idx].resource_list

    def _remove(selected: List[int]) -> None:
        _update_row(app, row_idx, resources=", ".join(r for k, r in enumerate(current) if k not in selected))

    _open_pick_dialog(t("tt.remove_resource"), t("tt.pick_remove"), current, t("tt.remove"), _remove,
                      t("task.no_resources"), "dialog.resource_remove")
