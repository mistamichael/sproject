"""
Sidebar – Wizard-Navigation (Dear PyGui)
=========================================

Linke Sidebar mit 5 Wizard-Schritten.  Optionale Abschnitte können
per Checkbox ein- und ausgeschaltet werden.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path

from gui.gui_config import load_gui_config

_CFG = load_gui_config()
_COL = _CFG.section("colors")


# (section_id, Anzeige-Label, immer_aktiv)
SECTIONS = [
    ("stammdaten",    "1. Stammdaten",  True),
    ("tasks",         "2. Aufgaben",    True),
    ("resources",     "3. Ressourcen",  False),
    ("persons",       "4. Personen",    False),
    ("resting_times", "5. Ruhezeiten",  False),
]

# Toggle-Tag-Map für die drei optionalen Abschnitte
_TOGGLE_TAGS = {
    "resources":     "sidebar_res_toggle",
    "persons":       "sidebar_pers_toggle",
    "resting_times": "sidebar_rest_toggle",
}


def build_sidebar(app) -> None:
    """Baut die Wizard-Navigations-Sidebar auf."""
    dpg.add_text("WIZARD", color=_COL.get("sidebar_wizard", (160, 160, 180)))
    dpg.add_separator()
    dpg.add_spacer(height=4)

    for section_id, label, always_active in SECTIONS:
        if always_active:
            # Klickbarer Text scrollt zur Sektion
            dpg.add_button(
                label=label,
                width=-1,
                callback=lambda s, a, u: dpg.focus_item(u),
                user_data=f"section_{section_id}",
            )
        else:
            toggle_tag = _TOGGLE_TAGS[section_id]
            is_active = app.active_sections.get(section_id, False)
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    tag=toggle_tag,
                    default_value=is_active,
                    callback=lambda s, v, u: _on_toggle(s, v, u),
                    user_data=(app, section_id),
                )
                dpg.add_text(label, color=_COL.get("sidebar_inactive", (180, 180, 200)) if not is_active else _COL.get("sidebar_active", (220, 220, 255)))

        dpg.add_spacer(height=2)

    dpg.add_separator()
    dpg.add_spacer(height=6)

    # Beispieldateien
    dpg.add_text("Beispiele:", color=_COL.get("sidebar_examples", (140, 140, 160)))
    dpg.add_spacer(height=2)

    examples_dir = Path(__file__).parent.parent.parent / "examples"
    if examples_dir.exists():
        for jf in sorted(examples_dir.glob("*.json")):
            dpg.add_button(
                label=jf.stem,
                width=-1,
                callback=lambda s, a, u: u[0].load_from_file(u[1]),
                user_data=(app, jf),
            )
            dpg.add_spacer(height=1)


def _on_toggle(sender, value: bool, user_data) -> None:
    """Callback für den Toggle-Checkbox einer optionalen Sektion."""
    app, section_id = user_data
    app.active_sections[section_id] = value
    app._update_section_visibility()
    app._update_sidebar()
