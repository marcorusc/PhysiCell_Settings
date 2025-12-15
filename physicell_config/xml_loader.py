"""XML Loading module for PhysiCell configurations.

This module provides the core XMLLoader class for parsing PhysiCell XML
configuration files and loading them into PhysiCellConfig instances.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Union, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class XMLLoadingError(Exception):
    """Base exception for XML loading errors."""
    pass


class XMLParseError(XMLLoadingError):
    """XML parsing or structure errors."""
    pass


class XMLValidationError(XMLLoadingError):
    """XML validation errors."""
    pass


class XMLLoader:
    """Core XML parsing engine for PhysiCell configurations.
    
    This class handles the parsing of PhysiCell XML files and populates
    PhysiCellConfig instances with the loaded data.
    """
    
    def __init__(self, config_instance):
        """Initialize XMLLoader with reference to PhysiCellConfig instance.
        
        Args:
            config_instance: PhysiCellConfig instance to populate with loaded data
        """
        self.config = config_instance
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_physicell_xml(self, xml_file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate that an XML file is a valid PhysiCell configuration file.
        
        Args:
            xml_file_path: Path to the XML file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if valid PhysiCell XML, False otherwise
            - error_message: Description of validation error if invalid, empty string if valid
        """
        try:
            # Parse the XML file
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Check 1: Root element should be 'PhysiCell_settings'
            if root.tag != 'PhysiCell_settings':
                return False, f"Invalid root element '{root.tag}'. Expected 'PhysiCell_settings'."
            
            # Check 2: Must have version attribute
            version = root.get('version')
            if not version:
                return False, "Missing 'version' attribute in root element."
            
            # Check 3: Must contain essential PhysiCell sections
            required_sections = ['domain', 'microenvironment_setup', 'cell_definitions']
            missing_sections = []
            
            for section in required_sections:
                if root.find(section) is None:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, f"Missing required PhysiCell sections: {', '.join(missing_sections)}"
            
            # Check 4: Validate domain structure
            domain = root.find('domain')
            required_domain_elements = ['x_min', 'x_max', 'y_min', 'y_max', 'dx', 'dy']
            missing_domain = []
            
            for elem in required_domain_elements:
                if domain.find(elem) is None:
                    missing_domain.append(elem)
            
            if missing_domain:
                return False, f"Invalid domain section. Missing elements: {', '.join(missing_domain)}"
            
            # Check 5: Validate microenvironment structure
            microenv = root.find('microenvironment_setup')
            if microenv.find('variable') is None:
                return False, "Invalid microenvironment_setup section. Missing substrate variables."
            
            # Check 6: Validate cell definitions structure
            cell_defs = root.find('cell_definitions')
            if len(cell_defs.findall('cell_definition')) == 0:
                return False, "Invalid cell_definitions section. No cell types defined."
            
            # Check 7: Validate cell definition structure
            for cell_def in cell_defs.findall('cell_definition'):
                if not cell_def.get('name'):
                    return False, "Invalid cell definition. Missing 'name' attribute."
                
                phenotype = cell_def.find('phenotype')
                if phenotype is None:
                    return False, f"Invalid cell definition '{cell_def.get('name')}'. Missing phenotype section."
            
            # All validations passed
            return True, ""
            
        except ET.ParseError as e:
            return False, f"XML parsing error: {str(e)}"
        except FileNotFoundError:
            return False, f"File not found: {xml_file_path}"
        except Exception as e:
            return False, f"Unexpected error during validation: {str(e)}"
        
    def load_from_file(self, filename: Union[str, Path]) -> None:
        """Load configuration from XML file.
        
        Args:
            filename: Path to PhysiCell XML configuration file
            
        Raises:
            XMLParseError: If XML file cannot be parsed
            XMLValidationError: If XML structure is invalid
            FileNotFoundError: If file doesn't exist
        """
        filename = Path(filename)
        
        if not filename.exists():
            raise FileNotFoundError(f"XML file not found: {filename}")
        
        # Validate that this is a PhysiCell XML file
        is_valid, error_message = self.validate_physicell_xml(filename)
        if not is_valid:
            raise XMLValidationError(f"Invalid PhysiCell XML file '{filename}': {error_message}")
            
        self.logger.info(f"Loading XML configuration from: {filename}")
        
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            self._load_from_root(root)
            self.logger.info("Successfully loaded XML configuration")
            
        except ET.ParseError as e:
            raise XMLParseError(f"Failed to parse XML file '{filename}': {e}")
        except Exception as e:
            raise XMLLoadingError(f"Unexpected error loading '{filename}': {e}")
        
    def load_from_string(self, xml_content: str) -> None:
        """Load configuration from XML string.
        
        Args:
            xml_content: XML configuration as string
            
        Raises:
            XMLParseError: If XML string cannot be parsed
            XMLValidationError: If XML structure is invalid
        """
        self.logger.info("Loading XML configuration from string")
        
        try:
            root = ET.fromstring(xml_content)
            self._load_from_root(root)
            self.logger.info("Successfully loaded XML configuration from string")
            
        except ET.ParseError as e:
            raise XMLParseError(f"Failed to parse XML string: {e}")
        except Exception as e:
            raise XMLLoadingError(f"Unexpected error loading XML string: {e}")
            
    def _load_from_root(self, root: ET.Element) -> None:
        """Load configuration from XML root element.
        
        Args:
            root: Root XML element of PhysiCell configuration
        """
        if root.tag != "PhysiCell_settings":
            raise XMLValidationError(f"Expected 'PhysiCell_settings' root element, got '{root.tag}'")
            
        # Parse XML into section elements
        sections = self._parse_xml_structure(root)
        
        # Load each section in order
        self._load_domain(sections.get('domain'))
        self._load_overall(sections.get('overall'))
        self._load_parallel(sections.get('parallel'))
        self._load_save_options(sections.get('save'))
        self._load_options(sections.get('options'))
        self._load_microenvironment(sections.get('microenvironment_setup'))
        self._load_cell_definitions(sections.get('cell_definitions'))
        self._load_initial_conditions(sections.get('initial_conditions'))
        self._load_cell_rules(sections.get('cell_rules'))
        self._load_user_parameters(sections.get('user_parameters'))
        
    def _parse_xml_structure(self, root: ET.Element) -> Dict[str, Optional[ET.Element]]:
        """Parse XML into section elements.
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary mapping section names to XML elements
        """
        sections = {}
        
        # Map XML section names to our internal names
        section_mapping = {
            'domain': 'domain',
            'overall': 'overall', 
            'parallel': 'parallel',
            'save': 'save',
            'options': 'options',
            'microenvironment_setup': 'microenvironment_setup',
            'cell_definitions': 'cell_definitions',
            'initial_conditions': 'initial_conditions',
            'cell_rules': 'cell_rules',
            'user_parameters': 'user_parameters'
        }
        
        for xml_name, internal_name in section_mapping.items():
            element = root.find(xml_name)
            sections[internal_name] = element
            if element is not None:
                self.logger.debug(f"Found {xml_name} section")
            else:
                self.logger.debug(f"No {xml_name} section found")
                
        return sections
        
    def _load_domain(self, domain_elem: Optional[ET.Element]) -> None:
        """Parse domain section and update config.
        
        Args:
            domain_elem: XML element containing domain data, or None if section missing
        """
        if domain_elem is not None:
            self.config.domain.load_from_xml(domain_elem)
            
    def _load_overall(self, overall_elem: Optional[ET.Element]) -> None:
        """Parse overall/options section.
        
        Args:
            overall_elem: XML element containing overall settings, or None if section missing
        """
        if overall_elem is not None:
            # Extract timing and unit information that goes to options module
            self.config.options.load_options_from_xml(overall_elem)
            
    def _load_parallel(self, parallel_elem: Optional[ET.Element]) -> None:
        """Parse parallel settings section.
        
        Args:
            parallel_elem: XML element containing parallel settings, or None if section missing
        """
        if parallel_elem is not None:
            # Extract parallel settings for options module
            self.config.options.load_parallel_from_xml(parallel_elem)
            
    def _load_save_options(self, save_elem: Optional[ET.Element]) -> None:
        """Parse save options section.
        
        Args:
            save_elem: XML element containing save options, or None if section missing
        """
        if save_elem is not None:
            self.config.save_options.load_from_xml(save_elem)
            
    def _load_options(self, options_elem: Optional[ET.Element]) -> None:
        """Parse options section.
        
        Args:
            options_elem: XML element containing options, or None if section missing
        """
        if options_elem is not None:
            self.config.options.load_from_xml(options_elem)
            
    def _load_microenvironment(self, micro_elem: Optional[ET.Element]) -> None:
        """Parse substrates section.
        
        Args:
            micro_elem: XML element containing microenvironment setup, or None if section missing
        """
        if micro_elem is not None:
            self.config.substrates.load_from_xml(micro_elem)
            
    def _load_cell_definitions(self, cell_defs_elem: Optional[ET.Element]) -> None:
        """Parse cell types section.
        
        Args:
            cell_defs_elem: XML element containing cell definitions, or None if section missing
        """
        if cell_defs_elem is not None:
            self.config.cell_types.load_from_xml(cell_defs_elem)
            
    def _load_initial_conditions(self, init_elem: Optional[ET.Element]) -> None:
        """Parse initial conditions section.
        
        Args:
            init_elem: XML element containing initial conditions, or None if section missing
        """
        if init_elem is not None:
            self.config.initial_conditions.load_from_xml(init_elem)
            
    def _load_cell_rules(self, rules_elem: Optional[ET.Element]) -> None:
        """Parse cell rules section.
        
        Args:
            rules_elem: XML element containing cell rules, or None if section missing
        """
        if rules_elem is not None:
            self.config.cell_rules.load_from_xml(rules_elem)
            
    def _load_user_parameters(self, params_elem: Optional[ET.Element]) -> None:
        """Parse user parameters section.
        
        Args:
            params_elem: XML element containing user parameters, or None if section missing
        """
        if params_elem is not None:
            # Load user parameters directly into config
            self._parse_user_parameters(params_elem)
            
    def _parse_user_parameters(self, params_elem: ET.Element) -> None:
        """Parse user parameters into config.
        
        Args:
            params_elem: XML element containing user parameters
        """
        for param_elem in params_elem:
            param_name = param_elem.tag
            param_value = param_elem.text or ""
            param_type = param_elem.get('type', 'string')
            param_units = param_elem.get('units', 'dimensionless')
            param_description = param_elem.get('description', '')
            
            # Convert value based on type
            try:
                if param_type == 'int':
                    value = int(param_value)
                elif param_type == 'double' or param_type == 'float':
                    value = float(param_value)
                elif param_type == 'bool':
                    value = param_value.lower() in ('true', '1', 'yes')
                else:
                    value = param_value
                    
                # Add to config user parameters
                self.config.user_parameters[param_name] = {
                    'value': value,
                    'type': param_type,
                    'units': param_units,
                    'description': param_description
                }
                
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to parse user parameter '{param_name}': {e}")
                # Store as string if conversion fails
                self.config.user_parameters[param_name] = {
                    'value': param_value,
                    'type': 'string',
                    'units': param_units,
                    'description': param_description
                }
