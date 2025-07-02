"""
Options configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from .base import BaseModule


class OptionsModule(BaseModule):
    """Handles options configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.options = {
            'virtual_wall_at_domain_edge': True,
            'disable_automated_spring_adhesions': False,
            'legacy_random_points_on_sphere_in_divide': False,
            'random_seed': 0,
            'max_time': 8640.0,
            'time_units': 'min',
            'space_units': 'micron',
            'dt_diffusion': 0.01,
            'dt_mechanics': 0.1,
            'dt_phenotype': 6.0,
            'omp_num_threads': 4
        }
    
    def set_max_time(self, max_time: float, units: str = 'min') -> None:
        """Set maximum simulation time."""
        self._validate_positive_number(max_time, "max_time")
        self.options['max_time'] = max_time
        self.options['time_units'] = units
    
    def set_time_steps(self, dt_diffusion: float = None, dt_mechanics: float = None,
                      dt_phenotype: float = None) -> None:
        """Set simulation time steps."""
        if dt_diffusion is not None:
            self._validate_positive_number(dt_diffusion, "dt_diffusion")
            self.options['dt_diffusion'] = dt_diffusion
        
        if dt_mechanics is not None:
            self._validate_positive_number(dt_mechanics, "dt_mechanics")
            self.options['dt_mechanics'] = dt_mechanics
        
        if dt_phenotype is not None:
            self._validate_positive_number(dt_phenotype, "dt_phenotype")
            self.options['dt_phenotype'] = dt_phenotype
    
    def set_virtual_wall(self, enabled: bool) -> None:
        """Set virtual wall at domain edge."""
        self.options['virtual_wall_at_domain_edge'] = enabled
    
    def set_automated_spring_adhesions(self, disabled: bool) -> None:
        """Set automated spring adhesions."""
        self.options['disable_automated_spring_adhesions'] = disabled
    
    def set_random_seed(self, seed: int) -> None:
        """Set random seed."""
        self.options['random_seed'] = seed
    
    def set_legacy_random_points(self, enabled: bool) -> None:
        """Set legacy random points on sphere in divide."""
        self.options['legacy_random_points_on_sphere_in_divide'] = enabled
    
    def set_parallel_threads(self, num_threads: int) -> None:
        """Set number of OpenMP threads."""
        if num_threads < 1:
            raise ValueError("Number of threads must be at least 1")
        self.options['omp_num_threads'] = num_threads

    def add_to_xml(self, parent: ET.Element) -> None:
        """Add options configuration to XML."""
        options_elem = self._create_element(parent, "options")
        
        # Legacy random points (must be first)
        self._create_element(options_elem, "legacy_random_points_on_sphere_in_divide", 
                          str(self.options['legacy_random_points_on_sphere_in_divide']).lower())
        
        # Virtual wall
        self._create_element(options_elem, "virtual_wall_at_domain_edge", 
                          str(self.options['virtual_wall_at_domain_edge']).lower())
        
        # Spring adhesions
        self._create_element(options_elem, "disable_automated_spring_adhesions",
                          str(self.options['disable_automated_spring_adhesions']).lower())
        
        # Random seed
        self._create_element(options_elem, "random_seed", str(self.options['random_seed']))
    
    def get_options(self) -> Dict[str, Any]:
        """Get all options."""
        return self.options.copy()
