# KI-Schnittstelle (MCP)

Mit der KI-Schnittstelle kann ein KI-Werkzeug wie Claude Code oder Claude Desktop Projekte
anlegen, aus Excel-Listen oder anderen Quellen aufbauen, prüfen, berechnen und speichern –
ohne GUI oder live in der laufenden GUI.

## Aufbau

```text
Claude Code / Claude Desktop / eigener Chatbot
        │  MCP (Model Context Protocol)
        ▼
mcp_server/server.py   Werkzeuge (Tools) und Ressourcen
        ▼
lib/api.py             ProjectSession: Operationen auf einem Projekt (ohne GUI, testbar)
        ▼
lib/models, lib/schedule.build_schedule, lib/exporters, lib/scenarios, lib/simulation
```

Quelldaten (Excel, PDF, Text) liest die KI selbst und überträgt sie mit den Werkzeugen ins Projekt.
Jede Änderung wird sofort validiert; ungültige Eingaben ändern nichts und liefern eine Fehlermeldung.

## Betriebsarten

| Betriebsart             | Start                                              | Verbindung                    |
|-------------------------|----------------------------------------------------|-------------------------------|
| ohne GUI (stdio)        | automatisch durch Claude Code über `.mcp.json`     | stdio                         |
| ohne GUI (HTTP)         | `bin\mcp_server.bat --http --port 8765`            | `http://127.0.0.1:8765/mcp`   |
| live in der GUI (HTTP)  | GUI: *Einstellungen → KI-Schnittstelle (MCP) aktiv* | `http://127.0.0.1:8765/mcp`   |

### Ohne GUI mit Claude Code

Im Repo liegt `.mcp.json`; Claude Code bietet den Server `sproject` beim Start im Projektordner an
(einmalig bestätigen). Danach z. B.:

> Lies `data/bauplan.xlsx` und baue daraus ein sproject-Projekt. Speichere es als `bauplan.json`.

Linux/macOS: in `.mcp.json` statt `cmd /c bin\mcp_server.bat` den Befehl `bash bin/mcp_server.sh` eintragen.

### Live in der GUI

1. GUI starten, Projekt öffnen oder neu anlegen.
2. *Einstellungen → KI-Schnittstelle (MCP) aktiv* einschalten. Die Statuszeile zeigt die Adresse.
3. Claude Code mit der laufenden GUI verbinden (einmalig):

   ```bash
   claude mcp add --transport http sproject-gui http://127.0.0.1:8765/mcp
   ```

Änderungen der KI erscheinen sofort in den Tabellen; das Projekt gilt danach als ungespeichert.
Die KI sieht auch noch nicht gespeicherte Eingaben aus der GUI.

Einstellungen in `cfg/gui.cfg`:

```ini
[ai]
mcp_port      = 8765
mcp_autostart = false   ; true = beim GUI-Start aktivieren
```

Der Server lauscht nur auf `127.0.0.1` (lokaler Rechner).

## Werkzeuge

| Werkzeug                               | Zweck                                                        |
|----------------------------------------|--------------------------------------------------------------|
| `new_project`, `load_project`, `save_project` | Projekt anlegen, öffnen, speichern (relative Pfade → `work/`) |
| `get_overview`, `get_project`          | Kurzfassung bzw. vollständiges JSON                          |
| `replace_project`, `patch_project`     | ganzes Projekt / Felder auf oberster Ebene setzen (Massenaufbau) |
| `add_task`, `update_task`, `remove_task` | Tasks bearbeiten (ohne `id` wird die nächste Zahl vergeben) |
| `add_dependency`, `remove_dependency`  | Abhängigkeiten EA, AA, EE, AE                                 |
| `set_uncertainty`                      | `duration_range` und `risk` für die Simulation               |
| `upsert_item`, `remove_item`, `set_list` | Ressourcen, Personen, Ruhezeiten, Szenarien               |
| `validate`                             | unbekannte Verweise, Zyklen, Rechenfehler                     |
| `calculate`                            | Start, Ende, kritischer Pfad, Kosten, Deadline-Warnungen     |
| `compare_scenarios`, `simulate`        | Szenarienvergleich, Monte-Carlo                              |
| `export`                               | Reports (json, txt, md, html, xlsx, …) nach `results/`       |
| `list_examples`                        | Beispielprojekte als Vorlagen                                |

Ressourcen: `sproject://schema` (JSON-Schema des Formats), `sproject://examples/<name>`.

## Ohne MCP aus Python

```python
from lib.api import ProjectSession

s = ProjectSession()
s.new_project("Garage", project_start="2026-04-01")
s.add_task({"name": "Fundament", "duration": "3d"})
s.add_task({"name": "Mauern", "duration": "5d"})
s.add_dependency(1, 2)
print(s.calculate()["end"])
s.save("work/garage.json")
```

## Test

```bash
python -m pytest tests/test_api.py
python -m pytest tests/test_gui_headless.py -k ai_bridge
npx @modelcontextprotocol/inspector python -m mcp_server   # Werkzeuge interaktiv ausprobieren
```
