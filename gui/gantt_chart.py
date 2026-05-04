"""
Gantt-Diagramm und Ressourcenauslastung via matplotlib
=======================================================

Erzeugt PNG-Bilder in-memory (BytesIO), die von Dear PyGui als Texture
angezeigt werden können.
"""

from io import BytesIO
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from lib.models.cpm import CPMResult, CPMTaskResult


def _hex_to_mpl(hex_str: str) -> str:
    """Wandelt '4472C4' in '#4472C4' um."""
    hex_str = hex_str.lstrip("#")
    return f"#{hex_str}"


def render_gantt_png(
    result: CPMResult,
    resource_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    width: int = 1000,
    height: int = 0,
    dpi: int = 100,
    dark_mode: bool = True,
) -> bytes:
    """Rendert ein Gantt-Diagramm als PNG-Bytes.

    Args:
        result: CPMResult mit Tasks
        resource_colors: Optionale Farbzuordnung resource_id → (R,G,B)
        width: Breite in Pixeln
        height: Höhe in Pixeln (0 = auto)
        dpi: Auflösung
        dark_mode: Dunkler Hintergrund
    Returns:
        PNG als bytes
    """
    # Tasks filtern (keine Breaks)
    tasks: List[Tuple] = []
    for tid, t in result.tasks.items():
        if t.is_break:
            continue
        tasks.append((tid, t))

    n = len(tasks)
    if n == 0:
        return b""

    if height <= 0:
        height = max(200, n * 28 + 80)

    fig_w = width / dpi
    fig_h = height / dpi

    if dark_mode:
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    crit_color = "#DC5050"
    normal_color = "#4A90D9"
    buffer_color = "#3A3A5A" if dark_mode else "#D0D0E0"

    y_positions = list(range(n - 1, -1, -1))
    bar_height = 0.6

    labels = []
    for i, (tid, t) in enumerate(tasks):
        y = y_positions[i]
        label = f"{tid}: {t.name}"
        labels.append(label)

        color = crit_color if t.is_critical else normal_color

        # Taskbalken (FAZ → FEZ)
        ax.barh(
            y, t.fez - t.faz, left=t.faz, height=bar_height,
            color=color, edgecolor="white" if dark_mode else "black",
            linewidth=0.5, alpha=0.9,
        )

        # Puffer (FEZ → SEZ) als dünner Balken
        if t.puffer > 0.01:
            ax.barh(
                y, t.sez - t.fez, left=t.fez, height=bar_height * 0.3,
                color=buffer_color, alpha=0.6,
            )

        # Dauer als Text im Balken
        bar_width = t.fez - t.faz
        if bar_width > 0.5:
            ax.text(
                t.faz + bar_width / 2, y, f"{t.duration:.0f}",
                ha="center", va="center", fontsize=7,
                color="white" if dark_mode else "black", fontweight="bold",
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel(result.time_unit, fontsize=9)
    ax.set_title("Gantt-Diagramm", fontsize=11, fontweight="bold")
    ax.set_xlim(left=0)
    ax.grid(axis="x", alpha=0.3, linestyle="--")

    # Legende
    legend_patches = [
        mpatches.Patch(color=crit_color, label="Kritischer Pfad"),
        mpatches.Patch(color=normal_color, label="Normal"),
        mpatches.Patch(color=buffer_color, label="Puffer"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=7, framealpha=0.7)

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render_resource_chart_png(
    result: CPMResult,
    project=None,
    resource_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    width: int = 1000,
    height: int = 0,
    dpi: int = 100,
    dark_mode: bool = True,
) -> bytes:
    """Rendert ein Ressourcenauslastungs-Diagramm als PNG-Bytes.

    Zeigt pro Ressource einen horizontalen Balken für jeden Task, dem sie
    zugewiesen ist.

    Args:
        result: CPMResult
        project: Projekt-Objekt (für Ressourcen-Info)
        resource_colors: resource_id → (R,G,B) Farben
        width, height, dpi, dark_mode: Render-Optionen
    Returns:
        PNG als bytes, leer wenn keine Ressourcen
    """
    if not project or not project.resources:
        return b""

    # Sammle Ressource → Liste von (task_id, task_name, faz, fez, is_critical)
    res_tasks: Dict[str, List[Tuple]] = {}

    # Zuordnung: welche Tasks nutzen welche Ressource?
    for task in (project.tasks or []):
        task_resources = getattr(task, "resources", None) or []
        # Auch Subtasks bei LoopTasks berücksichtigen
        subtasks = getattr(task, "subtasks", None) or []
        all_res = list(task_resources)
        for sub in subtasks:
            all_res.extend(getattr(sub, "resources", None) or [])

        for rid in all_res:
            # Resolve OR/AND resource expressions
            clean_rid = rid.strip().replace("|", "").replace("&", "").strip()
            if not clean_rid:
                continue
            cpm_task = result.tasks.get(task.id)
            if not cpm_task or cpm_task.is_break:
                continue
            if clean_rid not in res_tasks:
                res_tasks[clean_rid] = []
            res_tasks[clean_rid].append((
                task.id, task.name,
                cpm_task.faz, cpm_task.fez,
                cpm_task.is_critical,
            ))

    if not res_tasks:
        return b""

    res_ids = sorted(res_tasks.keys())
    n = len(res_ids)

    if height <= 0:
        height = max(180, n * 40 + 80)

    fig_w = width / dpi
    fig_h = height / dpi

    if dark_mode:
        plt.style.use("dark_background")
    else:
        plt.style.use("default")

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    bar_height = 0.6
    crit_color = "#DC5050"

    for i, rid in enumerate(res_ids):
        y = n - 1 - i
        # Farbe für die Ressource
        if resource_colors and rid in resource_colors:
            rgb = resource_colors[rid]
            base_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        else:
            base_color = "#4A90D9"

        for (tid, tname, faz, fez, is_crit) in res_tasks[rid]:
            color = crit_color if is_crit else base_color
            ax.barh(
                y, fez - faz, left=faz, height=bar_height,
                color=color, edgecolor="white" if dark_mode else "black",
                linewidth=0.5, alpha=0.85,
            )
            bar_width = fez - faz
            if bar_width > 0.8:
                ax.text(
                    faz + bar_width / 2, y, str(tid),
                    ha="center", va="center", fontsize=7,
                    color="white", fontweight="bold",
                )

    # Ressourcen-Labels mit Namen
    res_labels = []
    res_name_map = {r.id: r.name or r.id for r in project.resources}
    for rid in res_ids:
        name = res_name_map.get(rid, rid)
        res_labels.append(f"{rid}" if name == rid else f"{rid} ({name})")

    ax.set_yticks(list(range(n - 1, -1, -1)))
    ax.set_yticklabels(res_labels, fontsize=8)
    ax.set_xlabel(result.time_unit, fontsize=9)
    ax.set_title("Ressourcenauslastung", fontsize=11, fontweight="bold")
    ax.set_xlim(left=0)
    ax.grid(axis="x", alpha=0.3, linestyle="--")

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def load_png_as_dpg_texture(png_bytes: bytes, tag: str) -> bool:
    """Lädt PNG-Bytes als DPG Static Texture.

    Args:
        png_bytes: PNG-Bilddaten
        tag: DPG-Tag für die Texture
    Returns:
        True bei Erfolg
    """
    import dearpygui.dearpygui as dpg
    from PIL import Image
    from io import BytesIO

    try:
        img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        w, h = img.size
        data = list(img.tobytes())
        # Normalisiere auf 0.0–1.0 float
        float_data = [v / 255.0 for v in data]

        # Alte Texture entfernen
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)

        # Texture Registry erstellen falls nötig
        if not dpg.does_item_exist("_chart_tex_registry"):
            dpg.add_texture_registry(tag="_chart_tex_registry")

        dpg.add_static_texture(
            width=w, height=h,
            default_value=float_data,
            tag=tag,
            parent="_chart_tex_registry",
        )
        return True
    except Exception:
        return False
