"""
Aufgabentabelle (Herzstück) – Dear PyGui
=========================================

Baut die zentrale Task-Tabelle auf.

Besonderheiten:
- rebuild_task_table() löscht den Container und erstellt die Tabelle neu
- Loop-Zeilen: amber-Hintergrund (highlight_table_row)
- Subtask-Zeilen: hellgrauer Hintergrund
- Nachfolger-Spalte: schreibgeschützt; Bearbeitung via + / - Buttons
  - "+": Dialog zum Hinzufügen (Task-ID + Typ EA/AA/EE/AE)
  - "-": Checkboxen zum Entfernen einzelner Einträge
- Ressourcen: Komma-Liste + 🔍-Button öffnet Ressourcen-Picker
"""

import configparser

import dearpygui.dearpygui as dpg

from gui.gui_config import load_gui_config
from gui.i18n import t
from lib.utils import get_cfg_dir, interpolate_color, hex_to_rgb

_CFG = load_gui_config()
_COLORS = _CFG.section("colors")
_TT = _CFG.section("task_table")

# Zeilen-Highlights
_COLOR_LOOP = _COLORS.get("loop_row", (254, 243, 199, 110))
_COLOR_SUBTASK = _COLORS.get("subtask_row", (240, 240, 245, 90))

_SUCC_ADD_TAG = "succ_add_modal"
_SUCC_REM_TAG = "succ_rem_modal"
_RES_ADD_TAG = "res_add_modal"
_RES_REM_TAG = "res_rem_modal"

SUCC_TYPES = ["EA", "AA", "EE", "AE"]


_DEFAULT_PALETTE = ["9B59B6", "3498DB", "27AE60", "F1C40F", "E67E22"]


def _interpolate_palette(palette: list, position: float) -> str:
    """Interpoliert entlang einer Multi-Stop-Palette (Liste von Hex-Farben).

    position: 0.0 bis 1.0 ueber das gesamte Spektrum.
    Gibt Hex-Farbe ohne # zurueck.
    """
    if len(palette) < 2:
        return palette[0] if palette else "888888"
    # Position auf Segmente abbilden
    n_segments = len(palette) - 1
    scaled = position * n_segments
    idx = min(int(scaled), n_segments - 1)
    local_pos = scaled - idx
    return interpolate_color(palette[idx], palette[idx + 1], local_pos)


import re

_RE_RESOURCE_TOKENS = re.compile(r'([A-Za-z_]\w*)')


def _render_resource_colored(rid: str, suffix: str, color_map: dict) -> None:
    """Rendert einen (ggf. zusammengesetzten) Ressourcen-String farbig.

    Unterstützt einfache IDs (R_DEV1), zusammengesetzte (R_PERS3&B1)
    und Alternativen (R_PERS1&L1 | R_PERS2&L2).
    Jeder erkannte Ressourcen-Name wird in seiner Farbe dargestellt,
    Trennzeichen (&, |, Leerzeichen) werden neutral angezeigt.
    """
    # Tokenisiere: abwechselnd Bezeichner und Trennzeichen
    parts = _RE_RESOURCE_TOKENS.split(rid)
    # parts = ['', 'R_PERS3', '&', 'B1', ''] oder aehnlich
    rendered_any = False
    for part in parts:
        if not part:
            continue
        color = color_map.get(part)
        if color:
            dpg.add_text(part, color=color)
            rendered_any = True
        else:
            # Trennzeichen (&, |, Leerzeichen) oder unbekannte ID
            dpg.add_text(part)
            rendered_any = True
    if suffix:
        dpg.add_text(suffix)
    if not rendered_any:
        dpg.add_text(rid + suffix)


