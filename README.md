# sproject.py – CPM Project Planning

**sproject.py** calculates the critical path (CPM – Critical Path Method) from simple JSON project files and exports the results in various formats.

 ![svg example](doc/de/img/software_simple_gantt.svg)

> Deutsche Dokumentation: [README.de.md](README.de.md)

## Purpose

- **CPM Calculation**: Earliest/latest start and finish, total float, free float, critical path
- **Calendar Integration**: Weekends and public holidays are skipped in date calculations
- **Resource Management**: Optional persons, hourly rates, and cost overview
- **Gantt Chart**: Schedule visualization based on working days
- **Scenarios**: What-if variants (e.g. "task takes 50 % longer", "person sick for a week") compared with the base plan
- **Monte Carlo Simulation**: Duration ranges, risks and scenario probabilities → "80 % finished by …"
- **GUI Editor**: Edit projects in a desktop app (Dear PyGui), calculate and export
- **Multiple Export Formats**: JSON, TXT, XLSX, Markdown, HTML, SVG-ZIP, interactive charts

## Project Structure

```text
sproject/
├── bin/                        # Windows batch scripts
│   ├── setenv.bat              # Set environment variables
│   ├── activate_venv.bat       # Activate virtual environment
│   ├── create_reports.bat      # Generate reports
│   ├── gui.bat                 # Start the GUI editor
│   └── run_unittests.bat       # Run unit tests
├── cfg/                        # Configuration files
│   ├── defaults.cfg            # Main config (calendar, CPM, costs)
│   ├── excel_export.cfg        # XLSX tab order and names
│   ├── txt_export.cfg          # TXT output structure
│   ├── json_export.cfg         # JSON export settings
│   ├── markdown_export.cfg     # Markdown/Mermaid options (also used for HTML and ZIP)
│   └── holidays_BY_2026.json   # Bavaria public holidays 2026
├── examples/                   # Sample project files
│   ├── pizza.json              # Simple example (minutes)
│   ├── pizzas.json             # Loop-task example
│   ├── hausbau.json            # AA/EE dependency example
│   ├── simpleproject.json      # Machine assembly (days)
│   ├── software_simple.json    # Software project with resources
│   ├── tankdesign.json         # Engineering project
│   └── results/                # Pre-computed reference results
├── gui/                        # GUI editor (Dear PyGui)
│   ├── app.py                  # Layout, menus, toolbar, dialogs
│   ├── editor.py               # Editor state, file operations, calculation, exports
│   ├── task_rows.py            # Lossless conversion tasks ↔ table rows
│   ├── analysis_rows.py        # Text ↔ model for uncertainties and scenarios
│   └── components/             # Sections, tables, result panel, sidebar
├── lib/                        # Python source code (package "lib")
│   ├── sproject.py             # CLI entry point
│   ├── schedule.py             # build_schedule(): expand → CPM → Gantt → costs
│   ├── scenarios.py            # Apply and compare scenarios
│   ├── simulation.py           # Monte Carlo simulation
│   ├── charts.py               # Plotly charts (Gantt, resources, simulation)
│   ├── exporters.py            # Export registry (shared by CLI and GUI)
│   ├── models/                 # Pydantic models
│   │   ├── project.py          # Project root model (data + validation)
│   │   ├── tasks.py            # Task models (incl. loop/cycle)
│   │   ├── dependencies.py     # Dependency types EA/AA/EE/AE
│   │   ├── resources.py        # Resources and persons
│   │   ├── expander.py         # Expansion of instance/loop tasks
│   │   ├── rest_breaks.py      # Rest breaks for persons
│   │   ├── cpm.py              # CPM calculation
│   │   ├── gantt.py            # Gantt scheduling (calendar dates)
│   │   └── loader.py           # JSON loader
│   ├── durations.py            # Duration parsing/formatting (hours_per_day from defaults.cfg)
│   ├── work_calendar.py        # Working days, weekends, holidays
│   ├── cost_calculator.py      # Cost calculation
│   ├── report_data.py          # Data preparation shared by the exports
│   ├── excel_reports.py        # XLSX export
│   ├── json_export.py          # JSON export
│   ├── txt_export.py           # TXT export
│   ├── markdown_export.py      # Markdown/HTML/ZIP export
│   ├── mermaid_export.py       # SVG via Mermaid/kroki
│   ├── colors.py, paths.py, export_config.py, config_loader.py
├── tests/                      # pytest (incl. golden-file tests in tests/golden/)
├── requirements.txt            # Python dependencies
├── log/                        # Log files (auto-created)
├── results/                    # Generated reports (auto-created)
└── README.md
```

