# KI-Schnittstelle (MCP)

Mit der KI-Schnittstelle kann ein KI-Werkzeug wie Claude Code oder Claude Desktop Projekte
anlegen, aus Excel-Listen oder anderen Quellen aufbauen, prüfen, berechnen und speichern –
allein oder gemeinsam mit der GUI. Python-Skripte nutzen dieselben Operationen direkt.

> English version: [doc/en/ai-interface.md](../en/ai-interface.md)

## Grundidee: genau ein sproject-Server

```text
Claude Code / Claude Desktop          GUI (bin\gui.bat)
        │  MCP über HTTP                      │  Server → Mit sproject-Server verbinden …
        └──────────────┬──────────────────────┘
                       ▼
        sproject-Server  (bin\mcp_server.bat, http://127.0.0.1:8765/mcp)
        mcp_server/server.py → lib/api.py ProjectSession → hält DAS Projekt
                       ▼
        lib/models, build_schedule, exporters, scenarios, simulation
```

- Es läuft **ein** Server, und er hält **ein** Projekt. Claude und die GUI sind beide nur Clients
  und sehen immer denselben Stand – es gibt keine zweite, heimliche Kopie.
- Ein zweiter Server auf demselben Port startet nicht („Port 8765 ist belegt – läuft schon ein sproject-Server?“).
- Die GUI verbindet sich nur **ausdrücklich** (Menü *Server*). Ohne Verbindung arbeitet sie wie bisher lokal.
- Quelldaten (Excel, PDF, Text) liest die KI selbst und überträgt sie mit den Werkzeugen ins Projekt.
- Jede Änderung wird sofort validiert. Ungültige Eingaben ändern nichts und liefern eine Fehlermeldung.
- Gerechnet wird über `build_schedule()` – dieselben Ergebnisse wie CLI und GUI.

## Einrichtung

### 1. Server starten

```text
bin\mcp_server.bat                  HTTP auf http://127.0.0.1:8765/mcp (Standard)
bin\mcp_server.bat --port [N]       HTTP auf Port N (ohne N: 8765)
bin\mcp_server.bat --project DATEI  Projekt beim Start öffnen
bin\mcp_server.bat --claude         stdio – nur für Skripte/Tests (siehe unten)
bin\mcp_server.bat --help           Hilfe
```

Unter Linux/macOS gilt dasselbe mit `bin/mcp_server.sh`. Das Fenster zeigt die Adresse; beendet wird mit
Strg+C. Alternativ startet die GUI den Server auf Nachfrage selbst (siehe 3.).

### 2. Claude Code verbinden

Im Repo liegt `.mcp.json` – Claude Code verbindet sich damit per HTTP mit dem laufenden Server:

```json
{"mcpServers": {"sproject": {"type": "http", "url": "http://127.0.0.1:8765/mcp"}}}
```

Claude Code im Projektordner starten, den Server `sproject` einmal freigeben; `/mcp` zeigt den Status.
Läuft der Server noch nicht, meldet Claude Code die Verbindung als fehlgeschlagen – Server starten,
dann in `/mcp` neu verbinden. Für einen anderen Port die URL in `.mcp.json` anpassen.

### 3. GUI verbinden (optional)

1. GUI starten (`bin\gui.bat`), ggf. ein Projekt öffnen.
2. *Server → Mit sproject-Server verbinden …*, Host und Port bestätigen (Vorgabe aus `cfg/gui.cfg`).
3. Läuft dort kein Server, fragt die GUI „Jetzt starten?“. *Ja* startet `bin\mcp_server.bat --port N`
   in einem eigenen Fenster; die GUI verbindet sich, sobald er bereit ist. Der Server läuft auch nach dem
   Schließen der GUI weiter.

Beim Verbinden gilt:

| Server-Stand | Was passiert |
| --- | --- |
| Server hat noch kein Projekt | das Projekt der GUI wird auf den Server übertragen |
| Server hat ein Projekt | die GUI übernimmt es; hat die GUI ungespeicherte Änderungen, fragt sie vorher |
| unter der Adresse läuft etwas anderes | „Unter … läuft kein sproject-Server“, keine Verbindung |

Solange die GUI verbunden ist:

- Titelleiste und Statuszeile zeigen „verbunden mit `http://127.0.0.1:8765/mcp`“.
- Änderungen in der GUI gehen etwa jede Sekunde an den Server – aber nicht, solange ein Eingabefeld aktiv
  ist (beim Tippen wird nichts überschrieben).
