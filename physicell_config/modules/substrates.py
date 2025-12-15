"""Definition of diffusive substrates present in the simulation."""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from copy import deepcopy
from .base import BaseModule


class SubstrateModule(BaseModule):
    """Add substrates, boundary conditions and related options."""
    
    def __init__(self, config):
        super().__init__(config)
        self.substrates = {}
        self.track_internalized_substrates = False
        self.calculate_gradients = True
    
    def set_track_internalized_substrates(self, enabled: bool) -> None:
        """Set whether to track internalized substrates in each agent."""
        self.track_internalized_substrates = enabled
    
    def set_calculate_gradients(self, enabled: bool) -> None:
        """Enable/disable gradient computation in the microenvironment."""
        self.calculate_gradients = enabled
    
    def add_substrate(self, name: str, diffusion_coefficient: float = 1000.0,
                     decay_rate: float = 0.1, initial_condition: float = 0.0,
                     dirichlet_enabled: bool = False,
                     dirichlet_value: float = 0.0,
                     units: str = "dimensionless",
                     initial_units: str = "mmHg") -> None:
        """Create a new diffusive substrate entry.

        Parameters
        ----------
        name:
            Substrate identifier.
        diffusion_coefficient:
            Diffusion constant in micron^2/min.
        decay_rate:
            First-order decay rate ``1/min``.
        initial_condition:
            Initial concentration value.
        dirichlet_enabled, dirichlet_value:
            Global Dirichlet condition settings.
        units, initial_units:
            Units for the concentration fields.
        """
        self._validate_non_negative_number(diffusion_coefficient, "diffusion_coefficient")
        self._validate_non_negative_number(decay_rate, "decay_rate")
        
        substrate_id = len(self.substrates)
        
        self.substrates[name] = {
            'id': substrate_id,
            'diffusion_coefficient': diffusion_coefficient,
            'decay_rate': decay_rate,
            'initial_condition': initial_condition,
            'dirichlet_enabled': dirichlet_enabled,
            'dirichlet_value': dirichlet_value,
            'units': units,
            'initial_units': initial_units,
            'dirichlet_options': {
                'xmin': {'enabled': False, 'value': ""},
                'xmax': {'enabled': False, 'value': ""},
                'ymin': {'enabled': False, 'value': ""},
                'ymax': {'enabled': False, 'value': ""},
                'zmin': {'enabled': False, 'value': ""},
                'zmax': {'enabled': False, 'value': ""}
            }
        }
    
    def set_dirichlet_boundary(self, substrate_name: str, boundary: str,
                              enabled: bool, value: float = 0.0) -> None:
        """Configure boundary-specific Dirichlet settings."""
        if substrate_name not in self.substrates:
            raise ValueError(f"Substrate '{substrate_name}' not found")
        
        valid_boundaries = ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']
        if boundary not in valid_boundaries:
            raise ValueError(f"Invalid boundary '{boundary}'. Must be one of {valid_boundaries}")
        
        self.substrates[substrate_name]['dirichlet_options'][boundary] = {
            'enabled': enabled, 
            'value': value
        }
    
    def remove_substrate(self, name: str) -> None:
        """Remove a substrate from the configuration."""
        if name in self.substrates:
            del self.substrates[name]
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add substrates configuration to XML."""
        microenv_elem = self._create_element(parent, "microenvironment_setup")
        
        # Variable definitions
        for name, substrate in self.substrates.items():
            variable_elem = self._create_element(microenv_elem, "variable")
            variable_elem.set("name", name)
            variable_elem.set("units", substrate['units'])
            variable_elem.set("ID", str(substrate['id']))
            
            # Physical parameters
            physical_elem = self._create_element(variable_elem, "physical_parameter_set")
            
            try:
                diff_val = float(substrate['diffusion_coefficient'])
            except (ValueError, TypeError):
                diff_val = 0
            
            if diff_val > 0:
                diff_elem = self._create_element(physical_elem, "diffusion_coefficient", 
                                               substrate['diffusion_coefficient'])
                diff_elem.set("units", "micron^2/min")
            
            # Always add decay_rate, even if it's 0
            decay_elem = self._create_element(physical_elem, "decay_rate", 
                                            substrate['decay_rate'])
            decay_elem.set("units", "1/min")
            
            # Initial conditions
            initial_elem = self._create_element(variable_elem, "initial_condition", 
                                              substrate['initial_condition'])
            initial_elem.set("units", substrate['initial_units'])
            
            # Dirichlet boundary conditions
            boundary_elem = self._create_element(variable_elem, "Dirichlet_boundary_condition", 
                                               substrate['dirichlet_value'])
            boundary_elem.set("units", substrate['initial_units'])
            boundary_elem.set("enabled", "True" if substrate['dirichlet_enabled'] else "False")
            
            # Dirichlet options (boundary-specific settings)
            dirichlet_opts_elem = self._create_element(variable_elem, "Dirichlet_options")
            for boundary_id, boundary_data in substrate['dirichlet_options'].items():
                boundary_value_elem = ET.SubElement(dirichlet_opts_elem, "boundary_value")
                boundary_value_elem.set("ID", boundary_id)
                boundary_value_elem.set("enabled", "True" if boundary_data['enabled'] else "False")
                boundary_value_elem.text = str(boundary_data['value'])
        
        # Microenvironment options (always add these, even if no substrates)
        options_elem = self._create_element(microenv_elem, "options")
        self._create_element(options_elem, "calculate_gradients", 
                           str(self.calculate_gradients).lower())
        self._create_element(options_elem, "track_internalized_substrates_in_each_agent", 
                           "true" if self.track_internalized_substrates else "false")
        
        # Initial condition files (matlab format support)
        initial_cond_elem = self._create_element(options_elem, "initial_condition")
        initial_cond_elem.set("type", "matlab")
        initial_cond_elem.set("enabled", "false")
        self._create_element(initial_cond_elem, "filename", "./config/initial.mat")
        
        # Dirichlet nodes files
        dirichlet_nodes_elem = self._create_element(options_elem, "dirichlet_nodes")
        dirichlet_nodes_elem.set("type", "matlab") 
        dirichlet_nodes_elem.set("enabled", "false")
        self._create_element(dirichlet_nodes_elem, "filename", "./config/dirichlet.mat")
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load substrate configuration from XML element.
        
        Args:
            xml_element: XML element containing microenvironment configuration, or None if missing
        """
        if xml_element is None:
            # No microenvironment section found, keep defaults
            return
            
        # Clear existing substrates
        self.substrates = {}
        
        # Parse substrate variables
        variables = xml_element.findall('variable')
        for var in variables:
            name = var.get('name')
            if not name:
                continue
                
            units = var.get('units', 'dimensionless')
            substrate_id = int(var.get('ID', 0))
            
            # Initialize substrate with defaults
            substrate_data = {
                'id': substrate_id,
                'diffusion_coefficient': 1000.0,
                'decay_rate': 0.1,
                'initial_condition': 0.0,
                'dirichlet_enabled': False,
                'dirichlet_value': 0.0,
                'units': units,
                'initial_units': units,
                'dirichlet_options': {
                    'xmin': {'enabled': False, 'value': 0.0},
                    'xmax': {'enabled': False, 'value': 0.0},
                    'ymin': {'enabled': False, 'value': 0.0},
                    'ymax': {'enabled': False, 'value': 0.0},
                    'zmin': {'enabled': False, 'value': 0.0},
                    'zmax': {'enabled': False, 'value': 0.0}
                }
            }
            
            # Parse physical parameters
            physical_params = var.find('physical_parameter_set')
            if physical_params is not None:
                diff_coeff_elem = physical_params.find('diffusion_coefficient')
                if diff_coeff_elem is not None and diff_coeff_elem.text:
                    substrate_data['diffusion_coefficient'] = float(diff_coeff_elem.text)
                    
                decay_rate_elem = physical_params.find('decay_rate')
                if decay_rate_elem is not None and decay_rate_elem.text:
                    substrate_data['decay_rate'] = float(decay_rate_elem.text)
            
            # Parse initial condition
            initial_elem = var.find('initial_condition')
            if initial_elem is not None and initial_elem.text:
                substrate_data['initial_condition'] = float(initial_elem.text)
                # Use units from initial_condition if available
                if initial_elem.get('units'):
                    substrate_data['initial_units'] = initial_elem.get('units')
            
            # Parse Dirichlet boundary condition
            dirichlet_elem = var.find('Dirichlet_boundary_condition')
            if dirichlet_elem is not None:
                if dirichlet_elem.text:
                    substrate_data['dirichlet_value'] = float(dirichlet_elem.text)
                # Check if enabled
                enabled_attr = dirichlet_elem.get('enabled', 'false').lower()
                substrate_data['dirichlet_enabled'] = enabled_attr in ('true', '1', 'yes')
            
            # Parse Dirichlet options (boundary-specific)
            dirichlet_opts = var.find('Dirichlet_options')
            if dirichlet_opts is not None:
                for boundary_value in dirichlet_opts.findall('boundary_value'):
                    boundary_id = boundary_value.get('ID')
                    if boundary_id and boundary_id in substrate_data['dirichlet_options']:
                        enabled_attr = boundary_value.get('enabled', 'false').lower()
                        enabled = enabled_attr in ('true', '1', 'yes')
                        value = float(boundary_value.text) if boundary_value.text else 0.0
                        substrate_data['dirichlet_options'][boundary_id] = {
                            'enabled': enabled,
                            'value': value
                        }
            
            # Store substrate
            self.substrates[name] = substrate_data
        
        # Parse microenvironment options
        options = xml_element.find('options')
        if options is not None:
            calc_elem = options.find('calculate_gradients')
            if calc_elem is not None and calc_elem.text:
                self.calculate_gradients = calc_elem.text.strip().lower() in ('true', '1', 'yes')
            track_elem = options.find('track_internalized_substrates_in_each_agent')
            if track_elem is not None and track_elem.text:
                track_value = track_elem.text.lower()
                self.track_internalized_substrates = track_value in ('true', '1', 'yes')
    
    def get_substrates(self) -> Dict[str, Dict[str, Any]]:
        """Get all substrates."""
        return deepcopy(self.substrates)
