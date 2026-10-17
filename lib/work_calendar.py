"""
Work calendar
=============

Einzige Stelle, die entscheidet, ob ein Tag ein Arbeitstag ist, und die
CPM-Arbeitstage in Kalenderdaten umrechnet.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Tuple

_FAR_FUTURE = datetime(9999, 12, 31)
_FAR_PAST = datetime(1900, 1, 1)


@dataclass(frozen=True)
class WorkCalendar:
    """
    Arbeitskalender: Wochenenden und Feiertage.

    Attributes:
        skip_weekends: Samstag/Sonntag sind arbeitsfrei
        holidays:      arbeitsfreie Tage im Format 'YYYY-MM-DD'
    """
    skip_weekends: bool = True
    holidays: FrozenSet[str] = frozenset()
    day_start_hour: float = 8.0      # Arbeitsbeginn (aus [WorkingHours] morning_shift)

    def interruption_reason(self, day: datetime) -> Optional[str]:
        """'weekend', 'holiday' oder None für einen Arbeitstag."""
        if self.skip_weekends and day.weekday() >= 5:
            return 'weekend'
        if self.holidays and day.strftime('%Y-%m-%d') in self.holidays:
            return 'holiday'
        return None

    def is_working_day(self, day: datetime) -> bool:
        return self.interruption_reason(day) is None

    def next_work_start(self, now: datetime) -> datetime:
        """Arbeitsbeginn am Tag von now bzw. am nächsten Arbeitstag."""
        day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        while not self.is_working_day(day):
            day += timedelta(days=1)
        return day + timedelta(hours=self.day_start_hour)

    def add_workdays(self, start: datetime, days: float) -> datetime:
        """
        Addiert Arbeitstage zu start und überspringt arbeitsfreie Tage.

        Ganze Tage werden einzeln gezählt, ein Bruchteil wird danach als Zeitspanne
        addiert. Negative Werte rechnen rückwärts.

        Examples:
            >>> WorkCalendar().add_workdays(datetime(2026, 3, 6), 1).day   # Fr -> Mo
            9
        """
        if math.isinf(days):
            return _FAR_FUTURE if days > 0 else _FAR_PAST

        whole = int(days)
        step = timedelta(days=1 if whole > 0 else -1)
        current = start
        for _ in range(abs(whole)):
            current += step
            while not self.is_working_day(current):
                current += step
        fraction = days - whole
        return current + timedelta(days=fraction) if fraction else current

    def count_weekend_days(self, start: datetime, end: datetime) -> int:
        """Anzahl Samstage/Sonntage in [start, end)."""
        days = (start + timedelta(days=i) for i in range(max((end - start).days, 0)))
        return len([d for d in days if d.weekday() >= 5])

    def count_holidays(self, start: datetime, end: datetime) -> int:
        """Anzahl Feiertage in [start, end] (beide inklusiv)."""
        days = (start + timedelta(days=i) for i in range(max((end - start).days + 1, 0)))
        return len([d for d in days if d.strftime('%Y-%m-%d') in self.holidays])


def load_calendar(cfg_dir: Optional[Path] = None,
                  year: Optional[int] = None) -> Tuple[WorkCalendar, Optional[Dict[str, str]]]:
    """
    Erzeugt den Kalender aus cfg/defaults.cfg ([CPM] skip_weekends/skip_holidays, [Holidays]).

    Returns:
        (Kalender, Feiertage {YYYY-MM-DD: Name} für year ± 1 – None wenn skip_holidays aus ist)
    """
    from .config_loader import ConfigLoader

    config_path = Path(cfg_dir) / "defaults.cfg" if cfg_dir else None
    config = ConfigLoader(config_path if config_path and config_path.exists() else None)
    settings = config.get_cpm_settings()

    holidays: Optional[Dict[str, str]] = None
    if settings.get('skip_holidays', False):
        holidays = config.get_holidays(year=year or datetime.now().year, year_range=1)

    calendar = WorkCalendar(
        skip_weekends=settings.get('skip_weekends', True),
        holidays=frozenset(holidays or {}),
        day_start_hour=_parse_day_start(config.get_working_hours().get('morning_shift', '')),
    )
    return calendar, holidays


def _parse_day_start(shift: str) -> float:
    """'09:00-12:00' → 9.0; Fallback 8.0."""
    try:
        hours, minutes = shift.split('-')[0].strip().split(':')
        return int(hours) + int(minutes) / 60
    except (ValueError, AttributeError):
        return 8.0
