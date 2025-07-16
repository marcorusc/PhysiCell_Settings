"""
PhysiCell XML Configuration Generator

A Python package for generating robust, user-friendly PhysiCell XML configuration files.
Provides a simple API to set up all simulation parameters including domain, substrates,
cell definitions, and advanced features like PhysiBoSS and parameter distributions.
"""

__version__ = "0.1.5"
__author__ = "Marco Ruscone"
__email__ = "m.ruscone94@gmail.com"

from .config_builder_modular import PhysiCellConfig
__license__ = "MIT"
__url__ = "https://github.com/mruscone/PhysiCell_Settings"

__all__ = ["PhysiCellConfig"]

# Package metadata
__title__ = "physicell-settings"
__description__ = "User-friendly Python package for generating PhysiCell XML configuration files"
__long_description__ = __doc__

# Version information
VERSION = (0, 1, 5)
__version_info__ = VERSION
