"""Base utilities shared by all configuration modules.

This module defines :class:`BaseModule`, a lightweight helper providing
XML element creation and numeric validation routines used by the other
modules in :mod:`physicell_config`.  Modules store a reference to the
parent :class:`~physicell_config.config_builder_modular.PhysiCellConfig`
instance so they can interact with each other when generating XML.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import xml.etree.ElementTree as ET

if TYPE_CHECKING:
    from ..config_builder_modular import PhysiCellConfig


class BaseModule(ABC):
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
        try:
            f_val = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{name} must be a positive number, got {value}")
            
        if f_val <= 0:
            raise ValueError(f"{name} must be a positive number, got {value}")
    
    def _validate_non_negative_number(self, value: float, name: str) -> None:
        """Validate that *value* is zero or positive.

        Raises
        ------
        ValueError
            If *value* is negative.
        """
        try:
            f_val = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{name} must be a non-negative number, got {value}")
            
        if f_val < 0:
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

    @abstractmethod
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load module configuration from XML element.
        
        Args:
            xml_element: XML element containing module data, or None if section missing
        """
        pass
        
    def merge_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Merge XML configuration with existing module data.
        
        Default implementation calls load_from_xml. Override for custom merge logic.
        
        Args:
            xml_element: XML element containing module data, or None if section missing
        """
        self.load_from_xml(xml_element)
        
    def _safe_get_text(self, element: ET.Element, path: str, 
                       default: Any = None, convert_type: type = str) -> Any:
        """Safely extract text from XML element with type conversion.
        
        Args:
            element: Parent XML element
            path: XPath to child element
            default: Default value if element not found
            convert_type: Type to convert text to
            
        Returns:
            Converted text value or default
        """
        child = element.find(path)
        if child is None or child.text is None:
            return default
            
        try:
            text = child.text.strip()
            if convert_type == bool:
                return text.lower() in ('true', '1', 'yes')
            return convert_type(text)
        except (ValueError, TypeError):
            return default
        
    def _safe_get_attrib(self, element: ET.Element, attrib: str, 
                        default: Any = None, convert_type: type = str) -> Any:
        """Safely extract attribute from XML element with type conversion.
        
        Args:
            element: XML element
            attrib: Attribute name
            default: Default value if attribute not found
            convert_type: Type to convert attribute to
            
        Returns:
            Converted attribute value or default
        """
        value = element.get(attrib)
        if value is None:
            return default
            
        try:
            if convert_type == bool:
                return value.lower() in ('true', '1', 'yes')
            return convert_type(value)
        except (ValueError, TypeError):
            return default
        
    def _safe_find(self, element: ET.Element, path: str) -> Optional[ET.Element]:
        """Safely find child element, return None if not found.
        
        Args:
            element: Parent XML element
            path: XPath to child element
            
        Returns:
            Child element or None if not found
        """
        return element.find(path)
