# Command Line (CLI)

> Part of the [sproject documentation](../../README.md#documentation). Deutsch: [doc/de/cli.md](../de/cli.md)

## Usage

### Process a single project

Put your project file (e.g. `newproj.json`) into the `data/` folder (`$PV_DATA`) and run
`bin/create_reports.bat` (`.sh`) – it processes all project files there – or call directly:

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

# Small interactive HTML charts: load plotly.js from the internet instead of embedding it (~4 MB)
python lib/sproject.py --project examples/software_simple.json --export plotly,simulation --plotly-cdn

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

Charts of `--export plotly` (interactive HTML) and `--export plotly_svg` for `examples/software_simple.json`:

![Gantt chart](../img/gantt_en.svg)

![Resource utilization](../img/resources_en.svg)

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

## Logging

Log files are created automatically under `log/`:

- Format: `sproject_YYYYMMDD_HHMMSS.log`
- Console: INFO level (key messages)
- File: DEBUG level (full details)