def _build_resource_color_map(app) -> dict:
    """Berechnet resource_id -> (R, G, B) aus gui.cfg [resources_colours] palette.

    Die palette ist eine kommagetrennte Liste von Hex-Stuetzfarben.
    Fallback: color_start/color_end (2-Farben) oder defaults.cfg [ResourceAutoColor].
    """
    if not app.project or not app.project.resources:
        return {}

    cfg = configparser.ConfigParser()
    cfg_dir = get_cfg_dir()
    cfg.read([str(cfg_dir / "gui.cfg"), str(cfg_dir / "defaults.cfg")], encoding="utf-8")

    palette = list(_DEFAULT_PALETTE)
    if cfg.has_section("resources_colours"):
        raw = cfg.get("resources_colours", "palette", fallback="").strip()
        if raw:
            palette = [c.strip() for c in raw.split(",") if c.strip()]
        else:
            # Fallback auf altes color_start/color_end Format
            cs = cfg.get("resources_colours", "color_start", fallback="").strip()
            ce = cfg.get("resources_colours", "color_end", fallback="").strip()
            if cs and ce:
                palette = [cs, ce]
    elif cfg.has_section("ResourceAutoColor"):
        cs = cfg.get("ResourceAutoColor", "color_start", fallback="4472C4").strip()
        ce = cfg.get("ResourceAutoColor", "color_end", fallback="8B7AB8").strip()
        palette = [cs, ce]

    res_ids = sorted(r.id for r in app.project.resources)
    n = len(res_ids)
    color_map = {}
    for i, rid in enumerate(res_ids):
        pos = i / max(n - 1, 1) if n > 1 else 0.0
        hex_color = _interpolate_palette(palette, pos)
        color_map[rid] = hex_to_rgb(hex_color)
    return color_map


# ---------------------------------------------------------------------------
# Hilfs-Funktionen für Nachfolger-Strings
# ---------------------------------------------------------------------------

def _parse_successors(s: str) -> list:
    """
    Parst "2[EA], 3[AA], 5[EA]" → [("2","EA"), ("3","AA"), ("5","EA")].
    Fehlende Typ-Angabe wird als "EA" behandelt.
    """
    result = []
    if not s.strip():
        return result
    for item in s.split(","):
        item = item.strip()
        if not item:
            continue
        if "[" in item:
            id_part, rest = item.rsplit("[", 1)
            typ = rest.rstrip("]").upper()
            if typ not in SUCC_TYPES:
                typ = "EA"
        else:
            id_part, typ = item, "EA"
        id_part = id_part.strip()
        if id_part:
            result.append((id_part, typ))
    return result


def _format_successors(items: list) -> str:
    """[("2","EA"), ("3","AA")] → "2[EA], 3[AA]"."""
    return ", ".join(f"{id_}[{typ}]" for id_, typ in items)


# ---------------------------------------------------------------------------
# Abschnitts-Aufbau
# ---------------------------------------------------------------------------


def build_task_section(app) -> None:
    """Erstellt den Aufgaben-Abschnitt mit Toolbar und Tabellen-Container."""
    with dpg.collapsing_header(
        label=t("section.tasks"),
        tag="section_tasks_header",
        default_open=True,
    ):
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="+ Aufgabe",
                callback=lambda: app.add_task_row(False),
            )
            dpg.add_button(
                label="+ Loop-Task",
                callback=lambda: app.add_task_row(True),
            )

        dpg.add_spacer(height=3)
        dpg.add_text(
            "Nachfolger und Ressourcen über + / - Buttons bearbeiten",
            color=_COLORS.get("hint_text", (140, 140, 150)),
        )
        dpg.add_spacer(height=3)

        with dpg.group(tag="task_table_container"):
            dpg.add_text(
                "Keine Aufgaben – bitte eine Projektdatei laden.",
                color=_COLORS.get("empty_text", (160, 160, 170)),
            )


# ---------------------------------------------------------------------------
# Tabelle neu aufbauen
# ---------------------------------------------------------------------------

