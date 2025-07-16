"""Base utilities shared by all configuration modules.

This module defines :class:`BaseModule`, a lightweight helper providing
XML element creation and numeric validation routines used by the other
modules in :mod:`physicell_config`.  Modules store a reference to the
parent :class:`~physicell_config.config_builder_modular.PhysiCellConfig`
instance so they can interact with each other when generating XML.
"""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET


class BaseModule:
    """Base class for all configuration modules.

    Parameters
    ----------
    config:
        Parent :class:`PhysiCellConfig` instance used for cross-module
        communication.
    """
    
    def __init__(self, config: 'PhysiCellConfig'):
        """Store a reference to the parent configuration object."""
        self._config = config
    
    def _create_element(self, parent: ET.Element, tag: str,
                       text: Optional[str] = None,
                       attrib: Optional[Dict[str, str]] = None) -> ET.Element:
        """Create an XML element and append it to *parent*.

        Parameters
        ----------
        parent:
            The element that will contain the new node.
        tag:
            Tag name of the element to create.
        text:
            Optional text value for the element.
        attrib:
            Dictionary of attributes for the new element.

        Returns
        -------
        xml.etree.ElementTree.Element
            The newly created element.
        """
        element = ET.SubElement(parent, tag, attrib or {})
        if text is not None:
            element.text = str(text)
        return element
    
    def _validate_positive_number(self, value: float, name: str) -> None:
        """Validate that *value* is a positive number.

        Raises
        ------
        ValueError
            If *value* is not greater than zero.
        """
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{name} must be a positive number, got {value}")
    
    def _validate_non_negative_number(self, value: float, name: str) -> None:
        """Validate that *value* is zero or positive.

        Raises
        ------
        ValueError
            If *value* is negative.
        """
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{name} must be a non-negative number, got {value}")

    def _validate_number_in_range(self, value: float, min_val: float, max_val: float, name: str) -> None:
        """Validate that *value* is within ``min_val`` and ``max_val``.

        Raises
        ------
        ValueError
            If *value* is outside the provided range or not numeric.
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number, got {type(value).__name__}")
        if value < min_val or value > max_val:
            raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
