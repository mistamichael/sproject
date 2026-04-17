"""
GUI-Konfiguration laden (cfg/gui.cfg)
======================================

Liest cfg/gui.cfg (ConfigParser-Format) und stellt die Werte als
einfaches dict-artiges Objekt bereit.  Farbwerte werden als Tupel
geparst, numerische Werte als int/float.
"""

import configparser
import os
from pathlib import Path


def _parse_color(value: str) -> tuple:
    """'30, 32, 38' → (30, 32, 38)  oder  '220, 80, 80, 80' → (220, 80, 80, 80)."""
    parts = [int(x.strip()) for x in value.split(",")]
    return tuple(parts)


def _parse_int(value: str) -> int:
    return int(value.strip())


def _parse_float(value: str) -> float:
    return float(value.strip())


def _parse_font_ranges(value: str) -> list:
    """Parst '0x00C0, 0x00FF, 0x2000, 0x206F, ...' → [(0x00C0, 0x00FF), ...]."""
    tokens = [t.strip().rstrip(",") for t in value.split() if t.strip().rstrip(",")]
    nums = [int(t, 16) for t in tokens]
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


# Sections deren Werte komplett als Farb-Tupel gelesen werden
_COLOR_SECTIONS = {"dark_theme", "light_theme", "solarized_theme", "colors"}

# Sections deren Werte als int/float gelesen werden
_NUMERIC_SECTIONS = {
    "base", "style", "viewport", "layout",
    "dialog.save", "dialog.export", "dialog.about",
    "dialog.file_browser", "dialog.successor_add", "dialog.successor_add_empty",
    "dialog.successor_remove", "dialog.successor_remove_empty",
    "dialog.resource_picker", "dialog.resource_picker_empty",
    "autocomplete",
    "task_table", "stammdaten_table", "resources_table",
    "persons_table", "resting_times_table", "result_table",
    "successor_dialog_table",
}


class GuiConfig:
    """Hält die geparsten GUI-Konfigurationswerte."""

    def __init__(self, cfg_path: Path | None = None):
        self._cp = configparser.ConfigParser()

        if cfg_path is None:
            pv_cfg = os.environ.get("PV_CFG", "")
            if pv_cfg:
                cfg_path = Path(pv_cfg) / "gui.cfg"
            else:
                cfg_path = Path(__file__).resolve().parent.parent / "cfg" / "gui.cfg"

        if cfg_path.exists():
            self._cp.read(str(cfg_path), encoding="utf-8")

        self._data: dict = {}
        self._parse_all()

    def _parse_all(self) -> None:
        for section in self._cp.sections():
            self._data[section] = {}
            for key, raw in self._cp.items(section):
                if section in _COLOR_SECTIONS:
                    self._data[section][key] = _parse_color(raw)
                elif section == "font" and key == "ranges":
                    self._data[section][key] = _parse_font_ranges(raw)
                elif section == "font" and key == "size":
                    self._data[section][key] = _parse_int(raw)
                elif section == "font" and key == "path":
                    self._data[section][key] = raw.strip()
                elif section in _NUMERIC_SECTIONS:
                    try:
                        self._data[section][key] = _parse_int(raw)
                    except ValueError:
                        try:
                            self._data[section][key] = _parse_float(raw)
                        except ValueError:
                            self._data[section][key] = raw.strip()
                else:
                    self._data[section][key] = raw.strip()

    @property
    def base_width(self) -> int:
        """Referenz-Viewport-Breite aus [base]."""
        return self._data.get("base", {}).get("viewport_width", 1280)

    @property
    def base_height(self) -> int:
        """Referenz-Viewport-Hoehe aus [base]."""
        return self._data.get("base", {}).get("viewport_height", 860)

    def get(self, section: str, key: str, default=None):
        """Holt einen Wert: cfg.get('viewport', 'width', 1280)."""
        return self._data.get(section, {}).get(key, default)

    def resolve(self, section: str, key: str, default: int = 0) -> int:
        """Loest _pct Werte gegen die Basis-Viewport-Groesse auf.

        Sucht zuerst nach key_pct (Prozentwert), rechnet gegen [base] um.
        Breite/pos_x -> base_width, Hoehe/pos_y -> base_height.
        Fallback auf absoluten key (Pixelwert).

        Beispiel: resolve('dialog.save', 'width') sucht width_pct,
        findet 40.6, rechnet 40.6% * 1280 = 520.
        """
        sec = self._data.get(section, {})
        pct_key = f"{key}_pct"
        if pct_key in sec:
            pct = sec[pct_key]
            if key in ("width", "pos_x", "sidebar_width", "min_width"):
                return int(self.base_width * pct / 100.0)
            else:
                return int(self.base_height * pct / 100.0)
        if key in sec:
            return int(sec[key])
        return default

    def section(self, name: str) -> dict:
        """Gibt die gesamte Sektion als dict zurueck."""
        return self._data.get(name, {})

    @property
    def active_theme(self) -> str:
        return self.get("theme", "active", "dark_theme")

    def theme_colors(self) -> dict:
        """Gibt die Farben des aktiven Themes zurueck."""
        return self.section(self.active_theme)


# Singleton – wird beim ersten Import erzeugt
_instance: GuiConfig | None = None


def load_gui_config(cfg_path: Path | None = None) -> GuiConfig:
    """Laedt die GUI-Config (einmalig, cached)."""
    global _instance
    if _instance is None:
        _instance = GuiConfig(cfg_path)
    return _instance