- Änderungen von Claude erscheinen ebenso schnell in den Tabellen; optionale Sektionen werden eingeblendet.
- **Konflikt** (GUI und Claude ändern gleichzeitig): Der Server-Stand gewinnt, die Statuszeile meldet
  „Konflikt …“. Die GUI-Änderung muss dann neu eingegeben werden.
- Lehnt der Server einen GUI-Stand ab (z. B. ungültige Dauer), steht der Grund in der Statuszeile;
  die GUI bleibt verbunden.
- *Speichern* in der GUI schreibt die Datei lokal wie bisher. Speichert Claude (`save_project`), schreibt
  der Server die Datei.
- *Server → Verbindung trennen* trennt nur die GUI; der Server läuft weiter.

Einstellungen in `cfg/gui.cfg` (Vorgabe für den Verbinden-Dialog):

```ini
[server]
host = 127.0.0.1
port = 8765
```

Der Server lauscht nur auf `127.0.0.1` und ist damit nur vom eigenen Rechner aus erreichbar.

### stdio-Modus (Sonderfall)

`bin\mcp_server.bat --claude` startet einen Server über stdio, z. B. für einen MCP-Client, der den
Server selbst startet, oder für Tests. Ein solcher Server ist **privat** für diesen einen Client –
die GUI kann sich nicht mit ihm verbinden. Für die Zusammenarbeit mit der GUI immer den HTTP-Server nutzen.

## Beispiele für Anfragen an Claude

- „Lies `data/bauplan.xlsx` (Spalten: Nr, Vorgang, Dauer in Tagen, Vorgänger) und baue daraus ein
  sproject-Projekt mit Start am 4. Mai 2026. Prüfe es, berechne es und speichere es als `bauplan.json`.“
- „Lege für das offene Projekt die Personen Anna (Maurerin, 55 €/h) und Ben (Zimmerer, 60 €/h) an,
  weise sie den passenden Aufgaben zu und sag mir, wie sich Ende und Kosten ändern.“
- „Füge ein Szenario ‚Lieferverzug Fenster' hinzu, in dem Task 7 zehn Tage später starten kann,
  und vergleiche es mit dem Basisplan.“
- „Schätze für alle Aufgaben eine Min/Max-Dauer und simuliere: Bis wann sind wir zu 80 % fertig?“

## Typischer Ablauf der KI

```text
new_project / load_project
  → add_task (je Aufgabe; Antwort enthält die vergebene id)
  → add_dependency (mit den ids aus add_task)
  → upsert_item (Personen, Ressourcen) → update_task (resources zuweisen)
  → validate → calculate → save_project
```

Für große Listen ist ein einziger Aufruf schneller: `patch_project({"tasks": [...]})` oder
`replace_project({...})` mit dem kompletten Projekt im JSON-Format (Schema: `sproject://schema`).

## Werkzeuge (MCP)

| Werkzeug | Zweck / Rückgabe |
| --- | --- |
| `new_project`, `load_project` | Projekt anlegen / öffnen → Kurzfassung |
| `save_project` | speichern (relative Pfade → `work/`) → Dateipfad |
| `get_overview`, `get_project` | Kurzfassung bzw. vollständiges JSON |
| `replace_project`, `patch_project` | ganzes Projekt / Felder auf oberster Ebene setzen (Massenaufbau); `replace_project` optional mit `base_revision` |
| `add_task` | Task anlegen → gespeicherter Task **inkl. `id`** (ohne `id` wird die nächste Zahl vergeben) |
| `get_task`, `update_task`, `remove_task` | Task lesen, ändern (`null` entfernt ein Feld), löschen |
| `add_dependency`, `remove_dependency` | Abhängigkeiten EA (Standard), AA, EE, AE |
| `set_uncertainty` | `duration_range` und `risk` für die Simulation |
| `upsert_item`, `remove_item`, `set_list` | Ressourcen, Personen, Ruhezeiten, Szenarien |
| `validate` | unbekannte Verweise, Zyklen, Rechenfehler → Liste (leer = in Ordnung) |
| `calculate` | Start, Ende, kritischer Pfad, Kosten, Deadline-Warnungen, Termine je Task |
| `compare_scenarios`, `simulate` | Szenarienvergleich, Monte-Carlo |
| `export` | Reports (json, txt, md, html, xlsx, …) nach `results/` |
| `list_examples` | Beispielprojekte als Vorlagen |
| `get_revision`, `get_state` | Änderungszähler bzw. Zähler + Projekt + Pfad (für Clients wie die GUI) |

MCP-Ressourcen: `sproject://schema` (JSON-Schema des Projektformats), `sproject://examples/<name>`.

## Ohne MCP aus Python

Für Skripte ohne Server – arbeitet auf einem eigenen Projekt im Speicher:

