"""
PhysiCell Configuration Builder - Modular Implementation

Copyright (C) 2025 Marco Ruscone and Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Modular PhysiCell Configuration Builder

This is the refactored version that uses composition with nested module objects
to provide a clean interface while organizing code into manageable modules.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, List, Optional, Tuple
import os

# Import modules
from .modules.domain import DomainModule
from .modules.substrates import SubstrateModule
from .modules.cell_types import CellTypeModule
from .modules.cell_rules import CellRulesModule
from .modules.cell_rules_csv import CellRulesCSV
from .modules.physiboss import PhysiBoSSModule
from .modules.options import OptionsModule
from .modules.initial_conditions import InitialConditionsModule
from .modules.save_options import SaveOptionsModule


class PhysiCellConfig:
    """
    Main PhysiCell configuration class using modular composition.
    
    This class provides a single interface for building PhysiCell XML configurations
    while delegating functionality to specialized modules for maintainability.
    """
    
    def __init__(self):
        """Initialize the configuration with all modules."""
        # Initialize modules with reference to this config
        self.domain = DomainModule(self)
        self.substrates = SubstrateModule(self)
        self.cell_types = CellTypeModule(self)
        self.cell_rules = CellRulesModule(self)
        self.physiboss = PhysiBoSSModule(self)
        self.options = OptionsModule(self)
        self.initial_conditions = InitialConditionsModule(self)
        self.save_options = SaveOptionsModule(self)
        
        # Cell rules CSV module (initialized on demand)
        self._cell_rules_csv = None
        
        # User parameters (automatically include PhysiCell standard parameters)
        self.user_parameters = {}
        self._add_standard_user_parameters()
        
        # Add default substrate if none are present
        self._ensure_default_substrate()
    
    @property
    def cell_rules_csv(self) -> CellRulesCSV:
        """
        Get the cell rules CSV module with auto-updated context.
        
        This property initializes the CellRulesCSV module on first access
        and always updates the context with current cell types and substrates.
        
        Returns:
            CellRulesCSV instance with updated context
        """
        if self._cell_rules_csv is None:
            self._cell_rules_csv = CellRulesCSV(self)
        else:
            self._cell_rules_csv.update_context_from_config(self)
        
        return self._cell_rules_csv
    
    def _add_standard_user_parameters(self) -> None:
        """Initialize standard user parameters that appear in PhysiCell templates."""
        # number_of_cells is a standard parameter used for initial cell placement
        # If users specify their own cell.csv for initial conditions, this should be 0
        self.user_parameters['number_of_cells'] = {
            'value': 5,  # Default to 5 cells, common in PhysiCell examples
            'units': 'none',
            'description': 'initial number of cells (for each cell type)',
            'type': 'int'
        }
    
    def _ensure_default_substrate(self) -> None:
        """Ensure a default 'substrate' is present if no substrates are explicitly added."""
        # This will be called after initialization and before XML generation
        # to ensure there's always at least one substrate for cell secretion/chemotaxis
        pass
    
    def _add_default_substrate_if_needed(self) -> None:
        """Add default substrate if none are present before XML generation."""
        if not self.substrates.get_substrates():
            # Load default substrate parameters from config
            from .modules.config_loader import config_loader
            substrate_defaults = config_loader.get_substrate_defaults("substrate")
            
            self.substrates.add_substrate(
                name="substrate",
                diffusion_coefficient=substrate_defaults.get('diffusion_coefficient', 100000.0),
                decay_rate=substrate_defaults.get('decay_rate', 10.0),
                initial_condition=substrate_defaults.get('initial_condition', 0.0),
                dirichlet_enabled=substrate_defaults.get('dirichlet_boundary_condition', {}).get('enabled', False),
                dirichlet_value=substrate_defaults.get('dirichlet_boundary_condition', {}).get('value', 0.0),
                units="dimensionless",
                initial_units="mmHg"
            )
    
    # ===========================================
    # User Parameters (legacy compatibility)
    # ===========================================
    
    def add_user_parameter(self, name: str, value: Any, units: str = "dimensionless",
                          description: str = "", parameter_type: str = "double") -> None:
        """Add a user parameter."""
        self.user_parameters[name] = {
            'value': value,
            'units': units,
            'description': description,
            'type': parameter_type
        }
    
    def set_number_of_cells(self, count: int) -> None:
        """
        Set the number of cells for initial placement.
        
        Args:
            count: Number of cells to place initially for each cell type.
                   Set to 0 if using custom cell.csv file for initial conditions.
        """
        if not isinstance(count, int) or count < 0:
            raise ValueError("number_of_cells must be a non-negative integer")
        
        self.user_parameters['number_of_cells']['value'] = count
    
    # ===========================================
    # Convenience methods for common operations
    # ===========================================
    
    def setup_basic_simulation(self, x_range: Tuple[float, float] = (-500, 500),
                              y_range: Tuple[float, float] = (-500, 500),
                              mesh_spacing: float = 20.0,
                              max_time: float = 8640.0) -> None:
        """Setup a basic simulation with common parameters."""
        # Set domain
        self.domain.set_bounds(x_range[0], x_range[1], y_range[0], y_range[1])
        self.domain.set_mesh(mesh_spacing, mesh_spacing)
        self.domain.set_2D(True)
        
        # Set basic options
        self.options.set_max_time(max_time)
        
        # Set basic save options
        self.save_options.set_output_folder('./output')
        self.save_options.set_full_data_options(interval=60.0, enable=True)
        self.save_options.set_svg_options(interval=60.0, enable=True)
    
    def add_simple_substrate(self, name: str, diffusion_coeff: float = 1000.0,
                           decay_rate: float = 0.1, initial_value: float = 0.0) -> None:
        """Add a simple substrate with common parameters."""
        self.substrates.add_substrate(
            name=name,
            diffusion_coefficient=diffusion_coeff,
            decay_rate=decay_rate,
            initial_condition=initial_value
        )
    
    def add_simple_cell_type(self, name: str, secretion_substrate: str = None,
                           secretion_rate: float = 0.0, motile: bool = False) -> None:
        """Add a simple cell type with common parameters."""
        self.cell_types.add_cell_type(name)
        
        if secretion_substrate and secretion_rate > 0:
            self.cell_types.add_secretion(name, secretion_substrate, secretion_rate)
        
        if motile:
            self.cell_types.set_motility(name, speed=1.0, persistence_time=1.0, enabled=True)
    
    # ===========================================
    # XML Generation
    # ===========================================
    
    def generate_xml(self) -> str:
        """Generate the complete XML configuration."""
        # Ensure default substrate exists if no substrates are defined
        self._add_default_substrate_if_needed()
        
        # Update all cell types to reflect current substrate configuration
        # This must happen after substrate setup
        for cell_type_name in self.cell_types.cell_types.keys():
            self.cell_types._update_secretion_for_all_substrates(cell_type_name)
        
        # Create root element
        root = ET.Element("PhysiCell_settings")
        root.set("version", "devel-version")
        
        # Add elements in the correct order as per PhysiCell schema
        
        # 1. Domain
        self.domain.add_to_xml(root)
        
        # 2. Overall settings
        overall_elem = ET.SubElement(root, "overall")
        max_time_elem = ET.SubElement(overall_elem, "max_time", units="min")
        max_time_elem.text = str(self.options.options['max_time'])
        
        time_units_elem = ET.SubElement(overall_elem, "time_units")
        time_units_elem.text = self.options.options['time_units']
        
        space_units_elem = ET.SubElement(overall_elem, "space_units")
        space_units_elem.text = self.options.options['space_units']
        
        dt_diffusion_elem = ET.SubElement(overall_elem, "dt_diffusion", units="min")
        dt_diffusion_elem.text = str(self.options.options['dt_diffusion'])
        
        dt_mechanics_elem = ET.SubElement(overall_elem, "dt_mechanics", units="min")
        dt_mechanics_elem.text = str(self.options.options['dt_mechanics'])
        
        dt_phenotype_elem = ET.SubElement(overall_elem, "dt_phenotype", units="min")
        dt_phenotype_elem.text = str(self.options.options['dt_phenotype'])
        
        # 3. Parallel settings
        parallel_elem = ET.SubElement(root, "parallel")
        omp_num_threads_elem = ET.SubElement(parallel_elem, "omp_num_threads")
        omp_num_threads_elem.text = str(self.options.options['omp_num_threads'])
        
        # 4. Save options
        self.save_options.add_to_xml(root)
        
        # 5. Options (moved here for correct order)
        self.options.add_to_xml(root)
        
        # 6. Microenvironment (substrates)
        self.substrates.add_to_xml(root)
        
        # 7. Cell definitions
        self.cell_types.add_to_xml(root)
        
        # 8. Initial conditions
        self.initial_conditions.add_to_xml(root)
        
        # 9. Cell rules
        self.cell_rules.add_to_xml(root)
        
        # 10. User parameters
        if self.user_parameters:
            user_params_elem = ET.SubElement(root, "user_parameters")
            for name, param in self.user_parameters.items():
                param_elem = ET.SubElement(user_params_elem, name)
                param_elem.set("type", param['type'])
                param_elem.set("units", param['units'])
                param_elem.set("description", param['description'])
                param_elem.text = str(param['value'])
        
        # Convert to pretty XML string
        rough_string = ET.tostring(root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def save_xml(self, filename: str) -> None:
        """Save the XML configuration to a file."""
        xml_content = self.generate_xml()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write(xml_content)
    
    # ===========================================
    # Information and validation methods
    # ===========================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'domain': self.domain.get_info(),
            'substrates': list(self.substrates.get_substrates().keys()),
            'cell_types': list(self.cell_types.get_cell_types().keys()),
            'user_parameters': list(self.user_parameters.keys()),
            'num_rules': len(self.cell_rules.get_rules()),
            'num_rulesets': len(self.cell_rules.get_rulesets()),
            'physiboss_enabled': self.physiboss.is_enabled(),
            'initial_conditions': len(self.initial_conditions.get_conditions()),
            'options': self.options.get_options(),
            'save_options': self.save_options.get_save_options()
        }
    
    def validate(self) -> List[str]:
        """Validate the configuration and return list of issues."""
        issues = []
        
        # Check if we have at least one substrate
        if not self.substrates.get_substrates():
            issues.append("No substrates defined")
        
        # Check if we have at least one cell type
        if not self.cell_types.get_cell_types():
            issues.append("No cell types defined")
        
        # Check domain bounds make sense
        domain_info = self.domain.get_info()
        if domain_info['x_min'] >= domain_info['x_max']:
            issues.append("Domain x_min must be less than x_max")
        if domain_info['y_min'] >= domain_info['y_max']:
            issues.append("Domain y_min must be less than y_max")
        if domain_info['z_min'] >= domain_info['z_max']:
            issues.append("Domain z_min must be less than z_max")
        
        # Check mesh spacing is reasonable
        if domain_info['dx'] <= 0 or domain_info['dy'] <= 0 or domain_info['dz'] <= 0:
            issues.append("Mesh spacing must be positive")
        
        # Check time steps
        options = self.options.get_options()
        if options['dt_diffusion'] <= 0:
            issues.append("dt_diffusion must be positive")
        if options['dt_mechanics'] <= 0:
            issues.append("dt_mechanics must be positive")
        if options['dt_phenotype'] <= 0:
            issues.append("dt_phenotype must be positive")
        
        return issues
    
    # ===========================================
    # Legacy compatibility methods
    # ===========================================
    
    def set_domain(self, x_min: float, x_max: float, y_min: float, y_max: float,
                  z_min: float = -10.0, z_max: float = 10.0,
                  dx: float = 20.0, dy: float = 20.0, dz: float = 20.0) -> None:
        """Legacy method for setting domain (delegates to domain module)."""
        self.domain.set_bounds(x_min, x_max, y_min, y_max, z_min, z_max)
        self.domain.set_mesh(dx, dy, dz)
    
    def add_substrate(self, name: str, diffusion_coefficient: float = 1000.0,
                     decay_rate: float = 0.1, initial_condition: float = 0.0) -> None:
        """Legacy method for adding substrate (delegates to substrates module)."""
        self.substrates.add_substrate(name, diffusion_coefficient, decay_rate, initial_condition)
    
    def add_cell_type(self, name: str) -> None:
        """Legacy method for adding cell type (delegates to cell_types module)."""
        self.cell_types.add_cell_type(name)


    # ===========================================
    # Parallel settings
    # ===========================================
    
    def set_parallel_settings(self, omp_num_threads: int = 4) -> None:
        """Set parallel processing settings."""
        if omp_num_threads < 1:
            raise ValueError("omp_num_threads must be at least 1")
        self.options.options['omp_num_threads'] = omp_num_threads


# Create a convenient alias for backward compatibility
Config = PhysiCellConfig
