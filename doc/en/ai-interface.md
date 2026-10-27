# AI Interface (MCP)

With the AI interface, an AI tool such as Claude Code or Claude Desktop can create projects, build them
from Excel lists or other sources, check, calculate and save them – on its own or together with the GUI.
Python scripts use the same operations directly.

> Deutsche Fassung: [doc/de/ki-schnittstelle.md](../de/ki-schnittstelle.md)

## Core Idea: Exactly One sproject Server

```text
Claude Code / Claude Desktop          GUI (bin\gui.bat)
        │  MCP over HTTP                      │  Server → Connect to sproject server …
        └──────────────┬──────────────────────┘
                       ▼
        sproject server  (bin\mcp_server.bat, http://127.0.0.1:8765/mcp)
        mcp_server/server.py → lib/api.py ProjectSession → holds THE project
                       ▼
        lib/models, build_schedule, exporters, scenarios, simulation
```

- **One** server runs and holds **one** project. Claude and the GUI are both just clients and always see
  the same state – there is no second, hidden copy.
- A second server on the same port refuses to start ("Port 8765 ist belegt – läuft schon ein sproject-Server?").
- The GUI connects only **explicitly** (menu *Server*). Without a connection it works locally as before.
- The AI reads source data (Excel, PDF, text) itself and transfers it into the project with the tools.
- Every change is validated immediately. Invalid input changes nothing and returns an error message.
- Calculation runs through `build_schedule()` – the same results as CLI and GUI.

## Setup

### 1. Start the server

```text
bin\mcp_server.bat                  HTTP on http://127.0.0.1:8765/mcp (default)
bin\mcp_server.bat --port [N]       HTTP on port N (without N: 8765)
bin\mcp_server.bat --project FILE   open a project at startup
bin\mcp_server.bat --claude         stdio – for scripts/tests only (see below)
bin\mcp_server.bat --help           help
```

On Linux/macOS use `bin/mcp_server.sh` with the same switches. The window shows the address; stop with
Ctrl+C. Alternatively the GUI starts the server itself on request (see 3.).

### 2. Connect Claude Code

The repository contains `.mcp.json` – Claude Code uses it to connect to the running server over HTTP:

```json
{"mcpServers": {"sproject": {"type": "http", "url": "http://127.0.0.1:8765/mcp"}}}
```

Start Claude Code in the project folder and approve the server `sproject` once; `/mcp` shows its status.
If the server is not running yet, Claude Code reports the connection as failed – start the server, then
reconnect in `/mcp`. For a different port, change the URL in `.mcp.json`.

### 3. Connect the GUI (optional)

1. Start the GUI (`bin\gui.bat`), open a project if you like.
2. *Server → Connect to sproject server …*, confirm host and port (defaults from `cfg/gui.cfg`).
3. If no server is running there, the GUI asks "Start it now?". *Yes* starts `bin\mcp_server.bat --port N`
   in its own window; the GUI connects as soon as it is ready. The server keeps running after the GUI closes.

When connecting:

| Server state | What happens |
| --- | --- |
| server has no project yet | the GUI's project is sent to the server |
| server has a project | the GUI takes it over; with unsaved GUI changes it asks first |
| something else listens at the address | "… is not a sproject server", no connection |

While the GUI is connected:

- Title bar and status bar show "connected to `http://127.0.0.1:8765/mcp`".
- GUI changes are sent to the server about once per second – but not while an input field is active
  (nothing is overwritten while typing).
- Changes made by Claude appear in the tables just as quickly; optional sections are shown.
- **Conflict** (GUI and Claude change at the same time): the server version wins, the status bar reports
  "Conflict …". The lost GUI input is backed up to `work/backup/` first (path in the status bar).
