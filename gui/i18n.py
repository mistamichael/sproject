"""
Internationalisierung (i18n) fuer die sproject GUI
====================================================

Einfaches Uebersetzungssystem mit dict-basierten Sprachpaketen.
Aktive Sprache wird ueber set_language() / get_language() gesteuert.
"""

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        # ── Menues ────────────────────────────────────────────────────────
        "menu.file": "Datei",
        "menu.settings": "Einstellungen",
        "menu.help": "Hilfe",
        "menu.file.open": "Öffnen …",
        "menu.file.save": "Speichern",
        "menu.file.save_as": "Speichern unter …",
        "menu.file.export": "Export …",
        "menu.file.close": "Schließen",
        "menu.settings.theme": "Theme",
        "menu.settings.language": "Sprache",
        "menu.help.about": "Über …",

        # ── Theme-Namen ───────────────────────────────────────────────────
        "theme.default": "Standard",
        "theme.dark": "Dunkel",
        "theme.light": "Hell",
        "theme.solarized_dark": "Solarized Dark",
        "theme.solarized_light": "Solarized Light",

        # ── Sektionen ─────────────────────────────────────────────────────
        "section.stammdaten": "1. Projekt-Stammdaten",
        "section.tasks": "2. Aufgaben",
        "section.resources": "3. Ressourcen",
        "section.persons": "4. Personen",
        "section.resting_times": "5. Ruhezeiten",
        "section.result": "CPM-Ergebnis",

        # ── Labels (Stammdaten) ───────────────────────────────────────────
        "label.project_name": "Projektname:",
        "label.start_date": "Startdatum:",
        "label.unit": "Zeiteinheit:",
        "label.total_hours": "Gesamtstunden:",
        "label.total_volume": "Gesamtvolumen:",
        "label.order_volume": "Auftragsvolumen:",

        # ── Toolbar-Tooltips ──────────────────────────────────────────────
        "tooltip.open": "Öffnen  (Ctrl+O)",
        "tooltip.save": "Speichern  (Ctrl+S)",
        "tooltip.save_as": "Speichern unter …  (Ctrl+Shift+S)",
        "tooltip.export": "Export …",
        "tooltip.calculate": "Berechnen & Anzeigen",

        # ── Dialoge ──────────────────────────────────────────────────────
        "dialog.save_title": "Speichern unter …",
        "dialog.save_btn": "Speichern",
        "dialog.cancel": "Abbrechen",
        "dialog.export_title": "Export",
        "dialog.export_btn": "Exportieren",
        "dialog.export_formats": "Formate auswählen:",
        "dialog.export_target": "Zielordner:",
        "dialog.export_warn": "  ⚠ Markdown / Excel / TXT benötigen eine Berechnung (▶).",
        "dialog.about_title": "Über sproject Editor",
        "dialog.about_desc": "Einfache PyGui-Oberfläche für sproject-JSON-Dateien.",
        "dialog.about_examples": "Beispiele: examples",
        "dialog.about_close": "Schließen",
        "dialog.open_title": "Projekt öffnen",

        # ── Status ────────────────────────────────────────────────────────
        "status.ready": "Bereit – Datei öffnen oder links ein Beispiel wählen.",
        "status.no_project": "Kein Projekt geladen.",
        "status.loaded": "Projekt geladen: {name}",
        "status.saved": "Gespeichert: {path}",
        "status.calc_done": "Berechnung abgeschlossen – Dauer: {duration}",
        "status.load_error": "Fehler beim Laden: {error}",
        "status.calc_error": "Fehler bei der Berechnung: {error}",
        "status.export_error": "Export-Fehler: {errors}",
        "status.exported": "Exportiert: {formats}  →  {path}",
        "status.no_formats": "Keine Formate ausgewählt.",
        "status.dir_not_found": "Verzeichnis nicht gefunden: {path}",
        "status.export_failed": "Export fehlgeschlagen: {error}",
        "status.theme_changed": "Theme gewechselt: {theme}",
        "status.language_changed": "Sprache gewechselt: {lang}",

        # ── Tasks ─────────────────────────────────────────────────────────
        "task.new": "Neuer Task",
        "task.new_loop": "Neuer Loop-Task",
        "task.new_subtask": "Neuer Subtask",
        "task.no_resources": "Keine Ressourcen definiert.",
        "task.no_persons": "Keine Personen definiert.",
        "task.no_resting": "Keine Ruhezeitregeln definiert.",

        # ── Ergebnis ──────────────────────────────────────────────────────
        "result.duration": "Projektdauer: {duration}",
        "result.critical_path": "Kritischer Pfad: {path}",
        "result.col.id": "#",
        "result.col.name": "Name",
        "result.col.faz": "FAZ",
        "result.col.fez": "FEZ",
        "result.col.saz": "SAZ",
        "result.col.sez": "SEZ",
        "result.col.buffer": "Puffer",
        "result.col.critical": "Krit.",

        # ── Export (Textdatei) ────────────────────────────────────────────
        "export.project": "Projekt:",
        "export.duration": "Projektdauer:",
        "export.critical_path": "Kritischer Pfad:",

        # ── Sidebar ──────────────────────────────────────────────────────
        "sidebar.wizard": "WIZARD",
        "sidebar.examples": "Beispiele:",
    },

    "en": {
        # ── Menus ─────────────────────────────────────────────────────────
        "menu.file": "File",
        "menu.settings": "Settings",
        "menu.help": "Help",
        "menu.file.open": "Open …",
        "menu.file.save": "Save",
        "menu.file.save_as": "Save as …",
        "menu.file.export": "Export …",
        "menu.file.close": "Close",
        "menu.settings.theme": "Theme",
        "menu.settings.language": "Language",
        "menu.help.about": "About …",

        # ── Theme names ───────────────────────────────────────────────────
        "theme.default": "Default",
        "theme.dark": "Dark",
        "theme.light": "Light",
        "theme.solarized_dark": "Solarized Dark",
        "theme.solarized_light": "Solarized Light",

        # ── Sections ──────────────────────────────────────────────────────
        "section.stammdaten": "1. Project Master Data",
        "section.tasks": "2. Tasks",
        "section.resources": "3. Resources",
        "section.persons": "4. Persons",
        "section.resting_times": "5. Rest Periods",
        "section.result": "CPM Result",

        # ── Labels (Master Data) ──────────────────────────────────────────
        "label.project_name": "Project name:",
        "label.start_date": "Start date:",
        "label.unit": "Time unit:",
        "label.total_hours": "Total hours:",
        "label.total_volume": "Total volume:",
        "label.order_volume": "Order volume:",

        # ── Toolbar tooltips ──────────────────────────────────────────────
        "tooltip.open": "Open  (Ctrl+O)",
        "tooltip.save": "Save  (Ctrl+S)",
        "tooltip.save_as": "Save as …  (Ctrl+Shift+S)",
        "tooltip.export": "Export …",
        "tooltip.calculate": "Calculate & Show",

        # ── Dialogs ──────────────────────────────────────────────────────
        "dialog.save_title": "Save as …",
        "dialog.save_btn": "Save",
        "dialog.cancel": "Cancel",
        "dialog.export_title": "Export",
        "dialog.export_btn": "Export",
        "dialog.export_formats": "Select formats:",
        "dialog.export_target": "Target folder:",
        "dialog.export_warn": "  ⚠ Markdown / Excel / TXT require a calculation (▶).",
        "dialog.about_title": "About sproject Editor",
        "dialog.about_desc": "Simple PyGui interface for sproject JSON files.",
        "dialog.about_examples": "Examples: examples",
        "dialog.about_close": "Close",
        "dialog.open_title": "Open project",

        # ── Status ────────────────────────────────────────────────────────
        "status.ready": "Ready – open a file or choose an example on the left.",
        "status.no_project": "No project loaded.",
        "status.loaded": "Project loaded: {name}",
        "status.saved": "Saved: {path}",
        "status.calc_done": "Calculation complete – duration: {duration}",
        "status.load_error": "Error loading: {error}",
        "status.calc_error": "Calculation error: {error}",
        "status.export_error": "Export error: {errors}",
        "status.exported": "Exported: {formats}  →  {path}",
        "status.no_formats": "No formats selected.",
        "status.dir_not_found": "Directory not found: {path}",
        "status.export_failed": "Export failed: {error}",
        "status.theme_changed": "Theme changed: {theme}",
        "status.language_changed": "Language changed: {lang}",

        # ── Tasks ─────────────────────────────────────────────────────────
        "task.new": "New Task",
        "task.new_loop": "New Loop Task",
        "task.new_subtask": "New Subtask",
        "task.no_resources": "No resources defined.",
        "task.no_persons": "No persons defined.",
        "task.no_resting": "No rest time rules defined.",

        # ── Result ────────────────────────────────────────────────────────
        "result.duration": "Project duration: {duration}",
        "result.critical_path": "Critical path: {path}",
        "result.col.id": "#",
        "result.col.name": "Name",
        "result.col.faz": "EST",
        "result.col.fez": "EFT",
        "result.col.saz": "LST",
        "result.col.sez": "LFT",
        "result.col.buffer": "Slack",
        "result.col.critical": "Crit.",

        # ── Export (text file) ────────────────────────────────────────────
        "export.project": "Project:",
        "export.duration": "Project duration:",
        "export.critical_path": "Critical path:",

        # ── Sidebar ──────────────────────────────────────────────────────
        "sidebar.wizard": "WIZARD",
        "sidebar.examples": "Examples:",
    },
}

_current_language: str = "de"


def set_language(lang: str) -> None:
    """Setzt die aktive Sprache (z.B. 'de' oder 'en')."""
    global _current_language
    if lang in _TRANSLATIONS:
        _current_language = lang


def get_language() -> str:
    """Gibt den aktiven Sprachcode zurueck."""
    return _current_language


def t(key: str, **kwargs: object) -> str:
    """Uebersetzt einen Schluessel in die aktive Sprache.

    Unbekannte Schluessel werden unveraendert zurueckgegeben.
    Keyword-Argumente werden per str.format() eingesetzt.
    """
    text = _TRANSLATIONS.get(_current_language, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
