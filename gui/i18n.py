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
        "menu.file.new": "Neu",
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
        "section.resting_times": "5. Ruhezeiten und Urlaub",
        "section.result": "CPM-Ergebnis",

        # ── Labels (Stammdaten) ───────────────────────────────────────────
        "label.project_name": "Projektname:",
        "label.start_date": "Startdatum:",
        "label.unit": "Mengeneinheit:",
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
        "dialog.export_warn": "  ⚠ Reports (außer JSON-Projektdatei) benötigen eine Berechnung (▶).",
        "dialog.about_title": "Über sproject Editor",
        "dialog.about_desc": "Einfache PyGui-Oberfläche für sproject-JSON-Dateien.",
        "dialog.about_examples": "Beispiele: examples",
        "dialog.about_close": "Schließen",
        "dialog.open_title": "Projekt öffnen",

        # ── Status ────────────────────────────────────────────────────────
        "status.new_project": "Neues Projekt erstellt: {name}",
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
        "result.col.duration": "Dauer",
        "result.col.resources": "Ressourcen",
        "result.tab.input": "Eingabe",
        "result.tab.result": "Ergebnis",
        "result.header.critical_path": "Kritischer Pfad",
        "result.header.all_tasks": "Alle Aufgaben",
        "result.header.resources_costs": "Ressourcen & Kosten",
        "result.header.gantt": "Gantt-Diagramm",
        "result.header.resource_chart": "Ressourcenauslastung",
        "result.cost.person_costs": "Personalkosten",
        "result.cost.machine_costs": "Maschinenkosten (Lohn)",
        "result.cost.provisioning_costs": "Bereitstellungskosten",
        "result.cost.total_costs": "GESAMTKOSTEN",
        "result.cost.col.resource": "Ressource",
        "result.cost.col.type": "Typ",
        "result.cost.col.hours": "Stunden",
        "result.cost.col.rate": "Stundensatz",
        "result.cost.col.provisioning": "Bereitstellung",
        "result.cost.col.labor": "Lohnkosten",
        "result.cost.col.total": "Gesamt",

        # ── Export (Textdatei) ────────────────────────────────────────────
        "export.project": "Projekt:",
        "export.duration": "Projektdauer:",
        "export.critical_path": "Kritischer Pfad:",

        # ── Sidebar ──────────────────────────────────────────────────────
        "sidebar.wizard": "WIZARD",
        "sidebar.examples": "Beispiele:",

        # ── Bearbeitbare Listen (Ressourcen, Personen, Ruhezeiten) ─────────
        "tt.add_task": "+ Aufgabe",
        "tt.add_loop": "+ Loop-Task",
        "tt.hint": "Nachfolger und Ressourcen über + / - Buttons bearbeiten",
        "tt.empty": "Keine Aufgaben – bitte eine Projektdatei laden.",
        "tt.col.duration": "Dauer",
        "tt.col.successors": "Nachfolger",
        "tt.col.resources": "Ressourcen",
        "tt.col.cost": "Kosten",
        "tt.col.actions": "Aktionen",
        "tt.add_successor": "Nachfolger hinzufügen",
        "tt.remove_successor": "Nachfolger entfernen",
        "tt.add_resource": "Ressource hinzufügen",
        "tt.remove_resource": "Ressource entfernen",
        "tt.pick_add": "Zum Hinzufügen auswählen:",
        "tt.pick_remove": "Zu entfernende Einträge auswählen:",
        "tt.remove": "Entfernen",
        "tt.no_other_tasks": "Keine anderen Tasks vorhanden.",
        "tt.no_successors": "Keine Nachfolger vorhanden.",
        "tt.all_assigned": "Alle Ressourcen bereits zugewiesen.",
        "list.no_vacation": "Kein Urlaub definiert.",
        "list.no_workinghours": "Keine Teilzeitregelungen definiert.",
        "col.id": "ID",
        "col.name": "Name",
        "col.type": "Typ",
        "col.color": "Farbe",
        "col.role": "Rolle",
        "col.rate": "EUR/h",
        "col.info": "Info",
        "col.after_hours": "Nach (h)",
        "col.pause": "Pause",
        "col.note": "Hinweis",
        "col.person_id": "Personen-ID",
        "col.date": "Datum",
        "col.description": "Beschreibung",
        "col.days": "Tage",
        "col.hours": "Zeiten",
        "info.vacation": "Urlaub: {count}",
        "info.part_time": "Teilzeit",
        "button.add": "Hinzufügen",
        "button.cancel": "Abbrechen",
        "button.add_resource": "+ Ressource",
        "button.add_person": "+ Person",
        "button.add_resting_time": "+ Ruhezeit",
        "button.add_vacation": "+ Urlaub",
        "button.add_workinghours": "+ Teilzeit",
        "dlg.add_resource": "Ressource hinzufügen",
        "dlg.add_person": "Person hinzufügen",
        "dlg.add_resting_time": "Ruhezeit hinzufügen",
        "dlg.add_vacation": "Urlaub hinzufügen",
        "dlg.add_workinghours": "Teilzeit hinzufügen",
        "hint.resource_name": "Ressourcenname",
        "hint.color": "Hex ohne #",
        "hint.vacation_date": "YYYY-MM-DD oder YYYY-MM-DD – YYYY-MM-DD",
        "hint.vacation_desc": "z.B. Urlaub, Fortbildung",
        "default.vacation": "Urlaub",
        "default.part_time": "Teilzeit",
        "default.person_name": "Max Mustermann",
        "default.person_role": "Arbeiter",
        "default.project_name": "Neues Projekt",
        "error.duplicate_id": "ID '{id}' existiert bereits!",
        "error.no_result": "Kein Berechnungsergebnis. Bitte erst berechnen.",
    },

    "en": {
        # ── Menus ─────────────────────────────────────────────────────────
        "menu.file": "File",
        "menu.settings": "Settings",
        "menu.help": "Help",
        "menu.file.new": "New",
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
        "section.resting_times": "5. Rest Periods & Vacation",
        "section.result": "CPM Result",

        # ── Labels (Master Data) ──────────────────────────────────────────
        "label.project_name": "Project name:",
        "label.start_date": "Start date:",
        "label.unit": "Volume unit:",
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
        "dialog.export_warn": "  ⚠ Reports (except the JSON project file) require a calculation (▶).",
        "dialog.about_title": "About sproject Editor",
        "dialog.about_desc": "Simple PyGui interface for sproject JSON files.",
        "dialog.about_examples": "Examples: examples",
        "dialog.about_close": "Close",
        "dialog.open_title": "Open project",

        # ── Status ────────────────────────────────────────────────────────
        "status.new_project": "New project created: {name}",
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
        "result.col.duration": "Duration",
        "result.col.resources": "Resources",
        "result.tab.input": "Input",
        "result.tab.result": "Result",
        "result.header.critical_path": "Critical Path",
        "result.header.all_tasks": "All Tasks",
        "result.header.resources_costs": "Resources & Costs",
        "result.header.gantt": "Gantt Chart",
        "result.header.resource_chart": "Resource Utilization",
        "result.cost.person_costs": "Personnel Costs",
        "result.cost.machine_costs": "Machine Costs (Labor)",
        "result.cost.provisioning_costs": "Provisioning Costs",
        "result.cost.total_costs": "TOTAL COSTS",
        "result.cost.col.resource": "Resource",
        "result.cost.col.type": "Type",
        "result.cost.col.hours": "Hours",
        "result.cost.col.rate": "Hourly Rate",
        "result.cost.col.provisioning": "Provisioning",
        "result.cost.col.labor": "Labor Costs",
        "result.cost.col.total": "Total",

        # ── Export (text file) ────────────────────────────────────────────
        "export.project": "Project:",
        "export.duration": "Project duration:",
        "export.critical_path": "Critical path:",

        # ── Sidebar ──────────────────────────────────────────────────────
        "sidebar.wizard": "WIZARD",
        "sidebar.examples": "Examples:",

        # ── Editable lists (resources, persons, rest times) ──────────────
        "tt.add_task": "+ Task",
        "tt.add_loop": "+ Loop task",
        "tt.hint": "Edit successors and resources with the + / - buttons",
        "tt.empty": "No tasks – please load a project file.",
        "tt.col.duration": "Duration",
        "tt.col.successors": "Successors",
        "tt.col.resources": "Resources",
        "tt.col.cost": "Cost",
        "tt.col.actions": "Actions",
        "tt.add_successor": "Add successor",
        "tt.remove_successor": "Remove successor",
        "tt.add_resource": "Add resource",
        "tt.remove_resource": "Remove resource",
        "tt.pick_add": "Select entries to add:",
        "tt.pick_remove": "Select entries to remove:",
        "tt.remove": "Remove",
        "tt.no_other_tasks": "No other tasks available.",
        "tt.no_successors": "No successors defined.",
        "tt.all_assigned": "All resources already assigned.",
        "list.no_vacation": "No vacation defined.",
        "list.no_workinghours": "No part-time rules defined.",
        "col.id": "ID",
        "col.name": "Name",
        "col.type": "Type",
        "col.color": "Color",
        "col.role": "Role",
        "col.rate": "EUR/h",
        "col.info": "Info",
        "col.after_hours": "After (h)",
        "col.pause": "Break",
        "col.note": "Note",
        "col.person_id": "Person ID",
        "col.date": "Date",
        "col.description": "Description",
        "col.days": "Days",
        "col.hours": "Hours",
        "info.vacation": "Vacation: {count}",
        "info.part_time": "Part-time",
        "button.add": "Add",
        "button.cancel": "Cancel",
        "button.add_resource": "+ Resource",
        "button.add_person": "+ Person",
        "button.add_resting_time": "+ Rest rule",
        "button.add_vacation": "+ Vacation",
        "button.add_workinghours": "+ Part-time",
        "dlg.add_resource": "Add resource",
        "dlg.add_person": "Add person",
        "dlg.add_resting_time": "Add rest rule",
        "dlg.add_vacation": "Add vacation",
        "dlg.add_workinghours": "Add part-time rule",
        "hint.resource_name": "Resource name",
        "hint.color": "Hex without #",
        "hint.vacation_date": "YYYY-MM-DD or YYYY-MM-DD – YYYY-MM-DD",
        "hint.vacation_desc": "e.g. vacation, training",
        "default.vacation": "Vacation",
        "default.part_time": "Part-time",
        "default.person_name": "John Doe",
        "default.person_role": "Worker",
        "default.project_name": "New project",
        "error.duplicate_id": "ID '{id}' already exists!",
        "error.no_result": "No calculation result. Please calculate first.",
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
