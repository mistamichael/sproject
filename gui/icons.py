"""
Icon-Toolbar-Unterstützung (Dear PyGui)
========================================

Lädt PNG-Dateien aus gui/images/ und registriert sie als statische DPG-Texturen.
Falls eine PNG fehlt oder nicht geladen werden kann, wird ein farbiger
Platzhalter-Textur aus rohen RGBA-Werten erzeugt (kein Fallback auf Text nötig).

Verwendung in app.py:
    from gui.icons import setup_icon_textures, add_icon_button
    setup_icon_textures()          # einmalig nach dpg.create_context()
    btn = add_icon_button("open", "Öffnen", callback=...)
"""

from pathlib import Path
import dearpygui.dearpygui as dpg

ICON_SIZE = 32   # erwartete Pixelgröße

# Dateiname → Fallback-RGB-Farbe (wenn PNG fehlt oder unlesbar)
_ICONS: dict[str, tuple[int, int, int]] = {
    "open":      ( 80, 140, 200),
    "save":      ( 80, 180, 100),
    "save_as":   ( 60, 185, 170),
    "export":    (220, 150,  55),
    "calculate": (155,  80, 205),
}

_IMAGES_DIR = Path(__file__).parent / "images"
_loaded: bool = False


# ---------------------------------------------------------------------------
# Interne Helfer
# ---------------------------------------------------------------------------

def _solid_rgba_floats(r: int, g: int, b: int, size: int = ICON_SIZE) -> list[float]:
    """Erstellt eine flache RGBA-Float-Liste für ein einfarbiges Bild (0–1)."""
    pixel = [r / 255.0, g / 255.0, b / 255.0, 0.90]
    return pixel * (size * size)


def _load_texture(name: str, fallback_rgb: tuple[int, int, int]) -> tuple[int, int, list]:
    """
    Versucht gui/images/{name}.png zu laden.
    Bei Misserfolg: farbigen Platzhalter zurückgeben.
    Gibt (width, height, rgba_float_list) zurück.
    """
    path = _IMAGES_DIR / f"{name}.png"
    if path.exists() and path.stat().st_size > 0:
        try:
            w, h, _channels, data = dpg.load_image(str(path))
            return w, h, data
        except Exception as exc:
            print(f"[icons] Kann {path.name} nicht laden: {exc}")
    # Platzhalter
    return ICON_SIZE, ICON_SIZE, _solid_rgba_floats(*fallback_rgb)


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def setup_icon_textures() -> None:
    """
    Lädt alle Icons und registriert sie als statische DPG-Texturen.
    Muss einmalig nach dpg.create_context() aufgerufen werden,
    bevor Widgets erstellt werden.
    """
    global _loaded
    with dpg.texture_registry(tag="icon_tex_registry"):
        for name, fallback in _ICONS.items():
            w, h, data = _load_texture(name, fallback)
            dpg.add_static_texture(
                width=w,
                height=h,
                default_value=data,
                tag=f"icon_tex_{name}",
            )
    _loaded = True


def add_icon_button(
    name: str,
    tooltip: str,
    callback,
    tag: str = "",
    enabled: bool = True,
) -> int | str:
    """
    Fügt einen 32×32-Bild-Button in die aktuelle DPG-Gruppe ein.

    Args:
        name:     Schlüssel aus _ICONS (z. B. "open", "save")
        tooltip:  Text im Hover-Tooltip
        callback: DPG-Callback
        tag:      Optionaler eindeutiger DPG-Tag
        enabled:  Button aktiv/inaktiv

    Returns:
        DPG-Item-Tag des erstellten Buttons
    """
    tex_tag = f"icon_tex_{name}"
    kwargs: dict = {"callback": callback, "enabled": enabled}
    if tag:
        kwargs["tag"] = tag

    if _loaded and dpg.does_item_exist(tex_tag):
        btn = dpg.add_image_button(
            tex_tag,
            width=ICON_SIZE,
            height=ICON_SIZE,
            **kwargs,
        )
    else:
        # Fallback: Text-Button mit Emoji
        _emoji = {"open": "📂", "save": "💾", "save_as": "📄",
                  "export": "⬇", "calculate": "▶"}
        btn = dpg.add_button(
            label=_emoji.get(name, "?"),
            width=ICON_SIZE + 4,
            height=ICON_SIZE + 4,
            **kwargs,
        )

    if tooltip:
        with dpg.tooltip(btn):
            dpg.add_text(tooltip)

    return btn