- **Project switch** (someone replaces the whole project): see [Project switches and backups](#project-switches-and-backups).
- If the server rejects a GUI state (e.g. invalid duration), the reason appears in the status bar; the GUI
  stays connected.
- *Save* in the GUI writes the file locally as before. When Claude saves (`save_project`), the server writes the file.
- *Server → Disconnect* disconnects only the GUI; the server keeps running.

Settings in `cfg/gui.cfg` (defaults for the connect dialog):

```ini
[server]
host = 127.0.0.1
port = 8765
```

The server listens on `127.0.0.1` only and is therefore reachable from the local machine only.

### stdio mode (special case)

`bin\mcp_server.bat --claude` starts a server over stdio, e.g. for an MCP client that launches the server
itself, or for tests. Such a server is **private** to that one client – the GUI cannot connect to it.
To work together with the GUI, always use the HTTP server.

## Quick Start: New Project from an Excel File

For a first try, [`data/simple_software_project.xlsx`](../../data/simple_software_project.xlsx) is included –
a small web shop relaunch with three sheets (content in German):

| Sheet | Content |
| --- | --- |
| Projekt | project name "Webshop Relaunch", start 2 Nov 2026 |
| Aufgaben | no., activity, duration (days), predecessors (e.g. "4, 5"), responsible, min/max (days), remark |
| Team | short code, name, role, hourly rate (€/h) |

How to:

1. Start the server: `bin\mcp_server.bat`
2. Optionally connect the GUI (*Server → Connect to sproject server …*) to watch.
3. Start Claude Code in the project folder and check with `/mcp` that `sproject` is connected.
4. Ask Claude, for example:

   > Read `data/simple_software_project.xlsx` and build a new sproject project from it: master data from the
   > sheet "Projekt", persons and resources from "Team", tasks with dependencies from "Aufgaben". Assign each
   > task to the responsible person, use min/max as uncertainty and set the deadline 15 Dec 2026 for the
   > go-live. Check the project, calculate it, tell me end date, costs and critical path, simulate 300 runs
   > and save it as `webshop.json`.

Claude reads the Excel file itself and then calls the tools one after another: `new_project`, `upsert_item`
(persons and resources), `add_task` (the response contains the task id), `add_dependency` (predecessor →
successor with these ids), `set_uncertainty`, `update_task` (deadline), `validate`, `calculate`, `simulate`
and `save_project` (the file ends up in `work/webshop.json`). If the GUI is connected, you watch the project grow.

Expected result: end on 3 Dec 2026 (24 working days), costs 23,240 €, critical path kick-off → UX concept →
frontend → integration → test & QA → go-live, deadline met. The simulation shows that the plan is rarely met
(P80 around 9 Dec 2026) – a good starting point for questions like "What does a second frontend developer gain?".

Your own Excel files need no fixed format: describe sheets and columns to Claude in the request; Claude asks
if something is unclear.

## Project Switches and Backups

The server holds exactly one project. If it is **replaced as a whole**, the server first backs up the
previous state to `work/backup/<timestamp>_<project name>.json` (folder: `$PV_WORK/backup`) and reports the
switch on both sides:

| Trigger | Message to Claude | Message in the GUI |
| --- | --- | --- |
| Claude: `new_project`, `load_project`, `replace_project` without `base_revision` | response contains `warning` with old/new project and backup path | notice dialog "Another client replaced the project …" with backup path |
| GUI: *File → New* or *Open* while connected | the **next** call is **not executed** and reports the switch with the backup path; calling again then works | status bar "Project replaced on the server …" with backup path |

In addition:

- If the GUI had input not yet sent when the project was replaced (or on a conflict, or when discarding
  unsaved changes while connecting), the GUI backs that up to `work/backup/` as well.
- The server window logs every switch (`[sproject] Projekt ersetzt: …`).
- The project is only replaced if the new data is valid – otherwise nothing changes (no backup).
- A backup is loaded like any project file: in the GUI via *File → Open*, or by Claude with `load_project`
  (e.g. "Load the latest backup from work/backup").
- To change the existing project Claude uses `patch_project`, `add_task` etc. – that is not a switch.

## Example Requests to Claude

- "Read `data/bauplan.xlsx` (columns: no., activity, duration in days, predecessors) and build an sproject
  project starting on 4 May 2026. Check it, calculate it and save it as `bauplan.json`."
- "Add the persons Anna (mason, 55 €/h) and Ben (carpenter, 60 €/h) to the open project, assign them to the
  matching tasks and tell me how end date and costs change."
- "Add a scenario 'window delivery delay' in which task 7 can start ten days later, and compare it with
  the base plan."
- "Estimate a min/max duration for all tasks and simulate: by when are we 80 % done?"

## Typical AI Workflow

```text
new_project / load_project
  → add_task (per task; the response contains the assigned id)
  → add_dependency (using the ids from add_task)
  → upsert_item (persons, resources) → update_task (assign resources)
  → validate → calculate → save_project
```

For large lists a single call is faster: `patch_project({"tasks": [...]})` or `replace_project({...})`
with the complete project in JSON format (schema: `sproject://schema`).

## Tools (MCP)

| Tool | Purpose / result |
| --- | --- |
| `new_project`, `load_project` | create / open a project → overview |
| `save_project` | save (relative paths → `work/`) → file path |
| `get_overview`, `get_project` | overview or complete JSON |
| `replace_project` | replace the whole project (project switch with backup and `warning`); with `base_revision` only a change of a known state (GUI sync) |
| `patch_project` | set top-level fields (bulk build in the existing project, not a switch) |
| `add_task` | create a task → stored task **incl. `id`** (without `id` the next number is assigned) |
| `get_task`, `update_task`, `remove_task` | read, change (`null` removes a field), delete a task |
| `add_dependency`, `remove_dependency` | dependencies EA (default, finish-to-start), AA, EE, AE |
| `set_uncertainty` | `duration_range` and `risk` for the simulation |
| `upsert_item`, `remove_item`, `set_list` | resources, persons, rest periods, scenarios |
| `validate` | unknown references, cycles, calculation errors → list (empty = OK) |
| `calculate` | start, end, critical path, costs, deadline warnings, dates per task |
| `compare_scenarios`, `simulate` | scenario comparison, Monte Carlo |
| `export` | reports (json, txt, md, html, xlsx, …) to `results/` |
| `list_examples` | example projects as templates |
| `get_revision`, `get_state` | change counter, or counter + project + path (for clients such as the GUI) |

MCP resources: `sproject://schema` (JSON schema of the project format), `sproject://examples/<name>`.

## From Python without MCP

For scripts without a server – works on its own project in memory:

```python
from lib.api import ProjectSession, ApiError

s = ProjectSession()
s.new_project("Garage", project_start="2026-04-01")
foundation = s.add_task({"name": "Foundation", "duration": "3d"})   # → task id (here 1)
walls = s.add_task({"name": "Walls", "duration": "5d"})
roof = s.add_task({"name": "Roof", "duration": "2d"})
s.add_dependency(foundation, walls)
s.add_dependency(walls, roof)

s.upsert_item("persons", {"id": "P1", "name": "Anna", "role": "Mason", "hourly_rate": 55})
s.upsert_item("resources", {"id": "R1", "type": "person", "person_id": "P1"})
s.update_task(walls, {"resources": ["R1"]})

assert s.validate() == []
result = s.calculate()
print(result["end"], result["total_costs"], [t["name"] for t in result["critical_path"]])
s.save("work/garage.json")
s.export(["xlsx", "html"])

try:
    s.add_dependency(roof, 99)
except ApiError as e:
    print(e)          # task 99 not found – the project stays unchanged
```

| Method | Returns |
| --- | --- |
| `new_project(name, project_start, unit)` | overview (dict) |
| `load(path)`, `replace_project(data, base_revision=None)`, `patch_project(fields)` | overview (dict) |
| `save(path=None)` | path as text |
| `get_project()`, `overview()`, `list_tasks()`, `schema()` | project JSON, overview, task list, JSON schema |
| `add_task(task)` | **task id** |
| `get_task(id)`, `update_task(id, fields)`, `set_uncertainty(id, …)` | task (dict, normalized, e.g. `"5"` → `"5d"`) |
| `remove_task(id)` | remaining task ids |
| `add_dependency(predecessor, successor, dep_type="EA")`, `remove_dependency(…)` | predecessor task (dict) |
| `upsert_item(field, item)`, `remove_item(field, key)`, `set_list(field, items)` | entry or count |
| `validate()` | list of problems (empty = OK) |
| `calculate(start_date=None)` | dict: `start`, `end`, `duration_days`, `critical_path`, `total_costs`, `deadline_warnings`, `tracking`, `tasks` |
| `export(formats, out_dir=None)` | list of created files |
| `compare_scenarios()`, `simulate(runs, seed)` | table or dict with `summary` and `top_critical` |
| `revision`, `state()` | change counter, or `{"revision", "project", "path"}` |

Errors are raised as `ApiError` (subclass of `ValueError`) with a readable message (in German).

## Troubleshooting

| Problem | Solution |
| --- | --- |
| "Port 8765 ist belegt – läuft schon ein sproject-Server?" | a server is already running – use it. Otherwise another port: `--port 8766` (then also adjust `.mcp.json` and the GUI dialog) |
| Claude Code: server `sproject` failed | the server is not running → start `bin\mcp_server.bat`, reconnect in `/mcp` |
| GUI: "No sproject server at …" | choose *Yes* in the dialog (starts it) or start `bin\mcp_server.bat` by hand |
| GUI: "sproject server could not be started" | read the message in the server window; does `.venv` exist? (`bin\install_py.bat`) |
| GUI: "Conflict …" | GUI and Claude changed at the same time; the server version applies. The GUI input is in `work/backup/` |
| GUI: notice "Another client replaced the project …" | Claude created/loaded a new project. The previous one is in `work/backup/` (path in the notice) |
| Claude: "Das Projekt wurde inzwischen von einem anderen Client … ersetzt" | another project was opened in the GUI. Claude should check with `get_overview` and ask the user; the old project is in `work/backup/` |
| GUI: "Server rejected the change …" | the GUI input is invalid (reason shown) – correct it |
| `.venv nicht gefunden` | run `bin\install_py.bat` (also installs the `mcp` package) |
| own extension breaks the stdio connection | in stdio mode never `print()` to stdout – write to stderr or the log |

## Tests

```bash
python -m pytest tests/test_api.py                            # API, MCP tools, revision/conflict, port lock
python -m pytest tests/test_gui_headless.py -k server_link    # GUI ↔ server ↔ second client (Claude)
npx @modelcontextprotocol/inspector                           # try the tools: URL http://127.0.0.1:8765/mcp
```
