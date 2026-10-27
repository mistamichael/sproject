# Configuration

> Part of the [sproject documentation](../../README.md#documentation). Deutsch: [doc/de/config_doc.md](../de/config_doc.md)

All defaults are read from `cfg/defaults.cfg`:

```ini
[CPM]
skip_weekends  = true     # Skip weekends
skip_holidays  = true     # Skip public holidays (country/region: see below)

[WorkingHours]
hours_per_day  = 8        # Working hours per day
days_per_week  = 5        # Working days per week

[Resource]
hourly_rate    = 100.00   # Default hourly rate (EUR)

[Costs]
overhead_factor = 1.5     # Overhead multiplier

[Output]
results_dir    = results  # Output directory
```

Public holidays work for **any country and region**: set `country` and `region` in the `[Holidays]` section of
`cfg/defaults.cfg` (uses the [holidays](https://pypi.org/project/holidays/) library). The setting applies to all
projects. Optionally, `holidays_file` can point to your own JSON file instead (format: see
[doc/de/config_doc.md](../de/config_doc.md#feiertage)).

```ini
[Holidays]
consider_holidays = true
country = DE        # e.g. AT, CH, US, GB …
region  = NW        # state/region, e.g. BY, BW …
language =          # language of holiday names (e.g. de, en); empty = country default
holidays_file =     # optional: own JSON file in cfg/ instead of the library
```
