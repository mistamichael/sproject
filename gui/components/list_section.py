"""
ListSection – bearbeitbare Tabelle für eine Liste von Modell-Objekten
=====================================================================

Eine Sektion beschreibt nur ihre Spalten (Column). ListSection übernimmt:

- refresh(): Modell → Widgets (Tabelle neu aufbauen)
- sync():    Widgets → Modell (bearbeitete Werte zurückschreiben)
- Enter springt in dieselbe Spalte der nächsten Zeile, "X" entfernt eine Zeile

open_form_dialog() baut den passenden modalen "Hinzufügen"-Dialog.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union

import dearpygui.dearpygui as dpg

from gui.gui_config import load_gui_config
from gui.i18n import t
from lib.colors import hex_to_rgb, rgb_to_hex

_COLORS = load_gui_config().section("colors")
_EMPTY_COLOR = (160, 160, 170)

Getter = Callable[[Any], str]
Setter = Callable[[Any, str], None]


@dataclass
class Column:
    """
    Spalte einer ListSection.

    key:      Attributname am Zeilen-Objekt (Default für get/set) und Teil des Widget-Tags
    label:    i18n-Key der Überschrift
    width:    feste Breite in Pixel, None = dehnbar
    editable: False → nur Anzeige (z. B. IDs, auf die andere Objekte verweisen)
    items:    gesetzt → Combo-Box statt Textfeld
    color:    Hex-Farbe (RRGGBB) → Farbfeld vor dem Textfeld; Klick darauf oder
              Doppelklick ins Textfeld öffnet die Farbauswahl
    get/set:  eigene Umwandlung Objekt ↔ Text (Default: getattr/setattr als str)
    text_color: optional Zeilen-Objekt → RGB nur für diese Spalte (z. B. Warnung)
    """
    key: str
    label: str
    width: Optional[int] = None
    editable: bool = True
    items: Sequence[str] = ()
    color: bool = False
    get: Optional[Getter] = None
    set: Optional[Setter] = None
    text_color: Optional[Callable[[Any], Optional[Tuple[int, int, int]]]] = None

    def read(self, obj: Any) -> str:
        if self.get:
            return self.get(obj)
        value = getattr(obj, self.key)
        return "" if value is None else str(value)

    def write(self, obj: Any, text: str) -> None:
        if self.set:
            self.set(obj, text)
        else:
            setattr(obj, self.key, text or None)


def float_setter(key: str) -> Setter:
    """Setter für Zahlenfelder: ungültige Eingaben lassen den alten Wert stehen."""
    def _set(obj: Any, text: str) -> None:
        try:
            setattr(obj, key, float(text))
        except ValueError:
            pass
    return _set


def _focus_next(sender, app_data, user_data) -> None:
    if user_data and dpg.does_item_exist(user_data):
        dpg.focus_item(user_data)


# ---------------------------------------------------------------------------
# Farbauswahl
# ---------------------------------------------------------------------------

_COLOR_DIALOG = "color_picker_dialog"
_SWATCH_FALLBACK = (128, 128, 128)


def _parse_hex(text: str) -> Optional[Tuple[int, int, int]]:
    """'4472C4' oder '#4472C4' → (R, G, B); ungültig → None."""
    text = (text or "").strip().lstrip("#")
    if len(text) != 6:
        return None
    try:
        return hex_to_rgb(text)
    except ValueError:
        return None


def _swatch_tag(input_tag: str) -> str:
    return f"{input_tag}_swatch"


def open_color_dialog(input_tag: str, on_change: Optional[Callable[[], None]] = None) -> None:
    """Modaler Farbwähler; OK schreibt die Farbe als Hex (ohne #) ins Textfeld input_tag."""
    if dpg.does_item_exist(_COLOR_DIALOG):
        dpg.delete_item(_COLOR_DIALOG)
    rgb = _parse_hex(dpg.get_value(input_tag)) or _SWATCH_FALLBACK

    def _confirm() -> None:
        r, g, b = (int(round(v)) for v in dpg.get_value(f"{_COLOR_DIALOG}_picker")[:3])
        dpg.delete_item(_COLOR_DIALOG)
        dpg.set_value(input_tag, rgb_to_hex((r, g, b)))
        if dpg.does_item_exist(_swatch_tag(input_tag)):
            dpg.set_value(_swatch_tag(input_tag), (r, g, b, 255))
        if on_change:
            on_change()

    with dpg.window(label=t("dlg.pick_color"), tag=_COLOR_DIALOG, modal=True,
                    no_resize=True, autosize=True, pos=[450, 200]):
        dpg.add_color_picker(tag=f"{_COLOR_DIALOG}_picker", default_value=(*rgb, 255),
                             no_alpha=True, display_hex=True, display_rgb=True, width=260)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(label=t("button.ok"), width=80, callback=_confirm)
            dpg.add_button(label=t("button.cancel"), width=80,
                           callback=lambda: dpg.delete_item(_COLOR_DIALOG))


class ListSection:
    """
    Args:
        tag:        Parent-Container (DPG-Group) und Präfix der Widget-Tags
        columns:    Spalten
        get_rows:   liefert die aktuellen Zeilen-Objekte
        on_remove:  Index → Zeile entfernen (danach refresh durch den Aufrufer)
        empty_text: i18n-Key für "keine Einträge"
        text_color: optional Zeilen-Objekt → RGB für die Textfarbe
        on_change:  optional, nach Auswahl im Farbwähler (z. B. Modell syncen + neu aufbauen)
        on_double_click: optional, Index → Zeile bearbeiten (Doppelklick auf eine Zelle)
        warning:    optional, liefert einen Warnhinweis unter der Tabelle (None = keiner)
    """

    def __init__(self, tag: str, columns: List[Column],
                 get_rows: Callable[[], List[Any]],
                 on_remove: Callable[[int], None],
                 empty_text: str,
                 text_color: Optional[Callable[[Any], Optional[Tuple[int, int, int]]]] = None,
                 on_change: Optional[Callable[[], None]] = None,
                 on_double_click: Optional[Callable[[int], None]] = None,
                 warning: Optional[Callable[[], Optional[str]]] = None):
        self.tag = tag
        self.columns = columns
        self.get_rows = get_rows
        self.on_remove = on_remove
        self.empty_text = empty_text
        self.text_color = text_color
        self.on_change = on_change
        self.on_double_click = on_double_click
        self.warning = warning
        self._themes: Dict[Tuple[int, int, int], int] = {}
        self._color_handler: Optional[Union[int, str]] = None
        self._row_handler: Optional[Union[int, str]] = None
        self._row_of_item: Dict[Union[int, str], int] = {}
        self._shown_rows: List[Any] = []

    @property
    def shown_rows(self) -> List[Any]:
        """Die Zeilen-Objekte, aus denen die Tabelle zuletzt aufgebaut wurde."""
        return self._shown_rows

    def _widget_tag(self, row_idx: int, key: str) -> str:
        return f"{self.tag}_{row_idx}_{key}"

    def _color_theme(self, rgb: Tuple[int, int, int]) -> int:
        if rgb not in self._themes:
            with dpg.theme() as theme:
                with dpg.theme_component(dpg.mvInputText):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, [*rgb, 255])
            self._themes[rgb] = theme
        return self._themes[rgb]

    def _color_dblclick_handler(self) -> Union[int, str]:
        """Ein Handler für alle Farb-Textfelder der Sektion (überlebt refresh())."""
        if self._color_handler is None:
            registry = dpg.add_item_handler_registry()
            dpg.add_item_double_clicked_handler(
                parent=registry,
                callback=lambda s, a: open_color_dialog(dpg.get_item_alias(a[1]) or a[1],
                                                        self.on_change))
            self._color_handler = registry
        return self._color_handler

    def _row_dblclick_handler(self) -> Union[int, str]:
        """Ein Handler für alle Zellen der Sektion; die Zeile kommt aus _row_of_item."""
        if self._row_handler is None:
            registry = dpg.add_item_handler_registry()
            dpg.add_item_double_clicked_handler(parent=registry, callback=self._on_row_double_click)
            self._row_handler = registry
        return self._row_handler

    def _on_row_double_click(self, sender, app_data) -> None:
        item = app_data[1]
        row = self._row_of_item.get(item, self._row_of_item.get(dpg.get_item_alias(item)))
        if row is not None and self.on_double_click:
            self.on_double_click(row)

    def refresh(self) -> None:
        """Baut die Tabelle aus den aktuellen Zeilen-Objekten neu auf."""
        if not dpg.does_item_exist(self.tag):
            return
        dpg.delete_item(self.tag, children_only=True)
        rows = self._shown_rows = list(self.get_rows())
        self._row_of_item = {}

        if not rows:
            dpg.add_text(t(self.empty_text), parent=self.tag, color=_EMPTY_COLOR)
            return

        with dpg.table(parent=self.tag, header_row=True, resizable=True, row_background=True,
                       borders_outerH=True, borders_innerV=True, borders_outerV=True):
            for col in self.columns:
                if col.width:
                    dpg.add_table_column(label=t(col.label), width_fixed=True, init_width_or_weight=col.width)
                else:
                    dpg.add_table_column(label=t(col.label), width_stretch=True)
            dpg.add_table_column(label="X", width_fixed=True, init_width_or_weight=32)

            for i, obj in enumerate(rows):
                rgb = self.text_color(obj) if self.text_color else None
                with dpg.table_row():
                    for col in self.columns:
                        widget = self._add_cell(i, len(rows), obj, col, rgb)
                        if widget is not None and self.on_double_click:
                            self._row_of_item[widget] = i
                            dpg.bind_item_handler_registry(widget, self._row_dblclick_handler())
                    dpg.add_button(label="X", width=-1, user_data=i,
                                   callback=lambda s, a, u: self.on_remove(u))

        message = self.warning() if self.warning else None
        if message:
            dpg.add_text(message, parent=self.tag, tag=f"{self.tag}_warning", wrap=0,
                         color=_COLORS.get("error_text", (255, 80, 80)))

    def _add_cell(self, i: int, n: int, obj: Any, col: Column, rgb) -> Optional[Union[int, str]]:
        """Legt die Zelle an; liefert das Widget für den Zeilen-Doppelklick (Farbzellen: None)."""
        value = col.read(obj)
        col_rgb = col.text_color(obj) if col.text_color else None
        if not col.editable:
            text = dpg.add_text(value or "–")
            if col_rgb:
                dpg.configure_item(text, color=(*col_rgb, 255))
            return text
        rgb = col_rgb or rgb
        tag = self._widget_tag(i, col.key)
        if col.items:
            return dpg.add_combo(tag=tag, items=list(col.items), default_value=value, width=-1)
        next_tag = self._widget_tag(i + 1, col.key) if i + 1 < n else None
        if col.color:
            self._add_color_cell(tag, value, next_tag)
            return None
        widget = dpg.add_input_text(tag=tag, default_value=value, width=-1, on_enter=True,
                                    callback=_focus_next, user_data=next_tag)
        if rgb:
            dpg.bind_item_theme(widget, self._color_theme(rgb))
        return widget

    def _add_color_cell(self, tag: str, value: str, next_tag: Optional[str]) -> None:
        """Farbfeld + Hex-Textfeld; Klick aufs Farbfeld oder Doppelklick ins Textfeld → Farbwähler."""
        with dpg.group(horizontal=True, horizontal_spacing=4):
            swatch = dpg.add_color_button(tag=_swatch_tag(tag),
                                          default_value=(*(_parse_hex(value) or _SWATCH_FALLBACK), 255),
                                          no_alpha=True, width=20, height=20,
                                          callback=lambda: open_color_dialog(tag, self.on_change))
            with dpg.tooltip(swatch):
                dpg.add_text(t("tooltip.pick_color"))
            dpg.add_input_text(tag=tag, default_value=value, width=-1, on_enter=True,
                               callback=_focus_next, user_data=next_tag)
        dpg.bind_item_handler_registry(tag, self._color_dblclick_handler())

    def sync(self) -> bool:
        """Schreibt geänderte Widget-Werte ins Modell. True, wenn sich etwas geändert hat."""
        changed = False
        for i, obj in enumerate(self._shown_rows):
            for col in self.columns:
                tag = self._widget_tag(i, col.key)
                if not col.editable or not dpg.does_item_exist(tag):
                    continue
                text = (dpg.get_value(tag) or "").strip()
                if text != col.read(obj):
                    col.write(obj, text)
                    changed = True
        return changed


