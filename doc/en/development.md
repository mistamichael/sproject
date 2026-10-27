# Development

> Part of the [sproject documentation](../../README.md#documentation). Deutsch: [doc/de/entwicklung.md](../de/entwicklung.md)

## Tests

Run all tests (unit tests, golden-file comparison of all examples, headless GUI tests):

```bash
python -m pytest
```

After an intended change of results, regenerate the reference files in `tests/golden/`:

```bash
UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py
```

Only the AI interface (API, MCP tools, GUI connection over HTTP):

```bash
python -m pytest tests/test_api.py
python -m pytest tests/test_gui_headless.py -k server_link
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

- Task models: [lib/models/tasks.py](../../lib/models/tasks.py)
- Resources: [lib/models/resources.py](../../lib/models/resources.py)
- CPM calculation: [lib/models/cpm.py](../../lib/models/cpm.py)
- Gantt: [lib/models/gantt.py](../../lib/models/gantt.py)
- Export modules: `lib/*_export.py`

## Project Structure

```text
sproject/
├── bin/                        # Start scripts, each as .bat (Windows) and .sh (Linux/macOS)
│   ├── install_py.bat          # Install: create .venv and pip install (double-click)
│   ├── setenv.bat              # Set environment variables
│   ├── activate_venv.bat       # Activate virtual environment
│   ├── create_reports.bat      # Generate reports
│   ├── gui.bat                 # Start the GUI editor
│   ├── mcp_server.bat          # Start the sproject server (AI interface): --port [N] | --claude
│   └── run_unittests.bat       # Run unit tests
├── cfg/                        # Configuration files
│   ├── defaults.cfg            # Main config (calendar, CPM, costs)
│   ├── excel_export.cfg        # XLSX tab order and names
│   ├── txt_export.cfg          # TXT output structure
│   ├── json_export.cfg         # JSON export settings
│   └── markdown_export.cfg     # Markdown/Mermaid options (also used for HTML and ZIP)
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
│   ├── server_link.py          # GUI connection to the sproject server (menu Server)
│   └── components/             # Sections, tables, result panel, sidebar
├── lib/                        # Python source code (package "lib")
│   ├── sproject.py             # CLI entry point
│   ├── api.py                  # ProjectSession: project operations for AI tools and scripts
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
├── mcp_server/                 # MCP server (AI interface): tools on top of lib/api.py
├── tests/                      # pytest (incl. golden-file tests in tests/golden/)
├── data/                       # Your project files for the CLI (example: simple_software_project.xlsx)
├── .mcp.json                   # Registers the MCP server for Claude Code
├── requirements.txt            # Python dependencies
├── log/                        # Log files (auto-created)
├── results/                    # Generated reports (auto-created)
└── README.md
```
