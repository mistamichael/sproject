# Graphical Editor (GUI)

> Part of the [sproject documentation](../../README.md#documentation). Deutsch: [doc/de/gui.md](../de/gui.md)

![sproject editor: Gantt chart and resource utilization](../de/img/gui_editor_en.png)

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
- **AI interface:** *Server → Connect to moncapro server …* shares the project with Claude (see below).