def rebuild_task_table(app) -> None:
    """
    Löscht den Tabellen-Container und baut die Tabelle neu auf.
    Wird nach jedem Laden, Hinzufügen oder Löschen einer Zeile aufgerufen.
    """
    if not dpg.does_item_exist("task_table_container"):
        return

    dpg.delete_item("task_table_container", children_only=True)

    if not app._task_rows:
        dpg.add_text(
            "Keine Aufgaben – bitte eine Projektdatei laden.",
            parent="task_table_container",
            color=_COLORS.get("empty_text", (160, 160, 170)),
        )
        return

    resource_color_map = _build_resource_color_map(app)

    loop_indices: list = []
    subtask_indices: list = []

    with dpg.table(
        parent="task_table_container",
        tag="task_table",
        header_row=True,
        resizable=True,
        borders_outerH=True,
        borders_innerV=True,
        borders_outerV=True,
        row_background=True,
        scrollX=False,
        policy=dpg.mvTable_SizingStretchProp,
    ):
        dpg.add_table_column(label="#",          width_fixed=True,   init_width_or_weight=_TT.get("col_id_width", 60))
        dpg.add_table_column(label="Name",       width_stretch=True, init_width_or_weight=_TT.get("col_name_weight", 0.28))
        dpg.add_table_column(label="Dauer",      width_fixed=True,   init_width_or_weight=_TT.get("col_duration_width", 85))
        dpg.add_table_column(label="Nachfolger", width_stretch=True, init_width_or_weight=_TT.get("col_successor_weight", 0.20))
        dpg.add_table_column(label="+",          width_fixed=True,   init_width_or_weight=_TT.get("col_succ_add_width", 32))
        dpg.add_table_column(label="-",          width_fixed=True,   init_width_or_weight=_TT.get("col_succ_rem_width", 32))
        dpg.add_table_column(label="Ressourcen", width_stretch=True, init_width_or_weight=_TT.get("col_resource_weight", 0.20))
        dpg.add_table_column(label="+",          width_fixed=True,   init_width_or_weight=_TT.get("col_res_add_width", 32))
        dpg.add_table_column(label="-",          width_fixed=True,   init_width_or_weight=_TT.get("col_res_rem_width", 32))
        dpg.add_table_column(label="Kosten",     width_fixed=True,   init_width_or_weight=_TT.get("col_cost_width", 75))
        dpg.add_table_column(label="Aktionen",   width_fixed=True,   init_width_or_weight=_TT.get("col_actions_width", 95))

        for i, row in enumerate(app._task_rows):
            is_subtask = row.get("row_type") == "subtask"
            is_loop    = row.get("row_type") == "loop"

            with dpg.table_row():
                # Spalte: ID
                dpg.add_input_text(
                    tag=f"task_{i}_id",
                    default_value=str(row.get("id", "")),
                    width=-1,
                    no_spaces=True,
                )

                # Spalte: Name
                dpg.add_input_text(
                    tag=f"task_{i}_name",
                    default_value=row.get("name", ""),
                    width=-1,
                    hint="Loop-Task" if is_loop else "Task-Name",
                )

                # Spalte: Dauer
                dpg.add_input_text(
                    tag=f"task_{i}_duration",
                    default_value=row.get("duration", ""),
                    width=-1,
                    hint="10d / 4h / 30m",
                    enabled=not is_loop,
                )

                # Spalte: Nachfolger  (schreibgeschützt – Bearbeitung via + / -)
                dpg.add_input_text(
                    tag=f"task_{i}_successors_str",
                    default_value=row.get("successors_str", ""),
                    width=-1,
                    enabled=False,       # schreibgeschützt
                    readonly=True,
                )

                # Spalte: + (Nachfolger hinzufügen)
                dpg.add_button(
                    label="+",
                    width=-1,
                    enabled=not is_subtask,
                    callback=_open_add_successor,
                    user_data=(app, i),
                )

                # Spalte: - (Nachfolger entfernen)
                dpg.add_button(
                    label="-",
                    width=-1,
                    enabled=not is_subtask,
                    callback=_open_remove_successor,
                    user_data=(app, i),
                )

                # Spalte: Ressourcen (farbige IDs, schreibgeschützt)
                with dpg.group(horizontal=True):
                    res_str = row.get("resources", "")
                    res_ids = [r.strip() for r in res_str.split(",") if r.strip()]
                    if res_ids and resource_color_map:
                        for k, rid in enumerate(res_ids):
                            suffix = "" if k == len(res_ids) - 1 else ", "
                            _render_resource_colored(rid, suffix, resource_color_map)
                    elif res_str.strip():
                        dpg.add_text(res_str)
                    else:
                        dpg.add_text("", color=(160, 160, 170))

                # Spalte: + (Ressource hinzufügen)
                dpg.add_button(
                    label="+",
                    width=-1,
                    callback=_open_add_resource,
                    user_data=(app, i),
                )

                # Spalte: - (Ressource entfernen)
                dpg.add_button(
                    label="-",
                    width=-1,
                    enabled=bool(res_ids),
                    callback=_open_remove_resource,
                    user_data=(app, i),
                )

                # Spalte: Kosten
                dpg.add_input_text(
                    tag=f"task_{i}_cost",
                    default_value=row.get("cost", ""),
                    width=-1,
                    hint="0.0",
                )

                # Spalte: Aktionen
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="X",
                        width=_TT.get("delete_btn_width", 28),
                        callback=_delete_row,
                        user_data=(app, i),
                    )
                    if is_loop:
                        dpg.add_button(
                            label="+Sub",
                            width=_TT.get("subtask_btn_width", 40),
                            callback=_add_subtask,
                            user_data=(app, i),
                        )

            row_type = row.get("row_type", "simple")
            if row_type == "loop":
                loop_indices.append(i)
            elif row_type == "subtask":
                subtask_indices.append(i)

    for idx in loop_indices:
        dpg.highlight_table_row("task_table", idx, _COLOR_LOOP)
    for idx in subtask_indices:
        dpg.highlight_table_row("task_table", idx, _COLOR_SUBTASK)


