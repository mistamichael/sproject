#!/usr/bin/env python3
"""
config_loader.py
================
Lädt und verwaltet die Default-Konfiguration aus cfg/defaults.cfg
"""

import configparser
import json
from pathlib import Path
from typing import Any, Optional, List, Set
from datetime import datetime


class ConfigLoader:
    """
    Lädt und verwaltet Konfigurationswerte aus defaults.cfg
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialisiert den ConfigLoader.

        Args:
            config_path: Pfad zur Konfigurationsdatei (default: cfg/defaults.cfg)
        """
        if config_path is None:
            # Suche nach cfg/defaults.cfg relativ zum Skript oder im aktuellen Verzeichnis
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "cfg" / "defaults.cfg"
            if not config_path.exists():
                config_path = Path("cfg") / "defaults.cfg"

        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.cfg_dir = config_path.parent if config_path else Path("cfg")
        self._holidays_cache_dict: dict = {}  # Cache für Feiertage (Key: year_range)

        if config_path.exists():
            self.config.read(config_path, encoding='utf-8')
        else:
            print(f"WARNUNG: Konfigurationsdatei nicht gefunden: {config_path}")
            print("Verwende hartcodierte Defaults.")

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Holt einen Wert aus der Konfiguration.

        Args:
            section: Sektion in der Config
            key: Schlüssel
            fallback: Fallback-Wert falls nicht gefunden

        Returns:
            Konfigurationswert als String
        """
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Holt einen Integer-Wert."""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Holt einen Float-Wert."""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Holt einen Boolean-Wert."""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (ValueError, configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_list(self, section: str, key: str, separator: str = ',', fallback: list = None) -> list:
        """
        Holt eine Liste von Werten (kommasepariert).

        Args:
            section: Sektion
            key: Schlüssel
            separator: Trennzeichen (default: ,)
            fallback: Fallback-Liste

        Returns:
            Liste von Strings
        """
        if fallback is None:
            fallback = []

        value = self.get(section, key)
        if value is None:
            return fallback

        return [item.strip() for item in value.split(separator) if item.strip()]

    # ========================================================================
    # Convenience-Methoden für häufig verwendete Werte
    # ========================================================================

    def get_project_start_date(self) -> datetime:
        """
        Gibt das Standard-Projektstartdatum zurück.

        Returns:
            datetime-Objekt
        """
        start_date_str = self.get('Project', 'start_date', 'today')
        if start_date_str.lower() == 'today':
            return datetime.now()
        else:
            try:
                return datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return datetime.now()

    def get_default_resource(self) -> dict:
        """
        Gibt die Standard-Ressource zurück.

        Returns:
            Dictionary mit Ressourcen-Informationen
        """
        return {
            'id': self.get('Resource', 'id', 'default_resource'),
            'name': self.get('Resource', 'name', 'Max Mustermann'),
            'email': self.get('Resource', 'email', 'max@mustermann.com'),
            'hourly_rate': self.get_float('Resource', 'hourly_rate', 100.0),
        }

    def get_working_hours(self) -> dict:
        """
        Gibt Arbeitszeitinformationen zurück.

        Returns:
            Dictionary mit Arbeitszeitdaten
        """
        return {
            'hours_per_day': self.get_int('WorkingHours', 'hours_per_day', 8),
            'days_per_week': self.get_int('WorkingHours', 'days_per_week', 5),
            'working_days': self.get_list('WorkingHours', 'working_days', fallback=['mon', 'tue', 'wed', 'thu', 'fri']),
            'morning_shift': self.get('WorkingHours', 'morning_shift', '09:00-12:00'),
            'afternoon_shift': self.get('WorkingHours', 'afternoon_shift', '13:00-17:00'),
            'lunch_break': self.get_int('WorkingHours', 'lunch_break', 60),
        }

    def get_duration_conversions(self) -> dict:
        """
        Gibt Konvertierungsfaktoren für Dauern zurück.

        Returns:
            Dictionary mit Konvertierungsfaktoren
        """
        return {
            'week_to_days': self.get_int('Duration', 'week_to_days', 5),
            'day_to_hours': self.get_int('Duration', 'day_to_hours', 8),
            'month_to_days': self.get_int('Duration', 'month_to_days', 20),
        }

    def get_output_settings(self) -> dict:
        """
        Gibt Output-Einstellungen zurück.

        Returns:
            Dictionary mit Output-Einstellungen
        """
        return {
            'results_dir': self.get('Output', 'results_dir', 'results'),
            'graphs_dir': self.get('Output', 'graphs_dir', 'graphs'),
            'json_indent': self.get_int('Output', 'json_indent', 2),
            'include_dates': self.get_bool('Output', 'include_dates', True),
            'verbose_output': self.get_bool('Output', 'verbose_output', False),
        }

    def get_cpm_settings(self) -> dict:
        """
        Gibt CPM-Einstellungen zurück.

        Returns:
            Dictionary mit CPM-Einstellungen
        """
        return {
            'round_slack': self.get_bool('CPM', 'round_slack', False),
            'critical_tolerance': self.get_float('CPM', 'critical_tolerance', 0.001),
            'skip_weekends': self.get_bool('CPM', 'skip_weekends', True),
            'skip_holidays': self.get_bool('CPM', 'skip_holidays', False),
        }

    def get_cost_settings(self) -> dict:
        """
        Gibt Kosten-Einstellungen zurück.

        Returns:
            Dictionary mit Kosten-Einstellungen
        """
        return {
            'overhead_factor': self.get_float('Costs', 'overhead_factor', 1.5),
            'risk_buffer_percent': self.get_float('Costs', 'risk_buffer_percent', 10.0),
            'vat_percent': self.get_float('Costs', 'vat_percent', 19.0),
        }

    def get_holidays(self, year: Optional[int] = None, year_range: int = 1) -> Set[str]:
        """
        Lädt Feiertage mithilfe der holidays-Bibliothek.

        Args:
            year: Jahr für die Feiertage (default: aktuelles Jahr)
            year_range: Anzahl Jahre voraus/zurück (default: 1, also year-1 bis year+1)

        Returns:
            Set mit Feiertagsdaten im Format 'YYYY-MM-DD'
        """
        # Cache-Key beinhaltet year und year_range
        cache_key = f"{year}_{year_range}"
        if hasattr(self, '_holidays_cache_dict') and cache_key in self._holidays_cache_dict:
            return self._holidays_cache_dict[cache_key]

        holidays_set: Set[str] = set()

        # Prüfe ob Feiertage berücksichtigt werden sollen
        consider_holidays = self.get_bool('Holidays', 'consider_holidays', True)
        if not consider_holidays:
            if not hasattr(self, '_holidays_cache_dict'):
                self._holidays_cache_dict = {}
            self._holidays_cache_dict[cache_key] = holidays_set
            return holidays_set

        # Bestimme Jahr
        if year is None:
            year = datetime.now().year

        country = self.get('Holidays', 'country', 'DE')
        region = self.get('Holidays', 'region', 'BY')

        # Versuche holidays-Bibliothek zu verwenden
        try:
            import holidays as holidays_lib

            # Erstelle Feiertags-Objekt für das Land und die Region
            # Für Deutschland: holidays.country_holidays('DE', subdiv='BY')
            years_to_load = list(range(year - year_range, year + year_range + 1))
            country_holidays = holidays_lib.country_holidays(country, subdiv=region, years=years_to_load)

            # Konvertiere zu Set von Strings im Format 'YYYY-MM-DD'
            for holiday_date in country_holidays.keys():
                holidays_set.add(holiday_date.strftime('%Y-%m-%d'))

        except ImportError:
            print(f"WARNUNG: holidays-Bibliothek nicht verfügbar. Installiere mit: pip install holidays")
            print(f"Feiertage werden NICHT berücksichtigt.")
        except Exception as e:
            print(f"WARNUNG: Fehler beim Laden der Feiertage für {country}/{region}: {e}")
            print(f"Feiertage werden NICHT berücksichtigt.")

        # Cache speichern
        if not hasattr(self, '_holidays_cache_dict'):
            self._holidays_cache_dict = {}
        self._holidays_cache_dict[cache_key] = holidays_set
        return holidays_set

    def print_summary(self) -> None:
        """Gibt eine Übersicht der Konfiguration aus."""
        print("=" * 70)
        print("Konfiguration geladen aus:", self.config_path)
        print("=" * 70)

        # Projekt
        print("\n[Project]")
        print(f"  Start-Datum: {self.get_project_start_date().strftime('%Y-%m-%d')}")
        print(f"  Zeitzone:    {self.get('Project', 'timezone', 'Europe/Berlin')}")
        print(f"  Währung:     {self.get('Project', 'currency', 'EUR')}")

        # Ressource
        resource = self.get_default_resource()
        print("\n[Resource]")
        print(f"  Name:        {resource['name']}")
        print(f"  E-Mail:      {resource['email']}")
        print(f"  Stundensatz: {resource['hourly_rate']:.2f} EUR")

        # Arbeitszeiten
        wh = self.get_working_hours()
        print("\n[WorkingHours]")
        print(f"  Stunden/Tag: {wh['hours_per_day']}h")
        print(f"  Tage/Woche:  {wh['days_per_week']}")
        print(f"  Arbeitstage: {', '.join(wh['working_days'])}")

        # Output
        output = self.get_output_settings()
        print("\n[Output]")
        print(f"  Results Dir: {output['results_dir']}")
        print(f"  Graphs Dir:  {output['graphs_dir']}")
        print(f"  Mit Daten:   {output['include_dates']}")

        print("=" * 70)


# Globale Instanz für einfachen Zugriff
_default_config = None


def get_config(config_path: Optional[Path] = None) -> ConfigLoader:
    """
    Gibt die globale Config-Instanz zurück (Singleton-Pattern).

    Args:
        config_path: Optionaler Pfad zur Config (nur beim ersten Aufruf)

    Returns:
        ConfigLoader-Instanz
    """
    global _default_config
    if _default_config is None:
        _default_config = ConfigLoader(config_path)
    return _default_config


def main():
    """Test-Funktion für die Konfiguration."""
    config = ConfigLoader()
    config.print_summary()


if __name__ == '__main__':
    main()
