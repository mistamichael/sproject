# Beispielergebnisse

Fertig berechnete Ergebnisse der Beispielprojekte aus [`examples/`](../../examples) – zum Anschauen,
ohne sproject zu installieren. Am schnellsten: die `.md`-Berichte anklicken und die Diagramm-Bilder in
[doc/de/termine-und-ist.md](../de/termine-und-ist.md) ansehen – beides ohne Download.

> English: pre-computed results of the example projects, to look at without installing sproject.
> Markdown files render directly on GitHub/Gitea; clicking an HTML file there shows only its source –
> download HTML and XLSX files and open them locally.

## So schaut man sie an

| Format | Ansehen |
| --- | --- |
| `.md` | direkt im Browser auf GitHub/Gitea – inklusive Gantt- und Netzplan-Diagrammen (Mermaid) |
| `.html` | Ein Klick auf GitHub/Gitea zeigt nur den Quelltext – Datei herunterladen (*Download raw file*) und im Browser öffnen |
| `*_charts.html`, `*_scenarios.html`, `*_simulation.html` | wie `.html`; interaktiv (Zoomen, Tooltips). Laden die Plotly-Bibliothek aus dem Internet |
| `.xlsx` | herunterladen und mit Excel/LibreOffice öffnen |
| `.txt`, `*_network_plan.json` | direkt im Browser |

## Software-Entwicklungsprojekt (`examples/software_simple.json`)

Acht Aufgaben, Personen mit Urlaub und Teilzeit, Ressourcenplanung, Kosten, Unsicherheiten und Szenarien.

| Datei | Inhalt |
| --- | --- |
| [software_simple.md](software_simple.md) | Bericht mit Gantt-Diagramm, Netzplan, kritischem Pfad, Ressourcen und Kosten |
| [software_simple.html](software_simple.html) | derselbe Bericht als HTML |
| [software_simple_charts.html](software_simple_charts.html) | interaktives Gantt-Diagramm und Ressourcenauslastung |
| [software_simple_scenarios.html](software_simple_scenarios.html) | Szenario-Vergleich (Was wäre wenn?) |
| [software_simple_simulation.html](software_simple_simulation.html) | Monte-Carlo-Simulation (300 Läufe): Histogramm, Summenkurve, P50/P80/P90, Kritikalität |
| [software_simple.xlsx](software_simple.xlsx) | Excel-Bericht mit mehreren Tabellenblättern |
| [software_simple.txt](software_simple.txt) | Textbericht |
| [software_simple_network_plan.json](software_simple_network_plan.json) | Rechenergebnis als JSON (FAZ/FEZ/SAZ/SEZ, Puffer, Termine) |

## Maschinenmontage (`examples/simpleproject.json`)

Einfaches Projekt in Arbeitstagen.

| Datei | Inhalt |
| --- | --- |
| [simpleproject.md](simpleproject.md) | Bericht mit Diagrammen |
| [simpleproject.html](simpleproject.html) | Bericht als HTML |
| [simpleproject_charts.html](simpleproject_charts.html) | interaktives Gantt-Diagramm |
| [simpleproject.xlsx](simpleproject.xlsx) | Excel-Bericht |
| [simpleproject.txt](simpleproject.txt) | Textbericht |
| [simpleproject_network_plan.json](simpleproject_network_plan.json) | Rechenergebnis als JSON |

## Pizza backen (`examples/pizza.json`)

Kleines Projekt in Minuten.

| Datei | Inhalt |
| --- | --- |
| [pizza.md](pizza.md) | Bericht mit Diagrammen |
| [pizza.html](pizza.html) | Bericht als HTML |
| [pizza_charts.html](pizza_charts.html) | interaktives Gantt-Diagramm |
| [pizza.xlsx](pizza.xlsx) | Excel-Bericht |
| [pizza.txt](pizza.txt) | Textbericht |
| [pizza_network_plan.json](pizza_network_plan.json) | Rechenergebnis als JSON |

## Neu erzeugen

Nach Änderungen an Rechenweg oder Berichten (im Projektordner, `.venv` aktiv):

```bash
python lib/sproject.py --project examples/software_simple.json --export json,txt,md,html,xlsx,plotly,scenarios,simulation --seed 1 --plotly-cdn --output-dir doc/result_examples
python lib/sproject.py --project examples/simpleproject.json --export json,txt,md,html,xlsx,plotly --plotly-cdn --output-dir doc/result_examples
python lib/sproject.py --project examples/pizza.json --export json,txt,md,html,xlsx,plotly --plotly-cdn --output-dir doc/result_examples
```

`--seed 1` macht die Simulation reproduzierbar; `--plotly-cdn` hält die interaktiven Seiten klein
(plotly.js wird aus dem Internet geladen statt eingebettet).
