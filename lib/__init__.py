"""
sproject library
================

Main entry point for the sproject library.

Usage:
    from lib import load_project, parse_duration_to_days

    project = load_project("examples/software_simple.json")
    days = parse_duration_to_days("40h")
"""

# Import models
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
    Person,
    ResourceBase,
    MachineResource,
    PersonResource,
    TaskBase,
)

# Import utils
from .utils import (
    parse_duration_to_days,
    parse_duration_to_minutes,
    detect_time_unit,
    format_time_value,
    format_datetime_value,
    convert_days_to_time_unit,
    get_time_unit_label,
    add_workdays,
    count_weekend_days,
    generate_cycle_id,
    parse_cycle_id,
    validate_duration_string,
)

__version__ = "0.2.0"

__all__ = [
    # Project models
    'load_project',
    'save_project',
    'Project',
    'SimpleProject',
    'CycleProject',
    'LoopProject',
    'PersonProject',

    # Task models
    'SimpleTask',
    'InstanceTask',
    'LoopTask',
    'SubTask',
    'TaskBase',

    # Resource models
    'Person',
    'ResourceBase',
    'MachineResource',
    'PersonResource',

    # Utils - Duration
    'parse_duration_to_days',
    'parse_duration_to_minutes',
    'detect_time_unit',
    'format_time_value',
    'format_datetime_value',
    'convert_days_to_time_unit',
    'get_time_unit_label',
    'validate_duration_string',

    # Utils - Date
    'add_workdays',
    'count_workdays',

    # Utils - ID
    'generate_cycle_id',
    'parse_cycle_id',
]
