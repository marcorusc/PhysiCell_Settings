"""
Base module for PhysiCell configuration components.
"""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET


class BaseModule:
    """Base class for configuration modules."""
    
    def __init__(self, config: 'PhysiCellConfig'):
        """Initialize module with reference to parent config."""
        self._config = config
    
    def _create_element(self, parent: ET.Element, tag: str, 
                       text: Optional[str] = None, 
                       attrib: Optional[Dict[str, str]] = None) -> ET.Element:
        """Helper to create XML elements."""
        element = ET.SubElement(parent, tag, attrib or {})
        if text is not None:
            element.text = str(text)
        return element
    
    def _validate_positive_number(self, value: float, name: str) -> None:
        """Validate that a value is a positive number."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"{name} must be a positive number, got {value}")
    
    def _validate_non_negative_number(self, value: float, name: str) -> None:
        """Validate that a value is a non-negative number."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{name} must be a non-negative number, got {value}")
