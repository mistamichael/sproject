# Entwicklung

> Teil der [sproject-Dokumentation](../../README.de.md#dokumentation). English: [doc/en/development.md](../en/development.md)

sproject ist der Desktop-Editor. Die gesamte Berechnung (CPM, Ressourcenplanung, Szenarien, Monte-Carlo, Exporte)
und die KI-Schnittstelle (MCP-Server) liegen im eigenen Paket
[moncapro](https://github.com/mistamichael/moncapro) – `pip install moncapro`. Änderungen an Modell,
Berechnung, Exporten oder MCP-Werkzeugen gehören dorthin.

## Tests

```bash
python -m pytest                                              # GUI-Tests ohne Fenster
python -m pytest tests/test_gui_headless.py -k server_link    # GUI ↔ Server ↔ zweiter Client (Claude)
```

oder unter Windows `bin\run_unittests.bat`. Die Tests des Rechenkerns (einschließlich Golden-File-Vergleich
aller Beispiele) laufen im moncapro-Repository.

## Entwicklung

### Code-Qualität prüfen

```bash
make lint           # Alle Tools
make lint-dead      # Nur Dead Code (vulture + skylos)
make lint-types     # Nur Type Checks (pyright + mypy)
```

### Gemeinsam an moncapro und sproject arbeiten

```bash
pip install -e ../moncapro[all]     # lokalen Checkout statt der Git-/PyPI-Version verwenden
```

### Modelle und Exporte erweitern

Task-Modelle, Ressourcen, CPM, Gantt und die Export-Module liegen in `src/moncapro/` im
[moncapro-Repository](https://github.com/mistamichael/moncapro). Die Beispielprojekte gehören zu diesem Paket
(`moncapro.paths.get_examples_dir()`); die Seitenleiste der GUI listet sie auf.

## Projektstruktur

```text
sproject/
├── bin/                        # Start-Skripte, je als .bat (Windows) und .sh (Linux/macOS)
│   ├── install_py.bat          # Installation: .venv anlegen und pip install (Doppelklick)
│   ├── setenv.bat              # Umgebungsvariablen setzen (PV_*, MONCAPRO_*)
│   ├── activate_venv.bat       # Virtuelle Umgebung aktivieren
│   ├── create_reports.bat      # Berichte erzeugen (ruft `python -m moncapro` auf)
│   ├── gui.bat                 # GUI-Editor starten
│   ├── mcp_server.bat          # moncapro-Server (KI-Schnittstelle) starten: --port [N] | --claude
│   └── run_unittests.bat       # Unit-Tests ausführen
├── cfg/                        # GUI-Konfiguration
│   ├── gui.cfg                 # Farben, Größen, Server-Vorgaben
│   └── themes/                 # Theme-Dateien
├── gui/                        # GUI-Editor (Dear PyGui)
│   ├── app.py                  # Layout, Menüs, Toolbar, Dialoge
│   ├── editor.py               # Editor-Zustand, Dateioperationen, Berechnung, Exporte
│   ├── task_rows.py            # Verlustfreie Umwandlung Tasks ↔ Tabellenzeilen
│   ├── analysis_rows.py        # Text ↔ Modell für Unsicherheiten und Szenarien
│   ├── server_link.py          # Verbindung der GUI zum moncapro-Server (Menü Server)
│   └── components/             # Sektionen, Tabellen, Ergebnis-Panel, Seitenleiste
├── tests/                      # pytest: GUI-Tests ohne Fenster
├── data/                       # Eigene Projektdateien (Beispiel: simple_software_project.xlsx)
├── doc/                        # GUI-Dokumentation, Bilder, fertig berechnete Beispielergebnisse
├── .mcp.json                   # Meldet den MCP-Server bei Claude Code an
├── requirements.txt            # moncapro[all], dearpygui, pytest
├── log/                        # Logdateien (wird angelegt)
├── results/                    # Erzeugte Berichte (wird angelegt)
└── README.md
```

`PV_CFG` zeigt auf dieses `cfg/` (nur GUI). Die Berechnung nutzt die mit moncapro gelieferte Konfiguration
(Arbeitszeiten, Kalender, Export-Layout); zum Ändern `MONCAPRO_CFG` auf eine eigene Kopie setzen.