# ---------------------------------------------------------------------------
# Nachfolger hinzufügen – Dialog
# ---------------------------------------------------------------------------

def _open_add_successor(sender, app_data, user_data) -> None:
    """Öffnet einen Dialog zum Hinzufügen eines Nachfolgers."""
    app, row_idx = user_data

    if dpg.does_item_exist(_SUCC_ADD_TAG):
        dpg.delete_item(_SUCC_ADD_TAG)

    # Alle verfügbaren Task-IDs (ohne die eigene)
    own_id = str(app._task_rows[row_idx].get("id", "")) if row_idx < len(app._task_rows) else ""
    all_ids = [
        str(r.get("id", ""))
        for r in app._task_rows
        if str(r.get("id", "")) and str(r.get("id", "")) != own_id
    ]
    # Deduplizieren, Reihenfolge erhalten
    seen = set()
    unique_ids = [x for x in all_ids if not (x in seen or seen.add(x))]

    _se = "dialog.successor_add_empty"
    if not unique_ids:
        with dpg.window(
            label="Nachfolger hinzufügen",
            tag=_SUCC_ADD_TAG,
            modal=True,
            width=_CFG.resolve(_se, "width", 300),
            height=_CFG.resolve(_se, "height", 80),
            pos=[_CFG.resolve(_se, "pos_x", 450), _CFG.resolve(_se, "pos_y", 320)],
            no_resize=True,
        ):
            dpg.add_text("Keine anderen Tasks vorhanden.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_SUCC_ADD_TAG))
        return

    _sa = "dialog.successor_add"
    _sdt = _CFG.section("successor_dialog_table")
    with dpg.window(
        label="Nachfolger hinzufügen",
        tag=_SUCC_ADD_TAG,
        modal=True,
        width=_CFG.resolve(_sa, "width", 320),
        height=_CFG.resolve(_sa, "height", 130),
        pos=[_CFG.resolve(_sa, "pos_x", 450), _CFG.resolve(_sa, "pos_y", 300)],
        no_resize=True,
    ):
        with dpg.table(header_row=False, borders_outerH=False, borders_outerV=False,
                       borders_innerV=False, policy=dpg.mvTable_SizingFixedFit):
            dpg.add_table_column(width_fixed=True, init_width_or_weight=_sdt.get("col_label_width", 90))
            dpg.add_table_column(width_stretch=True)

            with dpg.table_row():
                dpg.add_text("Task-ID:")
                dpg.add_combo(
                    tag="succ_add_id",
                    items=unique_ids,
                    default_value=unique_ids[0],
                    width=-1,
                )
            with dpg.table_row():
                dpg.add_text("Typ:")
                dpg.add_combo(
                    tag="succ_add_type",
                    items=SUCC_TYPES,
                    default_value="EA",
                    width=-1,
                )

        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Hinzufügen",
                callback=lambda: _confirm_add_successor(app, row_idx),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(_SUCC_ADD_TAG),
            )


