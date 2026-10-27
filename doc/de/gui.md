# Grafischer Editor (GUI)

> Teil der [sproject-Dokumentation](../../README.de.md#dokumentation). English: [doc/en/gui.md](../en/gui.md)

![sproject-Editor: Gantt-Diagramm und Ressourcenauslastung](img/gui_editor_de.png)

Start mit `bin/gui.bat` (Windows) oder `bash bin/gui.sh` (Linux/Mac). Ein Beispiel öffnet man über die Sidebar, eine eigene Datei über *Datei → Öffnen*.

| Sektion | Inhalt |
| ------- | ------ |
| 1. Projekt-Stammdaten | Name, Startdatum, Einheit, Volumen, Stichtag |
| 2. Aufgaben | Einfache, Loop- und Subtasks mit Dauer, Ressourcen, Nachfolgern, Kosten |
| 3. Ressourcen | ID, Name, Typ, Farbe – Farbfeld mit Farbwähler (Klick aufs Farbfeld oder Doppelklick auf den Hex-Wert) |
| 4. Personen | Name, Rolle, Stundensatz |
| 5. Ruhezeiten und Urlaub | Ruhezeitregeln, Urlaub, Teilzeit |
| 6. Unsicherheiten | Je Task Min/Max-Dauer und Risiko (Wahrscheinlichkeit, Verzögerung, Hinweis) für die Monte-Carlo-Simulation |
| 7. Szenarien | Was-wäre-wenn-Varianten mit Wahrscheinlichkeit und ihre Änderungen (Task, Ressource, Person) |

Die Sektionen 3–7 sind optional und lassen sich in der Sidebar einschalten; sie erscheinen automatisch, wenn das geladene Projekt sie nutzt.

- **Bearbeiten:** direkt in den Tabellen tippen oder in den Sektionen 6 und 7 per Doppelklick auf eine Zeile das Formular öffnen.
- **Warnung:** Liegt die geplante Dauer eines Tasks außerhalb von Min–Max, markiert Sektion 6 sie rot (die Simulation würde mit dem Rand des Bereichs rechnen).
- **Menü Analyse / Toolbar:** berechnen, Szenarien vergleichen, Monte-Carlo-Simulation starten. Ergebnisse erscheinen im Tab *Ergebnis*, Reports landen in `results/`.
- **Sprache:** Deutsch / Englisch über *Einstellungen*.
- **KI-Schnittstelle:** *Server → Mit moncapro-Server verbinden …* teilt das Projekt mit Claude (siehe unten).
