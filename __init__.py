"""
PhysiCell XML Configuration Generator

A Python package for generating robust, user-friendly PhysiCell XML configuration files.
Provides a simple API to set up all simulation parameters including domain, substrates,
cell definitions, and advanced features like PhysiBoSS and parameter distributions.
"""

from .config_builder import PhysiCellConfig

__version__ = "1.0.0"
__author__ = "PhysiCell Configuration Builder Contributors"
__email__ = "your-email@domain.com"
__license__ = "MIT"
__url__ = "https://github.com/your-username/physicell-config"

__all__ = ["PhysiCellConfig"]

# Package metadata
__title__ = "physicell-config"
__description__ = "User-friendly Python package for generating PhysiCell XML configuration files"
__long_description__ = __doc__

# Version information
VERSION = (1, 0, 0)
__version_info__ = VERSION
