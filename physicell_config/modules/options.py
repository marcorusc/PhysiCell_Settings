"""Simulation and numeric options."""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from .base import BaseModule


class OptionsModule(BaseModule):
    """Configure general simulation options such as time steps."""
    
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
        """Define the total simulation duration.

        Parameters
        ----------
        max_time:
            Final time value.
        units:
            Time units (``'min'`` or ``'hour'``).
        """
        self._validate_positive_number(max_time, "max_time")
        self.options['max_time'] = max_time
        self.options['time_units'] = units
    
    def set_time_steps(self, dt_diffusion: float = None, dt_mechanics: float = None,
                      dt_phenotype: float = None) -> None:
        """Specify numerical integration time steps.

        Parameters
        ----------
        dt_diffusion, dt_mechanics, dt_phenotype:
            Optional overrides for the default time steps.
        """
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
        """Enable or disable the domain boundary wall.

        Parameters
        ----------
        enabled:
            ``True`` to prevent cells leaving the domain.
        """
        self.options['virtual_wall_at_domain_edge'] = enabled
    
    def set_automated_spring_adhesions(self, disabled: bool) -> None:
        """Toggle automated spring adhesion feature."""
        self.options['disable_automated_spring_adhesions'] = disabled
    
    def set_random_seed(self, seed: int) -> None:
        """Specify the random number generator seed."""
        self.options['random_seed'] = seed
    
    def set_legacy_random_points(self, enabled: bool) -> None:
        """Use legacy division positioning algorithm."""
        self.options['legacy_random_points_on_sphere_in_divide'] = enabled
    
    def set_parallel_threads(self, num_threads: int) -> None:
        """Set number of OpenMP threads used by the simulation."""
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
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load options configuration from XML element.
        
        Args:
            xml_element: XML element containing overall options configuration, or None if missing
        """
        if xml_element is None:
            return
            
        # Parse boolean options
        legacy_elem = xml_element.find('legacy_random_points_on_sphere_in_divide')
        if legacy_elem is not None and legacy_elem.text:
            self.options['legacy_random_points_on_sphere_in_divide'] = self._parse_bool(legacy_elem.text)
            
        virtual_wall_elem = xml_element.find('virtual_wall_at_domain_edge') 
        if virtual_wall_elem is not None and virtual_wall_elem.text:
            self.options['virtual_wall_at_domain_edge'] = self._parse_bool(virtual_wall_elem.text)
            
        spring_adhesions_elem = xml_element.find('disable_automated_spring_adhesions')
        if spring_adhesions_elem is not None and spring_adhesions_elem.text:
            self.options['disable_automated_spring_adhesions'] = self._parse_bool(spring_adhesions_elem.text)
            
        # Parse random seed
        random_seed_elem = xml_element.find('random_seed')
        if random_seed_elem is not None and random_seed_elem.text:
            self.options['random_seed'] = int(random_seed_elem.text)
    
    def load_parallel_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load parallel configuration from XML element.
        
        Args:
            xml_element: XML element containing parallel configuration, or None if missing
        """
        if xml_element is None:
            return
            
        # Parse OpenMP threads
        omp_threads_elem = xml_element.find('omp_num_threads')
        if omp_threads_elem is not None and omp_threads_elem.text:
            self.options['omp_num_threads'] = int(omp_threads_elem.text)
    
    def load_options_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load additional options configuration from XML element.
        
        Args:
            xml_element: XML element containing additional options configuration, or None if missing
        """
        if xml_element is None:
            return
            
        # Parse timing parameters
        max_time_elem = xml_element.find('max_time')
        if max_time_elem is not None and max_time_elem.text:
            self.options['max_time'] = float(max_time_elem.text)
            # Get units if available
            units = max_time_elem.get('units', 'min')
            self.options['time_units'] = units
            
        time_units_elem = xml_element.find('time_units')
        if time_units_elem is not None and time_units_elem.text:
            self.options['time_units'] = time_units_elem.text
            
        space_units_elem = xml_element.find('space_units')
        if space_units_elem is not None and space_units_elem.text:
            self.options['space_units'] = space_units_elem.text
            
        # Parse time steps
        dt_diffusion_elem = xml_element.find('dt_diffusion')
        if dt_diffusion_elem is not None and dt_diffusion_elem.text:
            self.options['dt_diffusion'] = float(dt_diffusion_elem.text)
            
        dt_mechanics_elem = xml_element.find('dt_mechanics')
        if dt_mechanics_elem is not None and dt_mechanics_elem.text:
            self.options['dt_mechanics'] = float(dt_mechanics_elem.text)
            
        dt_phenotype_elem = xml_element.find('dt_phenotype')
        if dt_phenotype_elem is not None and dt_phenotype_elem.text:
            self.options['dt_phenotype'] = float(dt_phenotype_elem.text)
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from XML text."""
        return value.lower() in ('true', '1', 'yes')
    
    def get_options(self) -> Dict[str, Any]:
        """Get all options."""
        return self.options.copy()
