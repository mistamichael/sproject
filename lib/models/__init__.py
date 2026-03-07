"""
Pydantic models for sproject JSON structures
=============================================

This package provides type-safe Pydantic models for loading and validating
project JSON files.

Usage:
    from models import load_project

    project = load_project(Path("examples/software_simple.json"))
    print(project.project)
"""

from .loader import load_project, save_project, load_project_from_dict
from .project import SimpleProject, CycleProject, LoopProject, PersonProject
from .tasks import SimpleTask, ExpandableTask, InstanceTask, LoopTask, SubTask
from .resources import Person, ResourceBase, MachineResource, PersonResource
from .base import TaskBase
from .cpm import CPMTaskResult, CPMResult, CPMCalculator
from .reports import GanttReport, ResourceListReport, StatusUpdateReport, Report

__all__ = [
    'load_project',
    'save_project',
    'load_project_from_dict',
    'SimpleProject',
    'CycleProject',
    'LoopProject',
    'PersonProject',
    'SimpleTask',
    'ExpandableTask',
    'InstanceTask',
    'LoopTask',
    'SubTask',
    'Person',
    'ResourceBase',
    'MachineResource',
    'PersonResource',
    'TaskBase',
    'CPMTaskResult',
    'CPMResult',
    'CPMCalculator',
    'GanttReport',
    'ResourceListReport',
    'StatusUpdateReport',
    'Report',
]