```python
from lib.api import ProjectSession, ApiError

s = ProjectSession()
s.new_project("Garage", project_start="2026-04-01")
fundament = s.add_task({"name": "Fundament", "duration": "3d"})   # → Task-ID (hier 1)
mauern = s.add_task({"name": "Mauern", "duration": "5d"})
dach = s.add_task({"name": "Dach", "duration": "2d"})
s.add_dependency(fundament, mauern)
s.add_dependency(mauern, dach)

s.upsert_item("persons", {"id": "P1", "name": "Anna", "role": "Maurerin", "hourly_rate": 55})
s.upsert_item("resources", {"id": "R1", "type": "person", "person_id": "P1"})
s.update_task(mauern, {"resources": ["R1"]})

assert s.validate() == []
result = s.calculate()
print(result["end"], result["total_costs"], [t["name"] for t in result["critical_path"]])
s.save("work/garage.json")
s.export(["xlsx", "html"])

try:
    s.add_dependency(dach, 99)
except ApiError as e:
    print(e)          # Task 99 nicht gefunden – das Projekt bleibt unverändert
```

| Methode | Rückgabe |
| --- | --- |
| `new_project(name, project_start, unit)` | Kurzfassung (dict) |
| `load(path)`, `replace_project(data, base_revision=None)`, `patch_project(fields)` | Kurzfassung (dict) |
| `save(path=None)` | Pfad als Text |
| `get_project()`, `overview()`, `list_tasks()`, `schema()` | Projekt-JSON, Kurzfassung, Task-Liste, JSON-Schema |
| `add_task(task)` | **Task-ID** |
| `get_task(id)`, `update_task(id, fields)`, `set_uncertainty(id, …)` | Task (dict, normalisiert, z. B. `"5"` → `"5d"`) |
| `remove_task(id)` | verbleibende Task-IDs |
| `add_dependency(vorgänger, nachfolger, dep_type="EA")`, `remove_dependency(…)` | Vorgänger-Task (dict) |
| `upsert_item(field, item)`, `remove_item(field, key)`, `set_list(field, items)` | Eintrag bzw. Anzahl |
| `validate()` | Liste von Problemen (leer = in Ordnung) |
| `calculate(start_date=None)` | dict: `start`, `end`, `duration_days`, `critical_path`, `total_costs`, `deadline_warnings`, `tracking`, `tasks` |
| `export(formats, out_dir=None)` | Liste der erzeugten Dateien |
| `compare_scenarios()`, `simulate(runs, seed)` | Tabelle bzw. dict mit `summary` und `top_critical` |
| `revision`, `state()` | Änderungszähler bzw. `{"revision", "project", "path"}` |

Fehler werden als `ApiError` (Unterklasse von `ValueError`) mit verständlicher Meldung ausgelöst.

## Fehlerbehebung

| Problem | Lösung |
| --- | --- |
| „Port 8765 ist belegt – läuft schon ein sproject-Server?“ | Es läuft bereits einer – diesen verwenden. Sonst anderen Port: `--port 8766` (dann auch `.mcp.json` und GUI-Dialog anpassen) |
| Claude Code: Server `sproject` fehlgeschlagen | Server läuft nicht → `bin\mcp_server.bat` starten, in `/mcp` neu verbinden |
| GUI: „Kein sproject-Server unter …“ | im Dialog *Ja* wählen (startet ihn) oder `bin\mcp_server.bat` von Hand starten |
| GUI: „sproject-Server ließ sich nicht starten“ | Meldung im Server-Fenster lesen; `.venv` vorhanden? (`bin\install_py.bat`) |
| GUI: „Konflikt …“ | GUI und Claude haben gleichzeitig geändert; der Server-Stand gilt, GUI-Eingabe wiederholen |
| GUI: „Server lehnt die Änderung ab …“ | Eingabe in der GUI ist ungültig (Grund steht dabei) – korrigieren |
| `.venv nicht gefunden` | `bin\install_py.bat` ausführen (installiert auch das Paket `mcp`) |
| eigene Erweiterung zerstört die stdio-Verbindung | im stdio-Modus nichts mit `print()` auf stdout schreiben – Ausgaben nach stderr oder ins Log |

## Test

```bash
python -m pytest tests/test_api.py                            # API, MCP-Werkzeuge, Revision/Konflikt, Port-Sperre
python -m pytest tests/test_gui_headless.py -k server_link    # GUI ↔ Server ↔ zweiter Client (Claude)
npx @modelcontextprotocol/inspector                           # Werkzeuge interaktiv: URL http://127.0.0.1:8765/mcp
```
