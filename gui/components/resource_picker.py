"""
Ressourcen-Picker Dialog (Dear PyGui)
======================================

Öffnet ein modales Fenster zur Auswahl von Ressourcen.
Das Fenster wird bei jedem Öffnen frisch erstellt und beim Schließen gelöscht.
"""

from typing import Callable
import dearpygui.dearpygui as dpg

_PICKER_TAG = "resource_picker_modal"


def open_resource_picker(app, current_resources: str, on_confirm: Callable) -> None:
    """
    Öffnet den Ressourcen-Picker als modales Fenster.

    Args:
        app:               ProjectEditorApp-Instanz
        current_resources: Komma-getrennte IDs der aktuell gewählten Ressourcen
        on_confirm:        Callback(new_resources_str) nach Bestätigung
    """
    # Altes Fenster aufräumen
    if dpg.does_item_exist(_PICKER_TAG):
        dpg.delete_item(_PICKER_TAG)

    if not app.project or not app.project.resources:
        # Kein Projekt oder keine Ressourcen – kurze Info-Meldung
        with dpg.window(
            label="Ressourcen",
            tag=_PICKER_TAG,
            modal=True,
            width=320,
            height=80,
            pos=[400, 300],
            no_resize=True,
        ):
            dpg.add_text("Keine Ressourcen definiert.")
            dpg.add_button(
                label="Schließen",
                callback=lambda: dpg.delete_item(_PICKER_TAG),
            )
        return

    current_ids = {r.strip() for r in current_resources.split(",") if r.strip()}

    # Checkboxen pro Ressource merken: {res_id: checkbox_tag}
    cb_tags: dict = {}
    # Zeilen-Tags für Typ-Filter: {res_id: (row_group_tag, res_type)}
    row_tags: dict = {}

    height = min(120 + len(app.project.resources) * 26, 500)

    with dpg.window(
        label="Ressourcen zuweisen",
        tag=_PICKER_TAG,
        modal=True,
        width=460,
        height=height,
        pos=[350, 180],
        no_resize=False,
    ):
        # Typ-Filter
        with dpg.group(horizontal=True):
            dpg.add_text("Typ-Filter:")
            type_filter = dpg.add_combo(
                items=["Alle", "person", "machine", "truck", "oven"],
                default_value="Alle",
                width=120,
                callback=lambda s, v: _apply_filter(v, row_tags),
            )

        dpg.add_separator()
        dpg.add_spacer(height=3)

        for res in app.project.resources:
            res_type = res.type or "?"
            color_hex = res.color or "888888"
            res_name = res.name or res.id
            row_group_tag = f"rp_row_{res.id}"

            with dpg.group(horizontal=True, tag=row_group_tag):
                cb_tag = f"rp_cb_{res.id}"
                dpg.add_checkbox(
                    tag=cb_tag,
                    default_value=(res.id in current_ids),
                )
                cb_tags[res.id] = cb_tag

                # Farbpunkt als gefärbter Text-Marker
                try:
                    r_int = int(color_hex[0:2], 16)
                    g_int = int(color_hex[2:4], 16)
                    b_int = int(color_hex[4:6], 16)
                    dot_color = (r_int, g_int, b_int, 220)
                except (ValueError, IndexError):
                    dot_color = (150, 150, 150, 200)
                dpg.add_text("●", color=dot_color)

                dpg.add_text(res.id, color=(220, 220, 255))
                dpg.add_text(res_name, color=(200, 200, 200))
                dpg.add_text(f"[{res_type}]", color=(150, 150, 170))

            row_tags[res.id] = (row_group_tag, res_type)
            dpg.add_spacer(height=1)

        dpg.add_separator()
        dpg.add_spacer(height=4)

        # Aktions-Buttons
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Alle",
                width=60,
                callback=lambda: [dpg.set_value(t, True) for t in cb_tags.values()],
            )
            dpg.add_button(
                label="Keine",
                width=60,
                callback=lambda: [dpg.set_value(t, False) for t in cb_tags.values()],
            )
            dpg.add_spacer(width=20)

            def _confirm():
                chosen = [
                    rid for rid, tag in cb_tags.items()
                    if dpg.does_item_exist(tag) and dpg.get_value(tag)
                ]
                on_confirm(", ".join(chosen))
                if dpg.does_item_exist(_PICKER_TAG):
                    dpg.delete_item(_PICKER_TAG)

            dpg.add_button(
                label="Übernehmen",
                callback=_confirm,
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(_PICKER_TAG),
            )


def _apply_filter(selected_type: str, row_tags: dict) -> None:
    """Zeigt/versteckt Ressourcen-Zeilen je nach gewähltem Typ."""
    for rid, (row_tag, res_type) in row_tags.items():
        visible = selected_type == "Alle" or res_type == selected_type
        if dpg.does_item_exist(row_tag):
            dpg.configure_item(row_tag, show=visible)