## Installation

### Requirements

- Python 3.10 or higher

### Dependencies

create a virtual environment and install pip dependencies: 

#### Windows
double click on 

```dos
bin/install_py.bat
```
#### Linux/Mac

call 

```bash
bash bin/install_py.sh
```

## Usage

### Process a single project

put your new newproj.json file in the sproject/data folder. Then call
call the create_reports.bat/.sh in the bin folder
or call direct

```bash
python lib/sproject.py --project newproj.json
```

### Choose export format

```bash
# JSON only (default)
python lib/sproject.py --project examples/tankdesign.json

# Multiple formats at once
python lib/sproject.py --project examples/hausbau.json --export txt,json,xlsx,md,html,zip

# All available formats
python lib/sproject.py --project examples/software_simple.json --export txt,json,xlsx,md,html,zip
```

### Process all projects in a directory

```bash
python lib/sproject.py --data-dir examples --export json
```

### Additional options

```bash
# Custom output directory
python lib/sproject.py --project examples/pizza.json --output-dir ./my_results

# Override start date
python lib/sproject.py --project examples/simpleproject.json --start-date 2026-06-01

# Custom config directory
python lib/sproject.py --project examples/pizza.json --cfg-dir ./cfg

# Verbose output
python lib/sproject.py --project examples/pizza.json --verbose

# Compare all scenarios with the base plan / calculate one scenario instead of the base plan
python lib/sproject.py --project examples/software_simple.json --scenarios
python lib/sproject.py --project examples/software_simple.json --scenario "Alice eine Woche krank" --export xlsx

# Monte Carlo simulation with 500 runs (reproducible with --seed)
python lib/sproject.py --project examples/software_simple.json --simulate 500 --seed 42

# Help
python lib/sproject.py --help
```

### Export Formats

| Format | Description |
| ------ | ----------- |
| `json` | Network plan + Gantt as JSON (default) |
| `txt` | Structured plain-text report |
| `xlsx` | Excel with configurable tabs (via `cfg/excel_export.cfg`) |
| `md` | Markdown report with embedded Mermaid diagrams |
| `html` | HTML report — Mermaid diagrams rendered in the browser |
| `zip` | All diagrams (Gantt, network plan, resource Gantts) as SVG files in a ZIP archive (rendered via kroki.io) |
| `plotly` | Interactive HTML charts (Gantt, resources) |
| `plotly_svg` | The Plotly charts as SVG images (needs kaleido and a local Chrome) |
| `scenarios` | Scenario comparison as HTML |
| `simulation` | Monte Carlo simulation as HTML (histogram, criticality, key figures) |

> **Excel tabs** (Gantt chart, resource list, etc.) are controlled by `section_order` in `cfg/excel_export.cfg` — no command-line flags needed.

## Graphical Editor (GUI)

Start with `bin/gui.bat` (Windows) or `bash bin/gui.sh` (Linux/Mac). Open an example from the sidebar or a file via *File → Open*.

| Section | Content |
| ------- | ------- |
| 1. Project master data | Name, start date, unit, volumes, status date |
| 2. Tasks | Simple, loop and subtasks with duration, resources, successors, costs |
| 3. Resources | ID, name, type, color – color field with color picker (click the swatch or double-click the hex value) |
| 4. Persons | Name, role, hourly rate |
| 5. Rest periods and vacation | Rest rules, vacation, part-time |
| 6. Uncertainties | Per task: Min/Max duration and risk (probability, delay, note) for the Monte Carlo simulation |
| 7. Scenarios | What-if variants with probability, and their changes (task, resource, person) |

Sections 3–7 are optional and can be switched on in the sidebar; they appear automatically when the loaded project uses them.

- **Edit:** type directly in the tables, or double-click a row in sections 6 and 7 to open it in a form.
- **Warning:** if a task's planned duration lies outside its Min–Max range, section 6 marks it red (the simulation would use the edge of the range).
- **Analysis menu / toolbar:** calculate, compare scenarios, run the Monte Carlo simulation. Results appear in the *Result* tab; reports go to `results/`.
- **Language:** German / English via *Settings*.