def _confirm_add_successor(app, row_idx: int) -> None:
    """Fügt den gewählten Nachfolger in die Nachfolger-Liste ein."""
    new_id   = dpg.get_value("succ_add_id")   if dpg.does_item_exist("succ_add_id")   else ""
    new_type = dpg.get_value("succ_add_type") if dpg.does_item_exist("succ_add_type") else "EA"

    if dpg.does_item_exist(_SUCC_ADD_TAG):
        dpg.delete_item(_SUCC_ADD_TAG)

    if not new_id or row_idx >= len(app._task_rows):
        return

    succ_tag = f"task_{row_idx}_successors_str"
    current  = dpg.get_value(succ_tag) if dpg.does_item_exist(succ_tag) else ""
    items    = _parse_successors(current)

    # Doppeleinträge (gleiche ID + Typ) verhindern
    if not any(id_ == new_id and typ == new_type for id_, typ in items):
        items.append((new_id, new_type))

    new_str = _format_successors(items)

    if dpg.does_item_exist(succ_tag):
        dpg.set_value(succ_tag, new_str)
    if row_idx < len(app._task_rows):
        app._task_rows[row_idx]["successors_str"] = new_str
    app.dirty = True


# ---------------------------------------------------------------------------
# Nachfolger entfernen – Dialog
# ---------------------------------------------------------------------------

def _open_remove_successor(sender, app_data, user_data) -> None:
    """Öffnet einen Dialog zum Entfernen eines oder mehrerer Nachfolger."""
    app, row_idx = user_data

    if dpg.does_item_exist(_SUCC_REM_TAG):
        dpg.delete_item(_SUCC_REM_TAG)

    succ_tag = f"task_{row_idx}_successors_str"
    current  = dpg.get_value(succ_tag) if dpg.does_item_exist(succ_tag) else ""
    items    = _parse_successors(current)

    _sre = "dialog.successor_remove_empty"
    if not items:
        with dpg.window(
            label="Nachfolger entfernen",
            tag=_SUCC_REM_TAG,
            modal=True,
            width=_CFG.resolve(_sre, "width", 280),
            height=_CFG.resolve(_sre, "height", 80),
            pos=[_CFG.resolve(_sre, "pos_x", 450), _CFG.resolve(_sre, "pos_y", 320)],
            no_resize=True,
        ):
            dpg.add_text("Keine Nachfolger vorhanden.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_SUCC_REM_TAG))
        return

    # Checkboxen für jeden Eintrag; Tag-Map: cb_tags[idx] = checkbox_tag
    cb_tags: dict = {}
    _sr = "dialog.successor_remove"
    _sr_s = _CFG.section(_sr)
    height = min(
        _sr_s.get("base_height", 80) + len(items) * _sr_s.get("row_height", 26),
        _sr_s.get("max_height", 400),
    )

    with dpg.window(
        label="Nachfolger entfernen",
        tag=_SUCC_REM_TAG,
        modal=True,
        width=_CFG.resolve(_sr, "width", 300),
        height=height,
        pos=[_CFG.resolve(_sr, "pos_x", 450), _CFG.resolve(_sr, "pos_y", 300)],
        no_resize=False,
    ):
        dpg.add_text("Zu entfernende Einträge auswählen:", color=_COLORS.get("dialog_prompt", (180, 180, 200)))
        dpg.add_spacer(height=4)

        for k, (id_, typ) in enumerate(items):
            cb_tag = f"succ_rem_cb_{k}"
            dpg.add_checkbox(
                tag=cb_tag,
                label=f"{id_}  [{typ}]",
                default_value=False,
            )
            cb_tags[k] = cb_tag

        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Entfernen",
                callback=lambda: _confirm_remove_successor(app, row_idx, items, cb_tags),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(_SUCC_REM_TAG),
            )


