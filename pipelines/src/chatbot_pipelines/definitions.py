"""The Dagster code location. The pipeline compose profile loads defs from this module.

Add jobs, sensors and schedules here as they are written in the other modules of this package.
"""

from dagster import Definitions

defs = Definitions()
