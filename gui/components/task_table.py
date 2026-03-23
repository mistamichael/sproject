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

import dearpygui.dearpygui as dpg

# Amber-Farbe für Loop-Zeilen
_COLOR_LOOP = (254, 243, 199, 110)
# Hellgrau für Subtask-Zeilen
_COLOR_SUBTASK = (240, 240, 245, 90)

_SUCC_ADD_TAG = "succ_add_modal"
_SUCC_REM_TAG = "succ_rem_modal"

SUCC_TYPES = ["EA", "AA", "EE", "AE"]


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
        label="② Aufgaben",
        tag="section_tasks",
        default_open=True,
    ):
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="+ Aufgabe",
                callback=lambda: app.add_task_row(False),
            )
            dpg.add_button(
                label="↺ Loop-Task",
                callback=lambda: app.add_task_row(True),
            )

        dpg.add_spacer(height=3)
        dpg.add_text(
            "Nachfolger über + / - Buttons bearbeiten  ·  Ressourcen: Komma-getrennte IDs",
            color=(140, 140, 150),
        )
        dpg.add_spacer(height=3)

        with dpg.group(tag="task_table_container"):
            dpg.add_text(
                "Keine Aufgaben – bitte eine Projektdatei laden.",
                color=(160, 160, 170),
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
            color=(160, 160, 170),
        )
        return

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
        dpg.add_table_column(label="#",          width_fixed=True,   init_width_or_weight=60)
        dpg.add_table_column(label="Name",       width_stretch=True, init_width_or_weight=0.28)
        dpg.add_table_column(label="Dauer",      width_fixed=True,   init_width_or_weight=85)
        dpg.add_table_column(label="Nachfolger", width_stretch=True, init_width_or_weight=0.20)
        dpg.add_table_column(label="+",          width_fixed=True,   init_width_or_weight=32)
        dpg.add_table_column(label="-",          width_fixed=True,   init_width_or_weight=32)
        dpg.add_table_column(label="Ressourcen", width_stretch=True, init_width_or_weight=0.20)
        dpg.add_table_column(label="Kosten",     width_fixed=True,   init_width_or_weight=75)
        dpg.add_table_column(label="Aktionen",   width_fixed=True,   init_width_or_weight=95)

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
                    hint="🔁 Loop-Task" if is_loop else "Task-Name",
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

                # Spalte: Ressourcen (Input + Picker-Button)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(
                        tag=f"task_{i}_resources",
                        default_value=row.get("resources", ""),
                        width=-30,
                        hint="R1, R2",
                    )
                    dpg.add_button(
                        label="🔍",
                        width=25,
                        callback=_open_resource_picker,
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
                        label="🗑",
                        width=28,
                        callback=_delete_row,
                        user_data=(app, i),
                    )
                    if is_loop:
                        dpg.add_button(
                            label="+Sub",
                            width=40,
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

    if not unique_ids:
        with dpg.window(
            label="Nachfolger hinzufügen",
            tag=_SUCC_ADD_TAG,
            modal=True,
            width=300,
            height=80,
            pos=[450, 320],
            no_resize=True,
        ):
            dpg.add_text("Keine anderen Tasks vorhanden.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_SUCC_ADD_TAG))
        return

    with dpg.window(
        label="Nachfolger hinzufügen",
        tag=_SUCC_ADD_TAG,
        modal=True,
        width=320,
        height=130,
        pos=[450, 300],
        no_resize=True,
    ):
        with dpg.table(header_row=False, borders_outerH=False, borders_outerV=False,
                       borders_innerV=False, policy=dpg.mvTable_SizingFixedFit):
            dpg.add_table_column(width_fixed=True, init_width_or_weight=90)
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

    if not items:
        with dpg.window(
            label="Nachfolger entfernen",
            tag=_SUCC_REM_TAG,
            modal=True,
            width=280,
            height=80,
            pos=[450, 320],
            no_resize=True,
        ):
            dpg.add_text("Keine Nachfolger vorhanden.")
            dpg.add_button(label="Schließen", callback=lambda: dpg.delete_item(_SUCC_REM_TAG))
        return

    # Checkboxen für jeden Eintrag; Tag-Map: cb_tags[idx] = checkbox_tag
    cb_tags: dict = {}
    height = min(80 + len(items) * 26, 400)

    with dpg.window(
        label="Nachfolger entfernen",
        tag=_SUCC_REM_TAG,
        modal=True,
        width=300,
        height=height,
        pos=[450, 300],
        no_resize=False,
    ):
        dpg.add_text("Zu entfernende Einträge auswählen:", color=(180, 180, 200))
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


def _open_resource_picker(sender, app_data, user_data) -> None:
    app, row_idx = user_data
    tag = f"task_{row_idx}_resources"
    current = dpg.get_value(tag) if dpg.does_item_exist(tag) else ""

    def on_confirm(new_resources: str) -> None:
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, new_resources)
        if row_idx < len(app._task_rows):
            app._task_rows[row_idx]["resources"] = new_resources
        app.dirty = True

    from gui.components.resource_picker import open_resource_picker
    open_resource_picker(app, current, on_confirm)
