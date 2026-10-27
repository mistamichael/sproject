# sproject – Project Schedules with Probabilities

**When will the project really be done?** sproject plans projects with the critical path method (CPM), levels
resources, vacations and part-time work – and then answers with a **Monte Carlo simulation**: *"done by 16 April
with 80 % probability"* instead of a single, usually too optimistic date. What-if **scenarios** show the effect
of a sick colleague or a late delivery. A desktop GUI, a CLI and an **MCP server** let you – or Claude – build
plans, e.g. straight from an Excel task list.

[![tests](https://github.com/mistamichael/sproject/actions/workflows/tests.yml/badge.svg)](https://github.com/mistamichael/sproject/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

> Deutsche Dokumentation: [README.de.md](README.de.md)

![Monte Carlo simulation: distribution of the project end, P50/P80/P90](doc/img/simulation_en.svg)

![sproject editor: Gantt chart and resource utilization](doc/de/img/gui_editor_en.png)

## Why sproject

- **Probabilities instead of a single date** – duration ranges, risks and scenario probabilities feed a Monte Carlo
  simulation: P50/P80/P90, the chance to meet the plan or a deadline, and which tasks are most often critical.
- **What-if scenarios** – "backend takes 50 % longer", "Alice sick for a week", "truck broken" – compared with the
  base plan in duration, costs and missed deadlines.
- **Realistic resource planning** – one person or machine can only do one task at a time; vacations, part-time and
  rest breaks stretch the plan; fixed dates (`not_before`, `deadline`); plan vs. actual with a baseline.
- **AI interface (MCP)** – Claude Code or Claude Desktop builds, checks and calculates projects through one shared
  moncapro server, e.g. from an Excel task list; the GUI can watch live.
- **Desktop GUI, CLI and reports** – Markdown/HTML with Gantt and network diagrams, Excel, TXT, JSON and interactive
  charts.

Look at the results without installing anything: [example results](doc/result_examples/README.md).

## Quickstart

Requires Python 3.10 or higher.

sproject is the desktop editor. The calculation core, the command line and the MCP server come from the
separate package [moncapro](https://github.com/mistamichael/moncapro) and are installed automatically.

1. Get the code: `git clone https://github.com/mistamichael/sproject.git` (or download the ZIP)
2. Install: double-click `bin\install_py.bat` – Linux/macOS: `bash bin/install_py.sh`
   (creates `.venv` and installs everything from `requirements.txt`)
3. Start: double-click `bin\gui.bat` – Linux/macOS: `bash bin/gui.sh` – and open an example from the sidebar (English files in `examples/en`, German ones in `examples/de`)

Command line instead of the GUI (with `.venv` active):

```bash
moncapro --project my_project.json --export md,html --simulate 300
```

Building a project with Claude: see [Three ways to use sproject](#three-ways-to-use-sproject).

## Three ways to use sproject

| | |
| --- | --- |
| **Desktop GUI** | `bin\gui.bat` – edit tasks, resources, uncertainties and scenarios, calculate, export. [GUI guide](doc/en/gui.md) |
| **Command line** | `moncapro --project <file> --export md,html,xlsx --simulate 300` – batch reports. [CLI guide](https://github.com/mistamichael/moncapro/blob/main/doc/en/cli.md) |
| **AI / Claude (MCP)** | start `bin\mcp_server.bat`, then ask Claude Code e.g. *"Read `data/simple_software_project.xlsx` and build a sproject project from it"* – the GUI can watch live. [AI interface](https://github.com/mistamichael/moncapro/blob/main/doc/en/ai-interface.md) |

![What-if scenarios compared with the base plan](doc/img/scenarios_en.svg)

## Example Results (without installing)

![Gantt chart from the Markdown report of software_simple.json](doc/de/img/software_simple_gantt.svg)

Pre-computed results of the examples are in [doc/result_examples/](doc/result_examples/README.md), e.g. for
`software_simple.json`. **Readable with one click:** the Markdown report (Gantt chart and network diagram render
directly on GitHub/Gitea) and the charts on this page.

| File | Content |
| --- | --- |
| [software_simple.md](doc/result_examples/software_simple.md) | report with Gantt chart and network diagram (renders directly on GitHub/Gitea) |
| [software_simple.html](doc/result_examples/software_simple.html) | the same report as HTML – *download and open* |
| [software_simple_charts.html](doc/result_examples/software_simple_charts.html) | interactive Gantt chart and resource utilization – *download and open, needs internet* |
| [software_simple_scenarios.html](doc/result_examples/software_simple_scenarios.html) | scenario comparison – *download and open, needs internet* |
| [software_simple_simulation.html](doc/result_examples/software_simple_simulation.html) | Monte Carlo simulation with criticality – *download and open, needs internet* |
| [software_simple.xlsx](doc/result_examples/software_simple.xlsx) | Excel report – *download and open* |

On GitHub/Gitea, clicking an HTML file only shows its source code – use *Download raw file* and open it in a
browser. The interactive pages load the Plotly library from the internet.

## Documentation

| Topic | Document |
| --- | --- |
| Desktop editor | [doc/en/gui.md](doc/en/gui.md) |
| Command line, export formats, output | [doc/en/cli.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/cli.md) |
| AI interface (MCP server, Claude, Excel import) | [doc/en/ai-interface.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/ai-interface.md) |
| Project file format: durations, dependencies, resources, loops, uncertainties, scenarios | [doc/en/project-format.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/project-format.md) |
| Configuration, public holidays | [doc/en/configuration.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/configuration.md) |
| Example projects | [`examples/`](examples/) – `en/` English, `de/` German; description: [doc/en/examples.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/examples.md) |
| Tests, development, project structure | [doc/en/development.md](doc/en/development.md) |
| Dates, resources, plan vs. actual, scenarios, Monte Carlo (German) | [doc/de/termine-und-ist.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/termine-und-ist.md) |

## License

This project is licensed under the [MIT License](LICENSE).
