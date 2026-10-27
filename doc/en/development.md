# Development

> Part of the [sproject documentation](../../README.md#documentation). Deutsch: [doc/de/entwicklung.md](../de/entwicklung.md)

sproject is the desktop editor. All calculation (CPM, resource leveling, scenarios, Monte Carlo, exports) and the
AI interface (MCP server) live in the separate package
[moncapro](https://github.com/mistamichael/moncapro) – `pip install moncapro`. Changes to the model, the
calculation, the exports or the MCP tools belong there.

## Tests

```bash
python -m pytest                                              # headless GUI tests
python -m pytest tests/test_gui_headless.py -k server_link    # GUI ↔ server ↔ second client (Claude)
```

or on Windows `bin\run_unittests.bat`. The tests of the calculation core (including the golden-file
comparison of all examples) run in the moncapro repository.

## Development

### Code Quality

```bash
make lint           # All tools
make lint-dead      # Dead code only (vulture + skylos)
make lint-types     # Type checks only (pyright + mypy)
```

### Working on moncapro and sproject together

```bash
pip install -e ../moncapro[all]     # use a local checkout instead of the git/PyPI version
```

### Extending models and exports

Task models, resources, CPM, Gantt and the export modules are in `src/moncapro/` of the
[moncapro repository](https://github.com/mistamichael/moncapro). The GUI's own example projects are in `examples/en` (English) and `examples/de` (German) in this repository; the
sidebar lists the ones for the active language. `tests/test_examples.py` makes sure both versions stay in sync.
moncapro additionally ships its own copies as test data (`moncapro.paths.get_examples_dir()`).

## Project Structure

```text
sproject/
├── bin/                        # Start scripts, each as .bat (Windows) and .sh (Linux/macOS)
│   ├── install_py.bat          # Install: create .venv and pip install (double-click)
│   ├── setenv.bat              # Set environment variables (PV_*, MONCAPRO_*)
│   ├── activate_venv.bat       # Activate virtual environment
│   ├── create_reports.bat      # Generate reports (calls `python -m moncapro`)
│   ├── gui.bat                 # Start the GUI editor
│   ├── mcp_server.bat          # Start the moncapro server (AI interface): --port [N] | --claude
│   └── run_unittests.bat       # Run unit tests
├── cfg/                        # GUI configuration
│   ├── gui.cfg                 # Colors, sizes, server defaults
│   └── themes/                 # Theme files
├── examples/                   # Example projects: en/ (English) and de/ (German), results/ (pre-computed)
├── gui/                        # GUI editor (Dear PyGui)
│   ├── app.py                  # Layout, menus, toolbar, dialogs
│   ├── editor.py               # Editor state, file operations, calculation, exports
│   ├── task_rows.py            # Lossless conversion tasks ↔ table rows
│   ├── analysis_rows.py        # Text ↔ model for uncertainties and scenarios
│   ├── examples.py             # Which example folder is shown (language, PV_EXAMPLES, fallback)
│   ├── server_link.py          # GUI connection to the moncapro server (menu Server)
│   └── components/             # Sections, tables, result panel, sidebar
├── tests/                      # pytest: headless GUI tests
├── data/                       # Your project files (example: simple_software_project.xlsx)
├── doc/                        # GUI documentation, images, pre-computed example results
├── .mcp.json                   # Registers the MCP server for Claude Code
├── requirements.txt            # moncapro[all], dearpygui, pytest
├── log/                        # Log files (auto-created)
├── results/                    # Generated reports (auto-created)
└── README.md
```

`PV_CFG` points to this `cfg/` (GUI only). The calculation uses the configuration packaged with moncapro
(working hours, calendar, export layout); to change it, point `MONCAPRO_CFG` to your own copy.