def _confirm_remove_successor(app, row_idx: int, items: list, cb_tags: dict) -> None:
    """Entfernt die markierten Nachfolger."""
    remaining = [
        entry for k, entry in enumerate(items)
        if not (dpg.does_item_exist(cb_tags.get(k, "")) and dpg.get_value(cb_tags[k]))
    ]

    if dpg.does_item_exist(_SUCC_REM_TAG):
        dpg.delete_item(_SUCC_REM_TAG)

    if row_idx >= len(app._task_rows):
        return

    new_str  = _format_successors(remaining)
    succ_tag = f"task_{row_idx}_successors_str"

    if dpg.does_item_exist(succ_tag):
        dpg.set_value(succ_tag, new_str)
    app._task_rows[row_idx]["successors_str"] = new_str
    app.dirty = True


# ---------------------------------------------------------------------------
# Restliche Callbacks
# ---------------------------------------------------------------------------

def _delete_row(sender, app_data, user_data) -> None:
    app, row_idx = user_data
    app.delete_task_row(row_idx)


def _add_subtask(sender, app_data, user_data) -> None:
    app, loop_row_idx = user_data
    app.add_subtask_to_loop(loop_row_idx)


def _open_add_resource(sender, app_data, user_data) -> None:
    """Öffnet einen Dialog zum Hinzufügen einer Ressource (Checkbox-Liste der noch nicht verwendeten)."""
    app, row_idx = user_data

    if dpg.does_item_exist(_RES_ADD_TAG):
        dpg.delete_item(_RES_ADD_TAG)

    if row_idx >= len(app._task_rows):
        return

    # Aktuell zugewiesene Ressourcen
    current_str = app._task_rows[row_idx].get("resources", "")
    current_ids = {r.strip() for r in current_str.split(",") if r.strip()}

    # Alle verfügbaren Ressourcen aus dem Projekt
    all_res_ids = sorted(r.id for r in app.project.resources) if app.project and app.project.resources else []

    # Noch nicht verwendete
    available = [rid for rid in all_res_ids if rid not in current_ids]

    _rae = "dialog.resource_add_empty"
    if not available:
        with dpg.window(
            label="Ressource hinzufügen",
            tag=_RES_ADD_TAG,
            modal=True,
            width=_CFG.resolve(_rae, "width", 300),
            height=_CFG.resolve(_rae, "height", 80),
            pos=[_CFG.resolve(_rae, "pos_x", 450), _CFG.resolve(_rae, "pos_y", 320)],
            no_resize=True,
        ):
            dpg.add_text("Alle Ressourcen bereits zugewiesen.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_RES_ADD_TAG))
        return

    cb_tags: dict = {}
    _ra = "dialog.resource_add"
    _ra_s = _CFG.section(_ra)
    height = min(
        _ra_s.get("base_height", 80) + len(available) * _ra_s.get("row_height", 26),
        _ra_s.get("max_height", 400),
    )

    with dpg.window(
        label="Ressource hinzufügen",
        tag=_RES_ADD_TAG,
        modal=True,
        width=_CFG.resolve(_ra, "width", 320),
        height=height,
        pos=[_CFG.resolve(_ra, "pos_x", 450), _CFG.resolve(_ra, "pos_y", 300)],
        no_resize=False,
    ):
        dpg.add_text("Ressourcen zum Hinzufügen auswählen:", color=_COLORS.get("dialog_prompt", (180, 180, 200)))
        dpg.add_spacer(height=4)

        for k, rid in enumerate(available):
            cb_tag = f"res_add_cb_{k}"
            dpg.add_checkbox(tag=cb_tag, label=rid, default_value=False)
            cb_tags[k] = cb_tag

        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Hinzufügen",
                callback=lambda: _confirm_add_resource(app, row_idx, available, cb_tags),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(_RES_ADD_TAG),
            )