# ---------------------------------------------------------------------------
# Hinzufügen-Dialog
# ---------------------------------------------------------------------------

@dataclass
class FormField:
    key: str
    label: str                    # i18n-Key
    default: str = ""
    items: Sequence[str] = ()     # gesetzt → Combo-Box
    hint: str = ""
    no_spaces: bool = False


@dataclass
class _Form:
    tag: str
    fields: List[FormField] = field(default_factory=list)

    def values(self) -> Dict[str, str]:
        return {
            f.key: (dpg.get_value(f"{self.tag}_{f.key}") or "").strip()
            for f in self.fields if dpg.does_item_exist(f"{self.tag}_{f.key}")
        }


def open_form_dialog(tag: str, title: str, fields: List[FormField],
                     on_confirm: Callable[[Dict[str, str]], None],
                     width: int = 380, confirm_label: str = "button.add") -> None:
    """Modaler Dialog mit einem Eingabefeld je FormField; on_confirm erhält {key: Text}."""
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
    form = _Form(tag, fields)

    def _confirm() -> None:
        values = form.values()
        dpg.delete_item(tag)
        on_confirm(values)

    with dpg.window(label=t(title), tag=tag, modal=True, width=width,
                    height=90 + 30 * len(fields), pos=[450, 300], no_resize=True):
        with dpg.table(header_row=False, borders_outerH=False, borders_outerV=False,
                       borders_innerV=False, policy=dpg.mvTable_SizingFixedFit):
            dpg.add_table_column(width_fixed=True, init_width_or_weight=110)
            dpg.add_table_column(width_stretch=True)
            for f in fields:
                with dpg.table_row():
                    dpg.add_text(t(f.label))
                    if f.items:
                        dpg.add_combo(tag=f"{tag}_{f.key}", items=list(f.items),
                                      default_value=f.default, width=-1)
                    else:
                        dpg.add_input_text(tag=f"{tag}_{f.key}", default_value=f.default,
                                           hint=f.hint, no_spaces=f.no_spaces, width=-1)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_button(label=t(confirm_label), callback=_confirm)
            dpg.add_button(label=t("button.cancel"), callback=lambda: dpg.delete_item(tag))


def show_error(parent: str, message: str) -> None:
    """Fehlermeldung unter einer Tabelle (verschwindet beim nächsten refresh)."""
    if dpg.does_item_exist(parent):
        dpg.add_text(message, parent=parent, color=_COLORS.get("error_text", (255, 80, 80)))
