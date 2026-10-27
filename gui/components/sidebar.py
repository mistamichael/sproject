"""
Sidebar – Wizard-Navigation (Dear PyGui)
=========================================

Linke Sidebar mit 7 Wizard-Schritten.  Optionale Abschnitte können
per Checkbox ein- und ausgeschaltet werden.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path

from gui.gui_config import load_gui_config
from moncapro.paths import get_examples_dir
from gui.i18n import t

_CFG = load_gui_config()
_COL = _CFG.section("colors")


# (section_id, immer_aktiv) – Beschriftung: t("section.<id>"), erst beim Aufbau übersetzt
# (beim Import steht die Sprache aus gui.cfg noch nicht fest)
SECTIONS = [
    ("stammdaten",    True),
    ("tasks",         True),
    ("resources",     False),
    ("persons",       False),
    ("resting_times", False),
    ("uncertainty",   False),
    ("scenarios",     False),
]

# Tags der Sidebar-Beschriftungen → i18n-Schlüssel (für den Sprachwechsel in gui/app.py)
LABEL_TAGS = {f"sidebar_label_{section_id}": f"section.{section_id}" for section_id, _ in SECTIONS}
TEXT_TAGS = {"sidebar_wizard": "sidebar.wizard", "sidebar_examples": "sidebar.examples"}

# Toggle-Tag-Map für die optionalen Abschnitte
TOGGLE_TAGS = {
    "resources":     "sidebar_res_toggle",
    "persons":       "sidebar_pers_toggle",
    "resting_times": "sidebar_rest_toggle",
    "uncertainty":   "sidebar_uncertainty_toggle",
    "scenarios":     "sidebar_scenarios_toggle",
}


def build_sidebar(app) -> None:
    """Baut die Wizard-Navigations-Sidebar auf."""
    dpg.add_text(t("sidebar.wizard"), tag="sidebar_wizard", color=_COL.get("sidebar_wizard", (160, 160, 180)))
    dpg.add_separator()
    dpg.add_spacer(height=4)

    for section_id, always_active in SECTIONS:
        label, tag = t(f"section.{section_id}"), f"sidebar_label_{section_id}"
        if always_active:
            # Klickbarer Text scrollt zur Sektion
            dpg.add_button(
                label=label,
                tag=tag,
                width=-1,
                callback=lambda s, a, u: dpg.focus_item(u),
                user_data=f"section_{section_id}",
            )
        else:
            toggle_tag = TOGGLE_TAGS[section_id]
            is_active = app.active_sections.get(section_id, False)
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    tag=toggle_tag,
                    default_value=is_active,
                    callback=lambda s, v, u: _on_toggle(s, v, u),
                    user_data=(app, section_id),
                )
                dpg.add_text(label, tag=tag, color=_COL.get("sidebar_inactive", (180, 180, 200)) if not is_active else _COL.get("sidebar_active", (220, 220, 255)))

        dpg.add_spacer(height=2)

    dpg.add_separator()
    dpg.add_spacer(height=6)

    # Beispieldateien
    dpg.add_text(t("sidebar.examples"), tag="sidebar_examples", color=_COL.get("sidebar_examples", (140, 140, 160)))
    dpg.add_spacer(height=2)

    examples_dir = get_examples_dir()
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
