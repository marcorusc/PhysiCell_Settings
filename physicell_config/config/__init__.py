"""Configuration data module for PhysiCell settings.

This module contains embedded configuration data that was previously stored
in JSON files. The embedded approach ensures compatibility with containerized
environments and MCP agents.
"""

from .embedded_defaults import get_default_parameters
from .embedded_signals_behaviors import get_signals_behaviors

__all__ = ['get_default_parameters', 'get_signals_behaviors']