def _confirm_add_resource(app, row_idx: int, available: list, cb_tags: dict) -> None:
    """Fügt die ausgewählten Ressourcen hinzu."""
    selected = [
        available[k] for k in sorted(cb_tags.keys())
        if dpg.does_item_exist(cb_tags[k]) and dpg.get_value(cb_tags[k])
    ]

    if dpg.does_item_exist(_RES_ADD_TAG):
        dpg.delete_item(_RES_ADD_TAG)

    if not selected or row_idx >= len(app._task_rows):
        return

    current_str = app._task_rows[row_idx].get("resources", "")
    current_ids = [r.strip() for r in current_str.split(",") if r.strip()]
    current_ids.extend(selected)

    new_str = ", ".join(current_ids)
    app._task_rows[row_idx]["resources"] = new_str
    app.dirty = True
    rebuild_task_table(app)


def _open_remove_resource(sender, app_data, user_data) -> None:
    """Öffnet einen Dialog zum Entfernen von Ressourcen (Checkbox-Liste der aktuell vorhandenen)."""
    app, row_idx = user_data

    if dpg.does_item_exist(_RES_REM_TAG):
        dpg.delete_item(_RES_REM_TAG)

    if row_idx >= len(app._task_rows):
        return

    current_str = app._task_rows[row_idx].get("resources", "")
    current_ids = [r.strip() for r in current_str.split(",") if r.strip()]

    _rre = "dialog.resource_remove_empty"
    if not current_ids:
        with dpg.window(
            label="Ressource entfernen",
            tag=_RES_REM_TAG,
            modal=True,
            width=_CFG.resolve(_rre, "width", 280),
            height=_CFG.resolve(_rre, "height", 80),
            pos=[_CFG.resolve(_rre, "pos_x", 450), _CFG.resolve(_rre, "pos_y", 320)],
            no_resize=True,
        ):
            dpg.add_text("Keine Ressourcen vorhanden.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_RES_REM_TAG))
        return

    cb_tags: dict = {}
    _rr = "dialog.resource_remove"
    _rr_s = _CFG.section(_rr)
    height = min(
        _rr_s.get("base_height", 80) + len(current_ids) * _rr_s.get("row_height", 26),
        _rr_s.get("max_height", 400),
    )

    with dpg.window(
        label="Ressource entfernen",
        tag=_RES_REM_TAG,
        modal=True,
        width=_CFG.resolve(_rr, "width", 300),
        height=height,
        pos=[_CFG.resolve(_rr, "pos_x", 450), _CFG.resolve(_rr, "pos_y", 300)],
        no_resize=False,
    ):
        dpg.add_text("Zu entfernende Ressourcen auswählen:", color=_COLORS.get("dialog_prompt", (180, 180, 200)))
        dpg.add_spacer(height=4)

        for k, rid in enumerate(current_ids):
            cb_tag = f"res_rem_cb_{k}"
            dpg.add_checkbox(tag=cb_tag, label=rid, default_value=False)
            cb_tags[k] = cb_tag

        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Entfernen",
                callback=lambda: _confirm_remove_resource(app, row_idx, current_ids, cb_tags),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(_RES_REM_TAG),
            )


def _confirm_remove_resource(app, row_idx: int, current_ids: list, cb_tags: dict) -> None:
    """Entfernt die markierten Ressourcen."""
    remaining = [
        rid for k, rid in enumerate(current_ids)
        if not (dpg.does_item_exist(cb_tags.get(k, "")) and dpg.get_value(cb_tags[k]))
    ]

    if dpg.does_item_exist(_RES_REM_TAG):
        dpg.delete_item(_RES_REM_TAG)

    if row_idx >= len(app._task_rows):
        return

    new_str = ", ".join(remaining)
    app._task_rows[row_idx]["resources"] = new_str
    app.dirty = True
    rebuild_task_table(app)
