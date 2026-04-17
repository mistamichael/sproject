"""
GUI-Konfiguration laden (cfg/gui.cfg)
======================================

Liest cfg/gui.cfg (ConfigParser-Format) und stellt die Werte als
einfaches dict-artiges Objekt bereit.  Farbwerte werden als Tupel
geparst, numerische Werte als int/float.

Theme-Dateien werden aus dem Verzeichnis PV_THEMES (bzw. cfg/themes/)
als einzelne .cfg-Dateien geladen.
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
_COLOR_SECTIONS = {"colors"}

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

        self._cfg_path: Path = cfg_path

        if cfg_path.exists():
            self._cp.read(str(cfg_path), encoding="utf-8")

        self._data: dict = {}
        self._themes: dict[str, dict] = {}
        self._parse_all()
        self._load_themes()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Themes aus Einzeldateien laden
    # ------------------------------------------------------------------

    @property
    def _themes_dir(self) -> Path:
        """Verzeichnis mit Theme-Dateien (PV_THEMES oder cfg/themes/)."""
        pv_themes = os.environ.get("PV_THEMES", "")
        if pv_themes:
            return Path(pv_themes)
        return self._cfg_path.parent / "themes"

    def _load_themes(self) -> None:
        """Laedt alle .cfg-Dateien aus dem Themes-Verzeichnis."""
        themes_dir = self._themes_dir
        if not themes_dir.exists():
            return
        for cfg_file in sorted(themes_dir.glob("*.cfg")):
            name = cfg_file.stem  # z.B. "dark", "light", "solarized_dark"
            cp = configparser.ConfigParser()
            cp.read(str(cfg_file), encoding="utf-8")
            if cp.has_section("theme"):
                self._themes[name] = {
                    k: _parse_color(v) for k, v in cp.items("theme")
                }

    # ------------------------------------------------------------------
    # Basis-Properties
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Theme-API
    # ------------------------------------------------------------------

    @property
    def active_theme(self) -> str:
        """Name des aktiven Themes (Dateiname ohne .cfg)."""
        return self.get("theme", "active", "default")

    def theme_colors(self) -> dict:
        """Gibt die Farben des aktiven Themes zurueck."""
        name = self.active_theme
        if name in self._themes:
            return self._themes[name]
        # Fallback auf 'default'
        return self._themes.get("default", {})

    def available_themes(self) -> list[str]:
        """Gibt die Namen aller verfuegbaren Themes zurueck (sortiert)."""
        return sorted(self._themes.keys())

    def set_active_theme(self, theme_name: str) -> None:
        """Setzt das aktive Theme in-memory und speichert in gui.cfg."""
        self._data.setdefault("theme", {})["active"] = theme_name
        self._save_setting("theme", "active", theme_name)

    # ------------------------------------------------------------------
    # Sprache
    # ------------------------------------------------------------------

    @property
    def active_language(self) -> str:
        """Aktive Sprache aus [language]."""
        return self.get("language", "active", "de")

    def set_active_language(self, lang: str) -> None:
        """Setzt die aktive Sprache in-memory und speichert in gui.cfg."""
        self._data.setdefault("language", {})["active"] = lang
        self._save_setting("language", "active", lang)

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------

    def _save_setting(self, section: str, key: str, value: str) -> None:
        """Aktualisiert einen einzelnen Wert in gui.cfg auf der Festplatte."""
        if not self._cfg_path or not self._cfg_path.exists():
            return
        lines = self._cfg_path.read_text(encoding="utf-8").splitlines(keepends=True)
        in_section = False
        key_found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                if in_section and not key_found:
                    lines.insert(i, f"{key} = {value}\n")
                    key_found = True
                    break
                in_section = stripped == f"[{section}]"
            elif in_section and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k == key:
                    lines[i] = f"{key} = {value}\n"
                    key_found = True
                    break
        if not key_found:
            if in_section:
                lines.append(f"{key} = {value}\n")
            else:
                lines.append(f"\n[{section}]\n{key} = {value}\n")
        self._cfg_path.write_text("".join(lines), encoding="utf-8")


# Singleton – wird beim ersten Import erzeugt
_instance: GuiConfig | None = None


def load_gui_config(cfg_path: Path | None = None) -> GuiConfig:
    """Laedt die GUI-Config (einmalig, cached)."""
    global _instance
    if _instance is None:
        _instance = GuiConfig(cfg_path)
    return _instance
