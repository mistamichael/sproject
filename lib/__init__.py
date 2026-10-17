"""
sproject library
================

Usage:
    from lib import load_project, build_schedule

    project = load_project("examples/software_simple.json")
    schedule = build_schedule(project)
    print(schedule.cpm.project_duration)
"""

from .models import (
    load_project,
    save_project,
    Project,
    SimpleProject,
    CycleProject,
    LoopProject,
    PersonProject,
    SimpleTask,
    InstanceTask,
    LoopTask,
    SubTask,
    TaskBase,
    Person,
    Resource,
)
from .durations import (
    parse_duration_to_days,
    parse_duration_to_minutes,
    detect_time_unit,
    format_time_value,
    convert_days_to_time_unit,
    get_time_unit_label,
    validate_duration_string,
)
from .work_calendar import WorkCalendar
from .models.expander import generate_cycle_id, parse_cycle_id
from .schedule import Schedule, build_schedule

__version__ = "0.3.0"

__all__ = [
    'load_project', 'save_project',
    'Project', 'SimpleProject', 'CycleProject', 'LoopProject', 'PersonProject',
    'SimpleTask', 'InstanceTask', 'LoopTask', 'SubTask', 'TaskBase',
    'Person', 'Resource',
    'parse_duration_to_days', 'parse_duration_to_minutes', 'detect_time_unit',
    'format_time_value', 'convert_days_to_time_unit', 'get_time_unit_label',
    'validate_duration_string',
    'WorkCalendar',
    'generate_cycle_id', 'parse_cycle_id',
    'Schedule', 'build_schedule',
]
