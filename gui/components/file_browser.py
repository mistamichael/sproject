"""
Eigener Datei-Browser-Dialog (Dear PyGui)
==========================================

Explorer-Sortierung:
  1.  ..  (übergeordnetes Verzeichnis)
  2.  Unterverzeichnisse (alphabetisch, Groß-/Kleinschreibung ignoriert)
  3.  Dateien             (alphabetisch)

OK- und Abbrechen-Buttons sind doppelt so hoch wie Standard-Buttons.
"""

from pathlib import Path
from typing import Callable, Optional
import dearpygui.dearpygui as dpg

from gui.gui_config import load_gui_config

_CFG = load_gui_config()
_COL = _CFG.section("colors")
_FB_SEC = "dialog.file_browser"
_FB  = _CFG.section(_FB_SEC)

_WIN_TAG     = "fb_window"
_LIST_TAG    = "fb_list"
_PATH_TAG    = "fb_path_input"
_NAME_TAG    = "fb_filename_input"
_BTN_H       = _FB.get("button_height", 38)
_BTN_W       = _FB.get("button_width", 160)


class _FileBrowser:
    """Zustandshalter für einen offenen Datei-Browser-Dialog."""

    def __init__(
        self,
        callback: Callable[[Path], None],
        start_path: Path,
        title: str,
        file_ext: str,
    ) -> None:
        self.callback    = callback
        self.ext         = file_ext.lower()
        self.title       = title
        # Startpfad: immer ein Verzeichnis
        p = start_path.resolve()
        self.current_dir = p if p.is_dir() else p.parent
        self._build()

    # ------------------------------------------------------------------
    # Verzeichnis-Listing
    # ------------------------------------------------------------------

    def _list_entries(self) -> tuple[list[Path], list[Path]]:
        """Gibt (dirs, files) zurück; Dateien nach ext gefiltert."""
        try:
            entries = list(self.current_dir.iterdir())
        except (PermissionError, OSError):
            return [], []
        dirs = sorted(
            [e for e in entries if e.is_dir()],
            key=lambda x: x.name.lower(),
        )
        files = sorted(
            [
                e for e in entries
                if e.is_file()
                and (not self.ext or e.suffix.lower() == self.ext)
            ],
            key=lambda x: x.name.lower(),
        )
        return dirs, files

    # ------------------------------------------------------------------
    # Liste neu aufbauen
    # ------------------------------------------------------------------

    def _rebuild_list(self) -> None:
        if not dpg.does_item_exist(_LIST_TAG):
            return
        dpg.delete_item(_LIST_TAG, children_only=True)

        if dpg.does_item_exist(_PATH_TAG):
            dpg.set_value(_PATH_TAG, str(self.current_dir))

        dirs, files = self._list_entries()
        parent = self.current_dir.parent

        # ".." – Elternverzeichnis (nur wenn nicht Wurzel)
        if parent != self.current_dir:
            dpg.add_button(
                label="📁   ..",
                width=-1,
                parent=_LIST_TAG,
                callback=lambda s, a, u: self._navigate(u),
                user_data=parent,
            )

        # Unterverzeichnisse
        for d in dirs:
            dpg.add_button(
                label=f"📁   {d.name}",
                width=-1,
                parent=_LIST_TAG,
                callback=lambda s, a, u: self._navigate(u),
                user_data=d,
            )

        # Trennlinie
        if (dirs or parent != self.current_dir) and files:
            dpg.add_separator(parent=_LIST_TAG)

        # Dateien
        for f in files:
            dpg.add_button(
                label=f"📄   {f.name}",
                width=-1,
                parent=_LIST_TAG,
                callback=lambda s, a, u: self._select_file(u),
                user_data=f.name,
            )

        if not dirs and not files and parent == self.current_dir:
            dpg.add_text(
                "(Verzeichnis ist leer)",
                parent=_LIST_TAG,
                color=_COL.get("empty_text", (140, 140, 150)),
            )

    # ------------------------------------------------------------------
    # Interaktion
    # ------------------------------------------------------------------

    def _navigate(self, path: Path) -> None:
        self.current_dir = path.resolve()
        self._rebuild_list()
        # Dateiname-Feld leeren beim Verzeichniswechsel
        if dpg.does_item_exist(_NAME_TAG):
            dpg.set_value(_NAME_TAG, "")

    def _navigate_from_input(self, raw: str) -> None:
        p = Path(raw.strip())
        if p.is_dir():
            self._navigate(p)
        elif p.parent.is_dir():
            self._navigate(p.parent)
            if dpg.does_item_exist(_NAME_TAG):
                dpg.set_value(_NAME_TAG, p.name)

    def _select_file(self, name: str) -> None:
        if dpg.does_item_exist(_NAME_TAG):
            dpg.set_value(_NAME_TAG, name)

    def _confirm(self) -> None:
        name = (dpg.get_value(_NAME_TAG) if dpg.does_item_exist(_NAME_TAG) else "").strip()
        if not name:
            return
        # Wenn kein Suffix angegeben und ext gesetzt → Suffix ergänzen
        p = Path(name)
        if self.ext and not p.suffix:
            name = name + self.ext
        path = self.current_dir / name
        if dpg.does_item_exist(_WIN_TAG):
            dpg.delete_item(_WIN_TAG)
        self.callback(path)

    def _cancel(self) -> None:
        if dpg.does_item_exist(_WIN_TAG):
            dpg.delete_item(_WIN_TAG)

    # ------------------------------------------------------------------
    # Fenster aufbauen
    # ------------------------------------------------------------------

    def _build(self) -> None:
        if dpg.does_item_exist(_WIN_TAG):
            dpg.delete_item(_WIN_TAG)

        with dpg.window(
            label=self.title,
            tag=_WIN_TAG,
            modal=True,
            width=_CFG.resolve(_FB_SEC, "width", 660),
            height=_CFG.resolve(_FB_SEC, "height", 500),
            pos=[_CFG.resolve(_FB_SEC, "pos_x", 280), _CFG.resolve(_FB_SEC, "pos_y", 120)],
            no_resize=False,
        ):
            # ── Pfad-Zeile ──────────────────────────────────────────────
            with dpg.group(horizontal=True):
                dpg.add_text("Pfad:", color=_COL.get("path_label", (180, 180, 200)))
                dpg.add_input_text(
                    tag=_PATH_TAG,
                    default_value=str(self.current_dir),
                    width=-60,
                    hint="Verzeichnispfad",
                    on_enter=True,
                    callback=lambda s, v: self._navigate_from_input(v),
                )
                dpg.add_button(
                    label="↑ Hoch",
                    width=55,
                    callback=lambda: self._navigate(self.current_dir.parent),
                )

            dpg.add_spacer(height=4)

            # ── Datei-Liste ─────────────────────────────────────────────
            with dpg.child_window(tag=_LIST_TAG, height=_CFG.resolve(_FB_SEC, "list_height", 340), border=True):
                pass  # wird durch _rebuild_list() befüllt

            dpg.add_spacer(height=6)

            # ── Dateiname-Eingabe ────────────────────────────────────────
            with dpg.group(horizontal=True):
                dpg.add_text("Dateiname:", color=_COL.get("path_label", (180, 180, 200)))
                dpg.add_input_text(
                    tag=_NAME_TAG,
                    default_value="",
                    width=-1,
                    hint="Datei auswählen oder Namen eingeben …",
                    on_enter=True,
                    callback=lambda s, v: self._confirm(),
                )

            dpg.add_spacer(height=10)

            # ── Aktions-Buttons (doppelte Höhe) ─────────────────────────
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="  ✔  Öffnen  ",
                    height=_BTN_H,
                    width=_BTN_W,
                    callback=lambda: self._confirm(),
                )
                dpg.add_spacer(width=12)
                dpg.add_button(
                    label="  ✕  Abbrechen  ",
                    height=_BTN_H,
                    width=_BTN_W,
                    callback=lambda: self._cancel(),
                )

        # Liste initial füllen (nach dem Fenster, damit fb_list existiert)
        self._rebuild_list()


# ---------------------------------------------------------------------------
# Öffentliche Funktion
# ---------------------------------------------------------------------------

def open_file_browser(
    callback: Callable[[Path], None],
    start_path: Optional[Path] = None,
    title: str = "Datei öffnen",
    file_ext: str = ".json",
) -> None:
    """
    Öffnet den Datei-Browser-Dialog.

    Args:
        callback:   Wird mit dem gewählten Path aufgerufen.
        start_path: Startverzeichnis (default: CWD).
        title:      Fenstertitel.
        file_ext:   Dateiendung-Filter (z.B. ".json", "" = alle).
    """
    _FileBrowser(
        callback=callback,
        start_path=(start_path or Path.cwd()),
        title=title,
        file_ext=file_ext,
    )
