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
    │  SIDEBAR  │  ① Stammdaten                         │
    │           │  ② Aufgaben                           │
    │           │  ③ Ressourcen (opt.)                  │
    │           │  ④ Personen   (opt.)                  │
    │           │  ⑤ Ruhezeiten (opt.)                  │
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

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
TAG_MAIN_WIN  = "main_window"
TAG_SAVE_DLG  = "save_dialog"
TAG_EXP_DLG   = "export_dialog"
TAG_ABOUT_WIN = "about_window"

VIEWPORT_W = 1280
VIEWPORT_H = 860
SIDEBAR_W  = 210


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

    with dpg.window(
        label="Speichern unter …",
        tag=TAG_SAVE_DLG,
        modal=True,
        width=520,
        height=110,
        pos=[380, 360],
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
# Export-Dialog
# ---------------------------------------------------------------------------

def _open_export_dialog(app: ProjectEditorApp) -> None:
    if app.project is None:
        app._set_status("Kein Projekt geladen.")
        return
    if dpg.does_item_exist(TAG_EXP_DLG):
        dpg.delete_item(TAG_EXP_DLG)

    name = (app.project.project or "project").replace(" ", "_")
    default_dir = str(
        app._last_save_path.parent if app._last_save_path else Path.cwd()
    )

    needs_calc = not app.last_cpm_result  # MD/Excel/TXT brauchen Ergebnis

    with dpg.window(
        label="Export",
        tag=TAG_EXP_DLG,
        modal=True,
        width=420,
        height=240,
        pos=[430, 260],
        no_resize=True,
    ):
        dpg.add_text("Formate auswählen:", color=(180, 180, 210))
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
                color=(220, 180, 60),
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
            )

        dpg.add_spacer(height=8)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Exportieren",
                callback=lambda: _do_export(app),
            )
            dpg.add_button(
                label="Abbrechen",
                callback=lambda: dpg.delete_item(TAG_EXP_DLG),
            )


def _do_export(app: ProjectEditorApp) -> None:
    target_dir = Path(dpg.get_value("exp_dir_input") or ".")
    if dpg.does_item_exist(TAG_EXP_DLG):
        dpg.delete_item(TAG_EXP_DLG)

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
        label="① Projekt-Stammdaten",
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
            dpg.add_table_column(width_fixed=True,  init_width_or_weight=130)
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_fixed=True,  init_width_or_weight=120)
            dpg.add_table_column(width_stretch=True)

            with dpg.table_row():
                dpg.add_text("Projektname:")
                dpg.add_input_text(tag="inp_project_name", default_value="",
                                   width=-1, hint="Mein Projekt")
                dpg.add_text("Startdatum:")
                dpg.add_input_text(tag="inp_project_start", default_value="",
                                   width=-1, hint="2026-01-01 08:00:00")
            with dpg.table_row():
                dpg.add_text("Zeiteinheit:")
                dpg.add_combo(tag="inp_unit", items=["days", "hours", "minutes"],
                              default_value="days", width=-1)
                dpg.add_text("Gesamtstunden:")
                dpg.add_input_text(tag="inp_total_hours", default_value="",
                                   width=-1, hint="160")
            with dpg.table_row():
                dpg.add_text("Gesamtvolumen:")
                dpg.add_input_text(tag="inp_total_volume", default_value="",
                                   width=-1, hint="1000")
                dpg.add_text("Auftragsvolumen:")
                dpg.add_input_text(tag="inp_order_volume", default_value="",
                                   width=-1, hint="12")
        dpg.add_spacer(height=2)


# ---------------------------------------------------------------------------
# Abschnitts-Builder: optionale Sektionen
# ---------------------------------------------------------------------------

def _build_resources_section(_app) -> None:
    with dpg.group(tag="section_resources", show=False):
        with dpg.collapsing_header(label="③ Ressourcen", default_open=True):
            with dpg.group(tag="resources_content"):
                dpg.add_text("Keine Ressourcen geladen.")
        dpg.add_spacer(height=4)


def _build_persons_section(_app) -> None:
    with dpg.group(tag="section_persons", show=False):
        with dpg.collapsing_header(label="④ Personen", default_open=True):
            with dpg.group(tag="persons_content"):
                dpg.add_text("Keine Personen geladen.")
        dpg.add_spacer(height=4)


def _build_resting_times_section(_app) -> None:
    with dpg.group(tag="section_resting_times", show=False):
        with dpg.collapsing_header(label="⑤ Ruhezeiten", default_open=True):
            with dpg.group(tag="resting_times_content"):
                dpg.add_text("Keine Ruhezeitregeln definiert.")
        dpg.add_spacer(height=4)


# ---------------------------------------------------------------------------
# Haupt-App zusammensetzen
# ---------------------------------------------------------------------------

def create_app() -> ProjectEditorApp:
    """Baut das vollständige DPG-Layout auf."""
    editor = ProjectEditorApp()

    # --- About-Fenster ---
    with dpg.window(
        label="Über sproject Editor",
        tag=TAG_ABOUT_WIN,
        show=False,
        modal=True,
        width=400,
        height=150,
        pos=[440, 300],
        no_resize=True,
    ):
        dpg.add_text("sproject Editor", color=(180, 210, 255))
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
            with dpg.menu(label="Datei"):
                dpg.add_menu_item(
                    label="Öffnen …",
                    shortcut="Ctrl+O",
                    callback=lambda: _show_open_browser(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Speichern",
                    shortcut="Ctrl+S",
                    callback=lambda: editor.save_quick(),
                )
                dpg.add_menu_item(
                    label="Speichern unter …",
                    shortcut="Ctrl+Shift+S",
                    callback=lambda: _open_save_dialog(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Export …",
                    callback=lambda: _open_export_dialog(editor),
                )
                dpg.add_separator()
                dpg.add_menu_item(
                    label="Schließen",
                    callback=lambda: dpg.stop_dearpygui(),
                )

            with dpg.menu(label="Hilfe"):
                dpg.add_menu_item(
                    label="Über …",
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

            dpg.add_text(" | ", color=(100, 100, 110))

            add_icon_button(
                "calculate", "Berechnen & Anzeigen",
                callback=lambda: editor.run_calculation(),
                tag="tb_calculate",
            )

        # Status-Zeile
        dpg.add_text(
            "Bereit – Datei öffnen oder links ein Beispiel wählen.",
            tag="statusbar_text",
            color=(150, 160, 170),
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

    # Dunkles Theme
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,      (30,  32,  38),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,       (34,  36,  43),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,       (45,  48,  58),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button,        (55,  90, 140),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 110, 170),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header,        (55,  90, 140),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (70, 110, 170),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (40,  55,  75),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg,    (32,  34,  40),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (38,  40,  48),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg,     (25,  27,  35),  category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4,               category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,4,               category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,   6, 4,            category=dpg.mvThemeCat_Core)

    dpg.bind_theme(global_theme)

    create_app()

    dpg.create_viewport(
        title="sproject Editor",
        width=VIEWPORT_W,
        height=VIEWPORT_H,
        min_width=900,
        min_height=600,
    )
    dpg.setup_dearpygui()
    dpg.set_primary_window(TAG_MAIN_WIN, True)
    dpg.set_viewport_resize_callback(_resize_callback)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
