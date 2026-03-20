# sproject.py – CPM Project Planning

**sproject.py** calculates the critical path (CPM – Critical Path Method) from simple JSON project files and exports the results in various formats.

> Deutsche Dokumentation: [README.de.md](README.de.md)

## Purpose

- **CPM Calculation**: Earliest/latest start and finish, total float, free float, critical path
- **Calendar Integration**: Weekends and public holidays are skipped in date calculations
- **Resource Management**: Optional persons, hourly rates, and cost overview
- **Gantt Chart**: Schedule visualization based on working days
- **Multiple Export Formats**: JSON, TXT, XLSX, Markdown, HTML, SVG-ZIP

## Project Structure

```text
sproject/
├── bin/                        # Windows batch scripts
│   ├── setenv.bat              # Set environment variables
│   ├── activate_venv.bat       # Activate virtual environment
│   ├── create_reports.bat      # Generate reports
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
├── lib/                        # Python source code
│   ├── sproject.py             # Main entry point
│   ├── models/                 # Pydantic models
│   │   ├── cpm.py              # CPM calculation
│   │   ├── gantt.py            # Gantt scheduling
│   │   ├── tasks.py            # Task models (incl. loop/cycle)
│   │   ├── resources.py        # Resources and persons
│   │   ├── project.py          # Project root model
│   │   └── loader.py           # JSON loader
│   ├── excel_reports.py        # XLSX export
│   ├── json_export.py          # JSON export
│   ├── txt_export.py           # TXT export
│   ├── markdown_export.py      # Markdown/HTML/ZIP export
│   ├── mermaid_export.py       # SVG via Mermaid/kroki
│   ├── utils.py                # Utility functions
│   └── config_loader.py        # Configuration reader
├── requirements.txt            # Python dependencies
├── log/                        # Log files (auto-created)
├── results/                    # Generated reports (auto-created)
└── README.md
```

## Installation

### Requirements

- Python 3.10 or higher

### Dependencies

```bash
pip install -r requirements.txt
```

Or individually:

```bash
pip install pydantic          # Required
pip install openpyxl          # For XLSX export
pip install requests          # For SVG/ZIP export (via kroki.io)
pip install markdown          # For HTML export
```

With a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate.bat     # Windows
pip install -r requirements.txt
```

## Usage

### Process a single project

```bash
python lib/sproject.py --project examples/pizza.json
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

> **Excel tabs** (Gantt chart, resource list, etc.) are controlled by `section_order` in `cfg/excel_export.cfg` — no command-line flags needed.

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

Run unit tests:

```bash
cd lib
python -m unittest test.py
python -m unittest test_models.py
python -m unittest test_sproject.py
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