## AI Interface (MCP)

Claude Code, Claude Desktop or a chatbot can build, check, calculate and save projects through an
MCP server – headless (`.mcp.json` / `bin/mcp_server.bat`) or live in the running GUI
(*Settings → AI interface (MCP) active*, `http://127.0.0.1:8765/mcp`). Python scripts can use
`lib.api.ProjectSession` directly. Details (in German): [doc/de/ki-schnittstelle.md](doc/de/ki-schnittstelle.md).

## Project File Format (JSON)

### Minimal Example

```json
{
  "project": "My Project",
  "project_start": "2026-04-01 08:00:00",
  "tasks": [
    {
      "id": 1,
      "name": "Planning",
      "duration": "3d",
      "successors": [2]
    },
    {
      "id": 2,
      "name": "Implementation",
      "duration": "10d",
      "successors": [3]
    },
    {
      "id": 3,
      "name": "Acceptance",
      "duration": "2d",
      "successors": []
    }
  ]
}
```

### Duration Formats

| Value   | Meaning                    |
| ------- | -------------------------- |
| `"10d"` | 10 working days            |
| `"2w"`  | 2 weeks = 10 working days  |
| `"8h"`  | 8 hours = 1 working day    |
| `"30m"` | 30 minutes                 |
| `10`    | 10 days (numeric)          |

### Dependency Types

| Field | Type | Meaning |
| --------------- | ---- | ------- |
| `successors` | FS | Finish→Start: successor starts after predecessor finishes (default) |
| `successors_aa` | SS | Start→Start: successor starts at the same time as predecessor |
| `successors_ae` | SF | Start→Finish: successor finishes when predecessor starts |
| `successors_ee` | FF | Finish→Finish: successor finishes at the same time as predecessor |

Example (from `hausbau.json`):

```json
{
  "id": 5,
  "name": "Build masonry",
  "duration": "10d",
  "successors": [10],
  "successors_aa": [6, 7],
  "note": "SS: Electrical and plumbing start as soon as masonry starts"
}
```

### Project with Resources and Costs

```json
{
  "project": "Software Project",
  "project_start": "2026-04-01 09:00:00",
  "persons": [
    {
      "id": "DEV1",
      "name": "Alice",
      "email": "alice@example.com",
      "role": "Senior Developer",
      "hourly_rate": 85.0,
      "vacation": [
        {"from": "2026-04-14", "to": "2026-04-18", "description": "Holiday"}
      ]
    }
  ],
  "resources": [
    {
      "id": "R_DEV1",
      "name": "Senior Developer",
      "type": "person",
      "person_id": "DEV1"
    }
  ],
  "tasks": [
    {
      "id": 1,
      "name": "Backend Development",
      "duration": "40h",
      "resources": ["R_DEV1"],
      "successors": [2]
    },
    {
      "id": 2,
      "name": "Deployment",
      "duration": "8h",
      "resources": ["R_DEV1"],
      "successors": []
    }
  ]
}
```

### Loop Tasks (Recurring Operations)

For repeating cycles (e.g. production loops), use `is_loop` tasks:

```json
{
  "id": 2,
  "name": "Production Cycle",
  "is_loop": true,
  "loop_until": "total_volume <= 0",
  "cycle_prefix": "P",
  "volume_per_cycle": 1,
  "subtasks": [
    {"name": "Processing", "duration": "5m", "resources": ["R_WORKER"]},
    {"name": "Quality Check", "duration": "2m", "resources": ["R_QA"]}
  ]
}
```

Loop tasks are automatically expanded before CPM calculation.

### Uncertainties and Scenarios

Uncertainties for the Monte Carlo simulation are set per task; scenarios are named lists of changes to the base plan:

```json
{
  "tasks": [
    { "id": 4, "name": "Backend", "duration": "40h",
      "duration_range": ["32h", "72h"],
      "risk": { "probability": 0.2, "delay": "16h", "note": "Customer API still unstable" } }
  ],
  "scenarios": [
    { "name": "Alice sick for a week", "probability": 0.15,
      "changes": [ { "person": "DEV1", "vacation": [ { "from": "2026-03-09", "to": "2026-03-13", "description": "sick" } ] } ] },
    { "name": "Backend 50 % more effort",
      "changes": [ { "task": 4, "duration_factor": 1.5 } ] }
  ]
}
```

