"""
Substrate configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .base import BaseModule


class SubstrateModule(BaseModule):
    """Handles substrate configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.substrates = {}
        self.track_internalized_substrates = False
    
    def set_track_internalized_substrates(self, enabled: bool) -> None:
        """Set whether to track internalized substrates in each agent."""
        self.track_internalized_substrates = enabled
    
    def add_substrate(self, name: str, diffusion_coefficient: float = 1000.0,
                     decay_rate: float = 0.1, initial_condition: float = 0.0,
                     dirichlet_enabled: bool = False,
                     dirichlet_value: float = 0.0,
                     units: str = "dimensionless",
                     initial_units: str = "mmHg") -> None:
        """Add a substrate to the configuration."""
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
                'xmin': {'enabled': False, 'value': 0.0},
                'xmax': {'enabled': False, 'value': 0.0},
                'ymin': {'enabled': False, 'value': 0.0},
                'ymax': {'enabled': False, 'value': 0.0},
                'zmin': {'enabled': False, 'value': 0.0},
                'zmax': {'enabled': False, 'value': 0.0}
            }
        }
    
    def set_dirichlet_boundary(self, substrate_name: str, boundary: str, 
                              enabled: bool, value: float = 0.0) -> None:
        """Set Dirichlet boundary condition for a specific boundary."""
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
        if not self.substrates:
            return
            
        microenv_elem = self._create_element(parent, "microenvironment_setup")
        
        # Variable definitions
        for name, substrate in self.substrates.items():
            variable_elem = self._create_element(microenv_elem, "variable")
            variable_elem.set("name", name)
            variable_elem.set("units", substrate['units'])
            variable_elem.set("ID", str(substrate['id']))
            
            # Physical parameters
            physical_elem = self._create_element(variable_elem, "physical_parameter_set")
            
            if substrate['diffusion_coefficient'] > 0:
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
                
                # Only set text value if boundary is enabled
                if boundary_data['enabled']:
                    boundary_value_elem.text = str(boundary_data['value'])
        
        # Microenvironment options
        options_elem = self._create_element(microenv_elem, "options")
        self._create_element(options_elem, "calculate_gradients", "true")
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
    
    def get_substrates(self) -> Dict[str, Dict[str, Any]]:
        """Get all substrates."""
        return self.substrates.copy()
