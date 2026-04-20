"""
sproject Editor – Dear PyGui Application
==========================================

Einstiegspunkt. Starten mit:

    python gui/app.py
    # oder via
    bin/gui.bat

Layout:
    ┌─ Menüleiste: Datei ──────────────────────────────┐
    ├─ Icon-Toolbar: [🗁][💾][📄][⬇] | [▶] ─────────────┤
    │  Status …                                         │
    ├───────────────────────────────────────────────────┤
    │  SIDEBAR  │  1 Stammdaten                         │
    │           │  2 Aufgaben                           │
    │           │  3 Ressourcen (opt.)                  │
    │           │  4 Personen   (opt.)                  │
    │           │  5 Ruhezeiten (opt.)                  │
    │           │  CPM-Ergebnis (nach Berechnung)       │
    └───────────┴───────────────────────────────────────┘
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import dearpygui.dearpygui as dpg

from gui.editor import ProjectEditorApp
from gui.icons import setup_icon_textures, add_icon_button
from gui.components.sidebar import build_sidebar
from gui.components.task_table import build_task_section
from gui.components.file_browser import open_file_browser
from gui.gui_config import load_gui_config
from gui.i18n import t, set_language, get_language

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
TAG_MAIN_WIN     = "main_window"
TAG_SAVE_DLG     = "save_dialog"
TAG_EXP_DLG      = "export_dialog"
TAG_ABOUT_WIN    = "about_window"
TAG_GLOBAL_THEME = "global_theme"

# Config laden (Singleton)
CFG = load_gui_config()

# Sprache aus Config initialisieren
set_language(CFG.active_language)

# DPG-Farb-Mapping: cfg-Key → DPG-Konstante
_THEME_COLOR_MAP = {
    "window_bg":        "mvThemeCol_WindowBg",
    "child_bg":         "mvThemeCol_ChildBg",
    "frame_bg":         "mvThemeCol_FrameBg",
    "button":           "mvThemeCol_Button",
    "button_hovered":   "mvThemeCol_ButtonHovered",
    "header":           "mvThemeCol_Header",
    "header_hovered":   "mvThemeCol_HeaderHovered",
    "table_header_bg":  "mvThemeCol_TableHeaderBg",
    "table_row_bg":     "mvThemeCol_TableRowBg",
    "table_row_bg_alt": "mvThemeCol_TableRowBgAlt",
    "menu_bar_bg":      "mvThemeCol_MenuBarBg",
    "popup_bg":         "mvThemeCol_PopupBg",
    "text":             "mvThemeCol_Text",
}


def _create_and_bind_theme() -> None:
    """Erstellt das globale DPG-Theme aus der aktiven Config und bindet es."""
    if dpg.does_item_exist(TAG_GLOBAL_THEME):
        dpg.delete_item(TAG_GLOBAL_THEME)

    tc = CFG.theme_colors()
    _sty = CFG.section("style")

    with dpg.theme(tag=TAG_GLOBAL_THEME):
        with dpg.theme_component(dpg.mvAll):
            for cfg_key, dpg_name in _THEME_COLOR_MAP.items():
                if cfg_key in tc:
                    dpg.add_theme_color(
                        getattr(dpg, dpg_name), tc[cfg_key],
                        category=dpg.mvThemeCat_Core,
                    )
            dpg.add_theme_style(
                dpg.mvStyleVar_FrameRounding,
                _sty.get("frame_rounding", 4),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowRounding,
                _sty.get("window_rounding", 4),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemSpacing,
                _sty.get("item_spacing_x", 6),
                _sty.get("item_spacing_y", 4),
                category=dpg.mvThemeCat_Core,
            )
    dpg.bind_theme(TAG_GLOBAL_THEME)


def _apply_theme(editor: ProjectEditorApp, theme_name: str) -> None:
    """Wechselt das Farb-Theme live."""
    CFG.set_active_theme(theme_name)
    _create_and_bind_theme()
    # Checkmarks aktualisieren
    for name in CFG.available_themes():
        tag = f"mi_theme_{name}"
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, name == theme_name)
    editor._set_status(t("status.theme_changed", theme=t(f"theme.{theme_name}")))


def _update_ui_language() -> None:
    """Aktualisiert alle getaggten UI-Elemente auf die aktive Sprache."""
    # Elemente die configure_item(label=...) verwenden (Menues, Buttons, Header)
    _label_map = {
        # Menues
        "menu_file":        "menu.file",
        "menu_settings":    "menu.settings",
        "menu_help":        "menu.help",
        "menu_theme":       "menu.settings.theme",
        "menu_language":    "menu.settings.language",
        # Menuepunkte
        "mi_open":          "menu.file.open",
        "mi_save":          "menu.file.save",
        "mi_save_as":       "menu.file.save_as",
        "mi_export":        "menu.file.export",
        "mi_close":         "menu.file.close",
        "mi_about":         "menu.help.about",
        # Sektions-Header
        "section_stammdaten":           "section.stammdaten",
        "section_tasks_header":         "section.tasks",
        "section_resources_header":     "section.resources",
        "section_persons_header":       "section.persons",
        "section_resting_times_header": "section.resting_times",
        "section_result_header":        "section.result",
    }
    for tag, key in _label_map.items():
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, label=t(key))

    # Theme-Menuepunkte (dynamisch aus verfuegbaren Themes)
    for name in CFG.available_themes():
        tag = f"mi_theme_{name}"
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, label=t(f"theme.{name}"))

    # Text-Elemente die set_value() verwenden (dpg.add_text)
    _text_map = {
        "lbl_project_name": "label.project_name",
        "lbl_start_date":   "label.start_date",
        "lbl_unit":         "label.unit",
        "lbl_total_hours":  "label.total_hours",
        "lbl_total_volume": "label.total_volume",
        "lbl_order_volume": "label.order_volume"
    }
    for tag, key in _text_map.items():
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, t(key))


def _switch_language(editor: ProjectEditorApp, lang: str) -> None:
    """Wechselt die UI-Sprache live."""
    set_language(lang)
    CFG.set_active_language(lang)
    # Checkmarks aktualisieren
    for code in ("de", "en"):
        tag = f"mi_lang_{code}"
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, code == lang)
    _update_ui_language()
    editor._set_status(t("status.language_changed", lang=lang))

VIEWPORT_W = CFG.base_width
VIEWPORT_H = CFG.base_height
SIDEBAR_W  = CFG.resolve("layout", "sidebar_width", 210)


# ---------------------------------------------------------------------------
# Öffnen-Browser
# ---------------------------------------------------------------------------

def _show_open_browser(app: ProjectEditorApp) -> None:
    """Öffnet den eigenen Datei-Browser zum Laden einer JSON-Datei."""
    start = (
        app._last_save_path.parent
        if app._last_save_path
        else Path(__file__).parent.parent / "examples"
    )
    open_file_browser(
        callback=app.load_from_file,
        start_path=start,
        title="Projekt öffnen",
        file_ext=".json",
    )


# ---------------------------------------------------------------------------
# Speichern-Dialog
# ---------------------------------------------------------------------------

def _open_save_dialog(app: ProjectEditorApp) -> None:
    if app.project is None:
        app._set_status("Kein Projekt geladen.")
        return
    if dpg.does_item_exist(TAG_SAVE_DLG):
        dpg.delete_item(TAG_SAVE_DLG)

    default_name = (app.project.project or "project").replace(" ", "_") + ".json"
    default_path = str(
        (app._last_save_path or Path.cwd() / default_name)
    )

    _s = "dialog.save"
    with dpg.window(
        label="Speichern unter …",
        tag=TAG_SAVE_DLG,
        modal=True,
        width=CFG.resolve(_s, "width", 520),
        height=CFG.resolve(_s, "height", 110),
        pos=[CFG.resolve(_s, "pos_x", 380), CFG.resolve(_s, "pos_y", 360)],
        no_resize=True,
    ):
        dpg.add_input_text(
            tag="save_path_input",
            default_value=default_path,
            width=-1,
            hint="Zielpfad der JSON-Datei",
        )
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            def _do_save():
                path_str = dpg.get_value("save_path_input")
                if path_str:
                    app.save_to_file(Path(path_str))
                if dpg.does_item_exist(TAG_SAVE_DLG):
                    dpg.delete_item(TAG_SAVE_DLG)

            dpg.add_button(label="Speichern", callback=_do_save)
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(TAG_SAVE_DLG),
            )


# ---------------------------------------------------------------------------
# Verzeichnis-Autocomplete für Export-Dialog
# ---------------------------------------------------------------------------

TAG_AC_POPUP    = "exp_ac_popup"
TAG_AC_LIST     = "exp_ac_list"
TAG_AC_HANDLERS = "exp_ac_handlers"


def _get_dir_completions(text: str) -> list[str]:
    p = Path(text)
    if text.endswith(("/", "\\")):
        parent, prefix = p, ""
    else:
        parent, prefix = p.parent, p.name.lower()
    try:
        return [
            str(parent / d.name)
            for d in sorted(parent.iterdir())
            if d.is_dir() and d.name.lower().startswith(prefix)
        ]
    except OSError:
        return []


def _close_ac_popup() -> None:
    if dpg.does_item_exist(TAG_AC_POPUP):
        dpg.delete_item(TAG_AC_POPUP)


def _ac_select(app: ProjectEditorApp, value: str) -> None:
    _close_ac_popup()
    if dpg.does_item_exist("exp_dir_input"):
        dpg.set_value("exp_dir_input", value)
        dpg.focus_item("exp_dir_input")


def _show_ac_popup(app: ProjectEditorApp, matches: list[str]) -> None:
    if not dpg.does_item_exist("exp_dir_input"):
        return
    _close_ac_popup()

    rect_min  = dpg.get_item_rect_min("exp_dir_input")
    rect_size = dpg.get_item_rect_size("exp_dir_input")
    pos   = [int(rect_min[0]), int(rect_min[1] + rect_size[1])]
    _ac = CFG.section("autocomplete")
    width = max(int(rect_size[0]), _ac.get("min_width", 260))
    n     = min(len(matches), _ac.get("max_items", 8))

    with dpg.window(
        tag=TAG_AC_POPUP,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
        pos=pos,
        width=width,
        height=n * _ac.get("item_height", 22) + _ac.get("padding", 14),
        no_scrollbar=True,
    ):
        dpg.add_listbox(
            tag=TAG_AC_LIST,
            items=matches,
            num_items=n,
            width=-1,
            callback=lambda s, a: _ac_select(app, a),
        )


def _ac_tab_handler(sender, app_data, user_data: ProjectEditorApp) -> None:
    if not dpg.does_item_exist("exp_dir_input"):
        return
    if dpg.is_item_focused("exp_dir_input"):
        # \t durch tab_input=True entfernen
        text = dpg.get_value("exp_dir_input").replace("\t", "")
        dpg.set_value("exp_dir_input", text)
        matches = _get_dir_completions(text)
        if not matches:
            return
        if len(matches) == 1:
            _close_ac_popup()
            dpg.set_value("exp_dir_input", matches[0])
        else:
            _show_ac_popup(user_data, matches)
    elif dpg.does_item_exist(TAG_AC_POPUP) and dpg.does_item_exist(TAG_AC_LIST):
        val = dpg.get_value(TAG_AC_LIST)
        if val:
            _ac_select(user_data, val)


def _ac_enter_handler(sender, app_data, user_data: ProjectEditorApp) -> None:
    if dpg.does_item_exist(TAG_AC_POPUP) and dpg.does_item_exist(TAG_AC_LIST):
        val = dpg.get_value(TAG_AC_LIST)
        if val:
            _ac_select(user_data, val)


def _setup_ac_handlers(app: ProjectEditorApp) -> None:
    if dpg.does_item_exist(TAG_AC_HANDLERS):
        dpg.delete_item(TAG_AC_HANDLERS)
    with dpg.handler_registry(tag=TAG_AC_HANDLERS):
        dpg.add_key_press_handler(
            dpg.mvKey_Tab, callback=_ac_tab_handler, user_data=app
        )
        dpg.add_key_press_handler(
            dpg.mvKey_Return, callback=_ac_enter_handler, user_data=app
        )
        dpg.add_key_press_handler(
            dpg.mvKey_Escape, callback=lambda s, a, u: _close_ac_popup()
        )


def _teardown_ac() -> None:
    _close_ac_popup()
    if dpg.does_item_exist(TAG_AC_HANDLERS):
        dpg.delete_item(TAG_AC_HANDLERS)


def _close_export_dialog() -> None:
    _teardown_ac()
    if dpg.does_item_exist(TAG_EXP_DLG):
        dpg.delete_item(TAG_EXP_DLG)


# ---------------------------------------------------------------------------
# Export-Dialog
# ---------------------------------------------------------------------------

def _open_export_dialog(app: ProjectEditorApp) -> None:
    if app.project is None:
        app._set_status("Kein Projekt geladen.")
        return
    if dpg.does_item_exist(TAG_EXP_DLG):
        dpg.delete_item(TAG_EXP_DLG)

    name = (app.project.project or "project").replace(" ", "_")
    import os
    results_dir = Path(os.environ.get("PV_RESULTS", "")) if os.environ.get("PV_RESULTS") else Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    default_dir = str(results_dir)

    needs_calc = not app.last_cpm_result  # MD/Excel/TXT brauchen Ergebnis

    _s = "dialog.export"
    _col = CFG.section("colors")
    with dpg.window(
        label="Export",
        tag=TAG_EXP_DLG,
        modal=True,
        width=CFG.resolve(_s, "width", 420),
        height=CFG.resolve(_s, "height", 240),
        pos=[CFG.resolve(_s, "pos_x", 430), CFG.resolve(_s, "pos_y", 260)],
        no_resize=True,
    ):
        dpg.add_text("Formate auswählen:", color=_col.get("dialog_label", (180, 180, 210)))
        dpg.add_spacer(height=5)

        # JSON ist immer möglich
        dpg.add_checkbox(
            tag="exp_chk_json",
            label=f"JSON       →  {name}.json",
            default_value=True,
        )
        # Folgende Formate brauchen ein Berechnungsergebnis
        for key, label, ext in [
            ("markdown", "Markdown",  "md"),
            ("excel",    "Excel",     "xlsx"),
            ("txt",      "Text",      "txt"),
        ]:
            tag = f"exp_chk_{key}"
            dpg.add_checkbox(
                tag=tag,
                label=f"{label:<10} →  {name}.{ext}",
                default_value=False,
                enabled=not needs_calc,
            )
        if needs_calc:
            dpg.add_text(
                "  ⚠ Markdown / Excel / TXT benötigen eine Berechnung (▶).",
                color=_col.get("warning_text", (220, 180, 60)),
            )

        dpg.add_spacer(height=8)
        dpg.add_separator()
        dpg.add_spacer(height=5)

        with dpg.group(horizontal=True):
            dpg.add_text("Zielordner:")
            dpg.add_input_text(
                tag="exp_dir_input",
                default_value=default_dir,
                width=-1,
                hint="Zielverzeichnis",
                tab_input=True,
                on_enter=False,
                callback=lambda: _close_ac_popup(),
            )

        dpg.add_spacer(height=8)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Exportieren",
                callback=lambda: _do_export(app),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: _close_export_dialog(),
            )

    _setup_ac_handlers(app)


def _do_export(app: ProjectEditorApp) -> None:
    target_dir = Path(dpg.get_value("exp_dir_input") or ".")
    _close_export_dialog()

    if not target_dir.exists():
        app._set_status(f"Verzeichnis nicht gefunden: {target_dir}")
        return

    exported: list[str] = []
    errors:   list[str] = []

    _tasks = [
        ("exp_chk_json",     app.export_json,     "JSON"),
        ("exp_chk_markdown", app.export_markdown, "Markdown"),
        ("exp_chk_excel",    app.export_excel,    "Excel"),
        ("exp_chk_txt",      app.export_txt,      "TXT"),
    ]
    for chk_tag, fn, label in _tasks:
        if dpg.does_item_exist(chk_tag) and dpg.get_value(chk_tag):
            try:
                fn(target_dir)
                exported.append(label)
            except Exception as exc:
                errors.append(f"{label}: {exc}")

    if errors:
        app._set_status("Export-Fehler: " + " | ".join(errors))
    elif exported:
        app._set_status(f"Exportiert: {', '.join(exported)}  →  {target_dir}")
    else:
        app._set_status("Keine Formate ausgewählt.")


# ---------------------------------------------------------------------------
# Abschnitts-Builder: Stammdaten
# ---------------------------------------------------------------------------

def _build_stammdaten(app: ProjectEditorApp) -> None:
    with dpg.collapsing_header(
        label=t("section.stammdaten"),
        tag="section_stammdaten",
        default_open=True,
    ):
        with dpg.table(
            header_row=False,
            borders_innerV=False,
            borders_outerH=False,
            borders_outerV=False,
            policy=dpg.mvTable_SizingStretchProp,
        ):
            _st = CFG.section("stammdaten_table")
            dpg.add_table_column(width_fixed=True,  init_width_or_weight=_st.get("col_label_width", 130))
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_fixed=True,  init_width_or_weight=_st.get("col_label2_width", 120))
            dpg.add_table_column(width_stretch=True)

            with dpg.table_row():
                dpg.add_text(t("label.project_name"), tag="lbl_project_name")
                dpg.add_input_text(tag="inp_project_name", default_value="",
                                   hint="Mein Projekt")
                dpg.add_text(t("label.start_date"), tag="lbl_start_date")
                dpg.add_input_text(tag="inp_project_start", default_value="",
                                   width=-1, hint="2026-01-01 08:00:00")
            with dpg.table_row():
                dpg.add_text(t("label.unit"), tag="lbl_unit")
                dpg.add_combo(tag="inp_unit", items=["days", "hours", "minutes"],
                              default_value="days")
                dpg.add_text(t("label.total_hours"), tag="lbl_total_hours")
                dpg.add_input_text(tag="inp_total_hours", default_value="",
                                   width=-1, hint="160")
            with dpg.table_row():
                dpg.add_text(t("label.total_volume"), tag="lbl_total_volume")
                dpg.add_input_text(tag="inp_total_volume", default_value="",
                                   hint="1000")
                dpg.add_text(t("label.order_volume"), tag="lbl_order_volume")
                dpg.add_input_text(tag="inp_order_volume", default_value="",
                                   width=-1, hint="12")
        dpg.add_spacer(height=2)


# ---------------------------------------------------------------------------
# Abschnitts-Builder: optionale Sektionen
# ---------------------------------------------------------------------------

def _build_resources_section(_app) -> None:
    with dpg.group(tag="section_resources", show=False):
        with dpg.collapsing_header(
            label=t("section.resources"),
            tag="section_resources_header",
            default_open=True
        ):
            dpg.add_button(
                label="+ Ressource",
                callback=lambda: _app._cb_add_resource(),
            )
            dpg.add_spacer(height=3)
            with dpg.group(tag="resources_content"):
                dpg.add_text("Keine Ressourcen geladen.")
        dpg.add_spacer(height=4)


def _build_persons_section(_app) -> None:
    with dpg.group(tag="section_persons", show=False):
        with dpg.collapsing_header(
            label=t("section.persons"),
            tag="section_persons_header",
            default_open=True
        ):
            dpg.add_button(
                label="+ Person",
                callback=lambda: _app._cb_add_person(),
            )
            dpg.add_spacer(height=3)
            with dpg.group(tag="persons_content"):
                dpg.add_text("Keine Personen geladen.")
        dpg.add_spacer(height=4)


def _build_resting_times_section(_app) -> None:
    with dpg.group(tag="section_resting_times", show=False):
        with dpg.collapsing_header(
                label=t("section.resting_times"),
                tag="section_resting_times_header",
                default_open=True
            ):
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="+ Ruhezeit",
                    callback=lambda: _app._cb_add_resting_time(),
                )
                dpg.add_button(
                    label="+ Urlaub",
                    callback=lambda: _app._cb_add_vacation(),
                )
                dpg.add_button(
                    label="+ Teilzeit",
                    callback=lambda: _app._cb_add_workinghours(),
                )
            dpg.add_spacer(height=3)
            with dpg.group(tag="resting_times_content"):
                dpg.add_text("Keine Ruhezeitregeln definiert.")
            dpg.add_spacer(height=4)
            with dpg.group(tag="vacation_content"):
                dpg.add_text("Kein Urlaub definiert.")
            dpg.add_spacer(height=4)
            with dpg.group(tag="workinghours_content"):
                dpg.add_text("Keine Teilzeitregelungen definiert.")
        dpg.add_spacer(height=4)


# ---------------------------------------------------------------------------
# Haupt-App zusammensetzen
# ---------------------------------------------------------------------------

def create_app() -> ProjectEditorApp:
    """Baut das vollständige DPG-Layout auf."""
    editor = ProjectEditorApp()

    # --- About-Fenster ---
    _s = "dialog.about"
    _col = CFG.section("colors")
    with dpg.window(
        label="Über sproject Editor",
        tag=TAG_ABOUT_WIN,
        show=False,
        modal=True,
        width=CFG.resolve(_s, "width", 400),
        height=CFG.resolve(_s, "height", 150),
        pos=[CFG.resolve(_s, "pos_x", 440), CFG.resolve(_s, "pos_y", 300)],
        no_resize=True,
    ):
        dpg.add_text("sproject Editor", color=_col.get("about_title", (180, 210, 255)))
        dpg.add_text("Einfache PyGui-Oberfläche für sproject-JSON-Dateien.")
        dpg.add_spacer(height=6)
        dpg.add_text("Beispiele: examples")
        dpg.add_button(
            label="Schließen",
            callback=lambda: dpg.configure_item(TAG_ABOUT_WIN, show=False),
        )

    # --- Hauptfenster ---
    with dpg.window(
        tag=TAG_MAIN_WIN,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
        no_close=True,
        no_scrollbar=False,
        menubar=True,
    ):
        # ── Menüleiste ──────────────────────────────────────────────────
        with dpg.menu_bar():
            with dpg.menu(label=t("menu.file"), tag="menu_file"):
                dpg.add_menu_item(
                    label=t("menu.file.open"),
                    tag="mi_open",
                    shortcut="Ctrl+O",
                    callback=lambda: _show_open_browser(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label=t("menu.file.save"),
                    tag="mi_save",
                    shortcut="Ctrl+S",
                    callback=lambda: editor.save_quick(),
                )
                dpg.add_menu_item(
                    label=t("menu.file.save_as"),
                    tag="mi_save_as",
                    shortcut="Ctrl+Shift+S",
                    callback=lambda: _open_save_dialog(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label=t("menu.file.export"),
                    tag="mi_export",
                    callback=lambda: _open_export_dialog(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label=t("menu.file.close"),
                    tag="mi_close",
                    callback=lambda: dpg.stop_dearpygui(),
                )

            with dpg.menu(label=t("menu.settings"), tag="menu_settings"):
                with dpg.menu(label=t("menu.settings.theme"), tag="menu_theme"):
                    for theme_name in CFG.available_themes():
                        dpg.add_menu_item(
                            label=t(f"theme.{theme_name}"),
                            tag=f"mi_theme_{theme_name}",
                            check=True,
                            default_value=(CFG.active_theme == theme_name),
                            callback=lambda s, a, u: _apply_theme(editor, u),
                            user_data=theme_name,
                        )
                with dpg.menu(label=t("menu.settings.language"), tag="menu_language"):
                    for lang_code, lang_label in [("de", "Deutsch"), ("en", "English")]:
                        dpg.add_menu_item(
                            label=lang_label,
                            tag=f"mi_lang_{lang_code}",
                            check=True,
                            default_value=(get_language() == lang_code),
                            callback=lambda s, a, u: _switch_language(editor, u),
                            user_data=lang_code,
                        )

            with dpg.menu(label=t("menu.help"), tag="menu_help"):
                dpg.add_menu_item(
                    label=t("menu.help.about"),
                    tag="mi_about",
                    callback=lambda: dpg.configure_item(TAG_ABOUT_WIN, show=True),
                )

        # ── Icon-Toolbar ─────────────────────────────────────────────────
        with dpg.group(horizontal=True, tag="icon_toolbar"):
            add_icon_button(
                "open", "Öffnen  (Ctrl+O)",
                callback=lambda: _show_open_browser(editor),
                tag="tb_open",
            )
            add_icon_button(
                "save", "Speichern  (Ctrl+S)",
                callback=lambda: editor.save_quick(),
                tag="tb_save",
            )
            add_icon_button(
                "save_as", "Speichern unter …  (Ctrl+Shift+S)",
                callback=lambda: _open_save_dialog(editor),
                tag="tb_save_as",
            )
            add_icon_button(
                "export", "Export …",
                callback=lambda: _open_export_dialog(editor),
                tag="tb_export",
            )

            dpg.add_text(" | ", color=_col.get("toolbar_sep", (100, 100, 110)))

            add_icon_button(
                "calculate", "Berechnen & Anzeigen",
                callback=lambda: editor.run_calculation(),
                tag="tb_calculate",
            )

        # Status-Zeile
        dpg.add_text(
            "Bereit – Datei öffnen oder links ein Beispiel wählen.",
            tag="statusbar_text",
            color=_col.get("status_text", (150, 160, 170)),
        )
        dpg.add_separator()
        dpg.add_spacer(height=2)

        # ── Zweispaltiges Layout ─────────────────────────────────────────
        with dpg.group(horizontal=True):
            # Linke Sidebar
            with dpg.child_window(
                tag="sidebar_panel",
                width=SIDEBAR_W,
                border=True,
                height=-1,
            ):
                build_sidebar(editor)

            # Rechter Hauptbereich
            with dpg.child_window(
                tag="main_content",
                width=-1,
                height=-1,
                border=False,
            ):
                _build_stammdaten(editor)
                dpg.add_spacer(height=4)

                build_task_section(editor)
                dpg.add_spacer(height=4)

                _build_resources_section(editor)
                _build_persons_section(editor)
                _build_resting_times_section(editor)

                # Ergebnis-Container
                dpg.add_spacer(height=4)
                with dpg.group(tag="result_container", show=False):
                    with dpg.collapsing_header(
                        label="CPM-Ergebnis",
                        default_open=True,
                    ):
                        pass

    return editor


# ---------------------------------------------------------------------------
# Viewport-Resize
# ---------------------------------------------------------------------------

def _resize_callback(sender, app_data) -> None:
    vp_w = dpg.get_viewport_client_width()
    vp_h = dpg.get_viewport_client_height()
    dpg.set_item_width(TAG_MAIN_WIN,  vp_w)
    dpg.set_item_height(TAG_MAIN_WIN, vp_h)


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main() -> None:
    dpg.create_context()

    # Icons laden (vor Widget-Erstellung)
    setup_icon_textures()

    # Theme aus Config laden und binden
    _create_and_bind_theme()

    # Font aus Config laden
    import os
    _font_cfg = CFG.section("font")
    font_path = _font_cfg.get("path", "")
    if font_path and os.path.exists(font_path):
        font_size = _font_cfg.get("size", 15)
        font_ranges = _font_cfg.get("ranges", [])
        with dpg.font_registry():
            with dpg.font(font_path, font_size) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                for start, end in font_ranges:
                    dpg.add_font_range(start, end)
        dpg.bind_font(default_font)

    create_app()

    dpg.create_viewport(
        title=CFG.get("viewport", "title", "sproject Editor"),
        width=VIEWPORT_W,
        height=VIEWPORT_H,
        min_width=CFG.resolve("viewport", "min_width", 900),
        min_height=CFG.resolve("viewport", "min_height", 600),
    )
    dpg.setup_dearpygui()
    dpg.set_primary_window(TAG_MAIN_WIN, True)
    dpg.set_viewport_resize_callback(_resize_callback)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