| Field | Effect |
| ----- | ------ |
| `duration_range` | Duration varies between minimum and maximum, most often the planned duration (triangular distribution) |
| `risk` | With `probability` the start is delayed by `delay` |
| `scenarios[].changes` | Exactly one of `task` (ID or pattern like `2-F*.1`), `resource` (`unavailable`), `person` (`vacation`); task changes: `duration_factor` or any task field |
| `scenarios[].probability` | The scenario occurs with this probability in the simulation; without it the scenario is only compared |

Details (in German): [doc/de/termine-und-ist.md](doc/de/termine-und-ist.md). Example: `examples/software_simple.json`.

## Configuration

All defaults are read from `cfg/defaults.cfg`:

```ini
[CPM]
skip_weekends  = true     # Skip weekends
skip_holidays  = true     # Skip public holidays (Bavaria 2026)

[WorkingHours]
hours_per_day  = 8        # Working hours per day
days_per_week  = 5        # Working days per week

[Resource]
hourly_rate    = 100.00   # Default hourly rate (EUR)

[Costs]
overhead_factor = 1.5     # Overhead multiplier

[Output]
results_dir    = results  # Output directory
```

## CPM Output Structure

```text
ID      Name                           Duration  ES     EF     LS     LF     TF     FF     Crit.
─────────────────────────────────────────────────────────────────────────────────────────────────
1       Planning                       3d        0.0    3.0    0.0    3.0    0.0    0.0    YES
2       Implementation                 10d       3.0    13.0   3.0    13.0   0.0    0.0    YES
3       Acceptance                     2d        13.0   15.0   13.0   15.0   0.0    0.0    YES
```

| Column | Meaning              |
| ------ | -------------------- |
| ES     | Earliest Start       |
| EF     | Earliest Finish      |
| LS     | Latest Start         |
| LF     | Latest Finish        |
| TF     | Total Float          |
| FF     | Free Float           |

## Example Projects

| File                   | Description                  | Features                          |
| ---------------------- | ---------------------------- | --------------------------------- |
| `pizza.json`           | Pizza preparation (minutes)  | Short durations in `m`            |
| `pizzas.json`          | Pizza service with volume    | Loop tasks, resources, machines   |
| `simpleproject.json`   | Machine assembly             | Classic CPM example               |
| `tankdesign.json`      | Tank design project          | Simple engineering project        |
| `hausbau.json`         | Single-family house build    | SS/FF dependencies                |
| `erdaushub.json`       | Excavation                   | Parallel activities               |
| `fassadenbau.json`     | Facade construction          | Section-by-section assembly       |
| `software_simple.json` | Software development         | Persons, resources, costs         |


 Here an example for an ouptut as [markdown with mermaid diagramm](doc/result_examples/software_simple.md) or as [html](doc/result_examples/software_simple.html)

## Tests

Run all tests (unit tests, golden-file comparison of all examples, headless GUI tests):

```bash
python -m pytest
```

After an intended change of results, regenerate the reference files in `tests/golden/`:

```bash
UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py
```

Or via batch script (Windows):

```cmd
bin\run_unittests.bat
```

## Development

### Code Quality

```bash
make lint           # All tools
make lint-dead      # Dead code only (vulture + skylos)
make lint-types     # Type checks only (pyright + mypy)
```

Individual tools:

```bash
make vulture        # Dead code (80% confidence)
make skylos         # Dead code (ML-based)
make pyright        # Type checking (fast)
make mypy           # Type checking (strict)
```

### Adding New Projects

1. Create a JSON file in `examples/` (see format above)
2. Run: `python lib/sproject.py --project examples/myproject.json`
3. Check results in the `results/` directory

### Extending Models

- Task models: [lib/models/tasks.py](lib/models/tasks.py)
- Resources: [lib/models/resources.py](lib/models/resources.py)
- CPM calculation: [lib/models/cpm.py](lib/models/cpm.py)
- Gantt: [lib/models/gantt.py](lib/models/gantt.py)
- Export modules: `lib/*_export.py`

## Logging

Log files are created automatically under `log/`:

- Format: `sproject_YYYYMMDD_HHMMSS.log`
- Console: INFO level (key messages)
- File: DEBUG level (full details)

## License

This project is licensed under the [MIT License](LICENSE).
