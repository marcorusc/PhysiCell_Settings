"""
PhysiBoSS configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from .base import BaseModule


class PhysiBoSSModule(BaseModule):
    """Handles PhysiBoSS configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.physiboss_settings = {}
        self.enabled = False
    
    def enable_physiboss(self, model_file: str = "boolean_model.bnd",
                        initial_values: Optional[Dict[str, bool]] = None,
                        mutations: Optional[Dict[str, Dict[str, bool]]] = None,
                        parameters: Optional[Dict[str, float]] = None) -> None:
        """Enable PhysiBoSS with configuration."""
        self.enabled = True
        self.physiboss_settings = {
            'model_file': model_file,
            'initial_values': initial_values or {},
            'mutations': mutations or {},
            'parameters': parameters or {},
            'time_step': 12.0,
            'scaling': 10.0,
            'start_time': 0.0
        }
    
    def set_time_step(self, time_step: float) -> None:
        """Set PhysiBoSS time step."""
        if not self.enabled:
            raise ValueError("PhysiBoSS must be enabled first")
        self._validate_positive_number(time_step, "time_step")
        self.physiboss_settings['time_step'] = time_step
    
    def set_scaling(self, scaling: float) -> None:
        """Set PhysiBoSS scaling factor."""
        if not self.enabled:
            raise ValueError("PhysiBoSS must be enabled first")
        self._validate_positive_number(scaling, "scaling")
        self.physiboss_settings['scaling'] = scaling
    
    def add_initial_value(self, node: str, value: bool) -> None:
        """Add initial value for a boolean node."""
        if not self.enabled:
            raise ValueError("PhysiBoSS must be enabled first")
        self.physiboss_settings['initial_values'][node] = value
    
    def add_mutation(self, cell_line: str, node: str, value: bool) -> None:
        """Add mutation for a cell line."""
        if not self.enabled:
            raise ValueError("PhysiBoSS must be enabled first")
        if cell_line not in self.physiboss_settings['mutations']:
            self.physiboss_settings['mutations'][cell_line] = {}
        self.physiboss_settings['mutations'][cell_line][node] = value
    
    def add_parameter(self, name: str, value: float) -> None:
        """Add parameter."""
        if not self.enabled:
            raise ValueError("PhysiBoSS must be enabled first")
        self.physiboss_settings['parameters'][name] = value
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add PhysiBoSS configuration to XML."""
        if not self.enabled:
            return
        
        physiboss_elem = self._create_element(parent, "physiboss")
        physiboss_elem.set("enabled", "true")
        
        # Settings
        settings_elem = self._create_element(physiboss_elem, "physiboss_settings")
        
        self._create_element(settings_elem, "physiboss_bnd_file", 
                          self.physiboss_settings['model_file'])
        
        time_step_elem = self._create_element(settings_elem, "physiboss_time_step", 
                                            self.physiboss_settings['time_step'])
        time_step_elem.set("units", "min")
        
        scaling_elem = self._create_element(settings_elem, "physiboss_scaling", 
                                          self.physiboss_settings['scaling'])
        
        start_time_elem = self._create_element(settings_elem, "physiboss_start_time",
                                             self.physiboss_settings['start_time'])
        start_time_elem.set("units", "min")
        
        # Initial values
        if self.physiboss_settings['initial_values']:
            initial_elem = self._create_element(physiboss_elem, "physiboss_initial_values")
            for node, value in self.physiboss_settings['initial_values'].items():
                node_elem = self._create_element(initial_elem, "physiboss_initial_value")
                node_elem.set("node", node)
                node_elem.text = str(value).lower()
        
        # Mutations
        if self.physiboss_settings['mutations']:
            mutations_elem = self._create_element(physiboss_elem, "physiboss_mutations")
            for cell_line, mutations in self.physiboss_settings['mutations'].items():
                cell_elem = self._create_element(mutations_elem, "physiboss_mutation")
                cell_elem.set("cell_line", cell_line)
                for node, value in mutations.items():
                    node_elem = self._create_element(cell_elem, "physiboss_mutation_value")
                    node_elem.set("node", node)
                    node_elem.text = str(value).lower()
        
        # Parameters
        if self.physiboss_settings['parameters']:
            params_elem = self._create_element(physiboss_elem, "physiboss_parameters")
            for name, value in self.physiboss_settings['parameters'].items():
                param_elem = self._create_element(params_elem, "physiboss_parameter")
                param_elem.set("name", name)
                param_elem.text = str(value)
    
    def is_enabled(self) -> bool:
        """Check if PhysiBoSS is enabled."""
        return self.enabled
    
    def get_settings(self) -> Dict[str, Any]:
        """Get PhysiBoSS settings."""
        return self.physiboss_settings.copy() if self.enabled else {}
