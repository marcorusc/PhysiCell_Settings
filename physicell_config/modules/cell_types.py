"""
Cell types configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .base import BaseModule
from .config_loader import config_loader


class CellTypeModule(BaseModule):
    """Handles cell type configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.cell_types = {}
    
    def add_cell_type(self, name: str, parent_type: str = "default", template: str = "default") -> None:
        """Add a cell type to the configuration."""
        self.cell_types[name] = {
            'name': name,
            'parent_type': parent_type,
            'phenotype': config_loader.get_default_phenotype(template),
            'custom_data': config_loader.get_cell_type_template(template).get('custom_data', {}),
            'functions': {},
            'interactions': {},
            'initial_parameter_distributions': config_loader.get_initial_parameter_distributions_defaults()
        }
        
        # Add intracellular if specified in template
        template_config = config_loader.get_cell_type_template(template)
        if "intracellular" in template_config:
            self.cell_types[name]['intracellular'] = config_loader.get_intracellular_defaults(template_config["intracellular"])
        
        # Ensure secretion parameters for all substrates
        self._update_secretion_for_all_substrates(name)
    
    def _update_secretion_for_all_substrates(self, cell_type: str) -> None:
        """Ensure secretion parameters exist for all substrates in the microenvironment."""
        if cell_type not in self.cell_types:
            return
            
        # Get all substrates from the config's substrate module
        all_substrates = self._config.substrates.get_substrates()
        
        # Get current secretion parameters
        current_secretion = self.cell_types[cell_type]['phenotype']['secretion']
        
        # Default secretion parameters for any missing substrate
        default_params = {
            'secretion_rate': 0.0,
            'secretion_target': 1.0,
            'uptake_rate': 0.0,
            'net_export_rate': 0.0
        }
        
        # If no substrates are explicitly defined, keep the default 'substrate' entry
        if len(all_substrates) == 0:
            # Ensure default 'substrate' exists in secretion
            if 'substrate' not in current_secretion:
                current_secretion['substrate'] = default_params.copy()
        else:
            # Remove the default 'substrate' entry if real substrates are defined
            if 'substrate' in current_secretion:
                del current_secretion['substrate']
            
            # Add missing substrates with default parameters
            for substrate_name in all_substrates.keys():
                if substrate_name not in current_secretion:
                    current_secretion[substrate_name] = default_params.copy()
        
        # Also update chemotactic sensitivities
        motility = self.cell_types[cell_type]['phenotype']['motility']
        if 'advanced_chemotaxis' in motility and 'chemotactic_sensitivities' in motility['advanced_chemotaxis']:
            sensitivities = motility['advanced_chemotaxis']['chemotactic_sensitivities']
            
            # If no substrates are explicitly defined, keep only the default 'substrate' entry
            if len(all_substrates) == 0:
                # Clear all and add only 'substrate'
                sensitivities.clear()
                sensitivities['substrate'] = 0.0
            else:
                # Remove the default 'substrate' entry if real substrates are defined
                if 'substrate' in sensitivities:
                    del sensitivities['substrate']
                
                # Add missing substrates with default sensitivity
                for substrate_name in all_substrates.keys():
                    if substrate_name not in sensitivities:
                        sensitivities[substrate_name] = 0.0
    
    def _default_phenotype(self) -> Dict[str, Any]:
        """Create default phenotype parameters."""
        # This method is now deprecated - use config_loader.get_default_phenotype() instead
        return config_loader.get_default_phenotype("default")
    
    def set_cycle_model(self, cell_type: str, model: str) -> None:
        """Set the cell cycle model for a cell type."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        # Updated to match the new comprehensive cell cycle models
        valid_models = ['Ki67_basic', 'Ki67_advanced', 'live', 'cycling_quiescent', 
                       'flow_cytometry', 'flow_cytometry_separated']
        
        if model not in valid_models:
            raise ValueError(f"Invalid cycle model '{model}'. Valid models: {valid_models}")
        
        # Get the model configuration from the config loader
        model_config = config_loader.get_cycle_model(model)
        
        # Set the cycle model and apply its configuration
        self.cell_types[cell_type]['phenotype']['cycle']['model'] = model
        self.cell_types[cell_type]['phenotype']['cycle']['data'] = model_config
        
        # Apply model-specific configurations like transition rates
        if 'transition_rates' in model_config:
            self.cell_types[cell_type]['phenotype']['cycle']['transition_rates'] = model_config['transition_rates']
        if 'phases' in model_config:
            self.cell_types[cell_type]['phenotype']['cycle']['phases'] = model_config['phases']
    
    def set_cycle_transition_rate(self, cell_type: str, from_phase: int, to_phase: int, rate: float) -> None:
        """Set a specific transition rate between cycle phases."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        self._validate_non_negative_number(rate, "transition rate")
        
        # Initialize transition_rates if not present
        if 'transition_rates' not in self.cell_types[cell_type]['phenotype']['cycle']:
            self.cell_types[cell_type]['phenotype']['cycle']['transition_rates'] = []
        
        # Update or add the transition rate
        transition_rates = self.cell_types[cell_type]['phenotype']['cycle']['transition_rates']
        
        # Find existing transition or add new one
        for transition in transition_rates:
            if transition['from'] == from_phase and transition['to'] == to_phase:
                transition['rate'] = rate
                return
        
        # Add new transition
        transition_rates.append({
            'from': from_phase,
            'to': to_phase, 
            'rate': rate
        })
    
    def set_death_rate(self, cell_type: str, death_type: str, rate: float) -> None:
        """Set death rate for a cell type."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if death_type not in ['apoptosis', 'necrosis']:
            raise ValueError(f"Invalid death type '{death_type}'. Use 'apoptosis' or 'necrosis'")
        
        self._validate_non_negative_number(rate, f"{death_type} rate")
        # Update the rate in the death model
        if 'default_rate' in self.cell_types[cell_type]['phenotype']['death'][death_type]:
            self.cell_types[cell_type]['phenotype']['death'][death_type]['default_rate'] = rate
        else:
            self.cell_types[cell_type]['phenotype']['death'][death_type]['rate'] = rate
    
    def set_volume_parameters(self, cell_type: str, total: float = None, 
                            nuclear: float = None, fluid_fraction: float = None) -> None:
        """Set volume parameters for a cell type."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        volume = self.cell_types[cell_type]['phenotype']['volume']
        
        if total is not None:
            self._validate_positive_number(total, "total volume")
            volume['total'] = total
        
        if nuclear is not None:
            self._validate_positive_number(nuclear, "nuclear volume")
            volume['nuclear'] = nuclear
        
        if fluid_fraction is not None:
            if not 0 <= fluid_fraction <= 1:
                raise ValueError("Fluid fraction must be between 0 and 1")
            volume['fluid_fraction'] = fluid_fraction
    
    def set_motility(self, cell_type: str, speed: float = None, persistence_time: float = None,
                    migration_bias: float = None, enabled: bool = None) -> None:
        """Set motility parameters for a cell type."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        motility = self.cell_types[cell_type]['phenotype']['motility']
        
        if speed is not None:
            self._validate_non_negative_number(speed, "motility speed")
            motility['speed'] = speed
        
        if persistence_time is not None:
            self._validate_non_negative_number(persistence_time, "persistence time")
            motility['persistence_time'] = persistence_time
        
        if migration_bias is not None:
            self._validate_number_in_range(migration_bias, -1.0, 1.0, "migration bias")
            motility['migration_bias'] = migration_bias
        
        if enabled is not None:
            motility['enabled'] = enabled
    
    def set_chemotaxis(self, cell_type: str, substrate: str, enabled: bool = True, 
                      direction: int = 1) -> None:
        """Set chemotaxis parameters for a cell type.
        
        Args:
            cell_type: Name of the cell type
            substrate: Name of the substrate to follow (must be a real substrate name)
            enabled: Whether chemotaxis is enabled
            direction: Direction of chemotaxis (1 for attraction, -1 for repulsion)
        """
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        # Validate substrate name - it should not be the default placeholder
        if substrate == 'substrate':
            raise ValueError("Substrate name cannot be the default placeholder 'substrate'. Use a real substrate name.")
        
        # Validate direction
        if direction not in [-1, 1]:
            raise ValueError("Direction must be 1 (attraction) or -1 (repulsion)")
        
        motility = self.cell_types[cell_type]['phenotype']['motility']
        
        # Initialize chemotaxis section if it doesn't exist
        if 'chemotaxis' not in motility:
            motility['chemotaxis'] = {}
        
        motility['chemotaxis']['enabled'] = enabled
        motility['chemotaxis']['substrate'] = substrate
        motility['chemotaxis']['direction'] = direction
    
    def set_advanced_chemotaxis(self, cell_type: str, substrate_sensitivities: dict, 
                               enabled: bool = True, normalize_each_gradient: bool = False) -> None:
        """Set advanced chemotaxis parameters for a cell type.
        
        Args:
            cell_type: Name of the cell type
            substrate_sensitivities: Dictionary mapping substrate names to sensitivity values
            enabled: Whether advanced chemotaxis is enabled
            normalize_each_gradient: Whether to normalize each gradient
        """
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        # Validate substrate names - they should not be the default placeholder
        for substrate in substrate_sensitivities.keys():
            if substrate == 'substrate':
                raise ValueError("Substrate name cannot be the default placeholder 'substrate'. Use real substrate names.")
        
        motility = self.cell_types[cell_type]['phenotype']['motility']
        
        # Initialize advanced_chemotaxis section if it doesn't exist
        if 'advanced_chemotaxis' not in motility:
            motility['advanced_chemotaxis'] = {}
        
        motility['advanced_chemotaxis']['enabled'] = enabled
        motility['advanced_chemotaxis']['normalize_each_gradient'] = normalize_each_gradient
        motility['advanced_chemotaxis']['chemotactic_sensitivities'] = substrate_sensitivities.copy()

    def add_secretion(self, cell_type: str, substrate: str, secretion_rate: float,
                     secretion_target: float = 1.0, uptake_rate: float = 0.0,
                     net_export_rate: float = 0.0) -> None:
        """Add secretion parameters for a substrate."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        self._validate_non_negative_number(secretion_rate, "secretion rate")
        self._validate_non_negative_number(secretion_target, "secretion target")
        self._validate_non_negative_number(uptake_rate, "uptake rate")
        
        secretion = self.cell_types[cell_type]['phenotype']['secretion']
        secretion[substrate] = {
            'secretion_rate': secretion_rate,
            'secretion_target': secretion_target,
            'uptake_rate': uptake_rate,
            'net_export_rate': net_export_rate
        }
    
    def update_all_cell_types_for_substrates(self) -> None:
        """Update all cell types to include secretion parameters for all substrates."""
        for cell_type_name in self.cell_types.keys():
            self._update_secretion_for_all_substrates(cell_type_name)
    
    def add_intracellular_model(self, cell_type: str, model_type: str = 'maboss', 
                               bnd_filename: str = '', cfg_filename: str = '') -> None:
        """Add intracellular model to a cell type."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        self.cell_types[cell_type]['phenotype']['intracellular'] = {
            'type': model_type,
            'bnd_filename': bnd_filename,
            'cfg_filename': cfg_filename,
            'settings': {},
            'mapping': {'inputs': [], 'outputs': []},
            'initial_values': []
        }
    
    def set_intracellular_settings(self, cell_type: str, intracellular_dt: float = None,
                                  time_stochasticity: int = None, scaling: float = None,
                                  start_time: float = None, inheritance_global: bool = None) -> None:
        """Set intracellular model settings."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if 'intracellular' not in self.cell_types[cell_type]['phenotype']:
            raise ValueError(f"No intracellular model found for cell type '{cell_type}'")
        
        settings = self.cell_types[cell_type]['phenotype']['intracellular']['settings']
        
        if intracellular_dt is not None:
            settings['intracellular_dt'] = intracellular_dt
        if time_stochasticity is not None:
            settings['time_stochasticity'] = time_stochasticity
        if scaling is not None:
            settings['scaling'] = scaling
        if start_time is not None:
            settings['start_time'] = start_time
        if inheritance_global is not None:
            settings['inheritance'] = {'global': inheritance_global}
    
    def add_intracellular_mutation(self, cell_type: str, intracellular_name: str, value: int) -> None:
        """Add a mutation to the intracellular model."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if 'intracellular' not in self.cell_types[cell_type]['phenotype']:
            raise ValueError(f"No intracellular model found for cell type '{cell_type}'")
        
        settings = self.cell_types[cell_type]['phenotype']['intracellular']['settings']
        if 'mutations' not in settings:
            settings['mutations'] = []
        
        settings['mutations'].append({
            'intracellular_name': intracellular_name,
            'value': value
        })
    
    def add_intracellular_initial_value(self, cell_type: str, intracellular_name: str, value: float) -> None:
        """Add an initial value for the intracellular model."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if 'intracellular' not in self.cell_types[cell_type]['phenotype']:
            raise ValueError(f"No intracellular model found for cell type '{cell_type}'")
        
        initial_values = self.cell_types[cell_type]['phenotype']['intracellular']['initial_values']
        initial_values.append({
            'intracellular_name': intracellular_name,
            'value': value
        })
    
    def add_intracellular_input(self, cell_type: str, physicell_name: str, intracellular_name: str,
                               action: str = 'activation', threshold: float = 1, smoothing: int = 0) -> None:
        """Add an input mapping for the intracellular model."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if 'intracellular' not in self.cell_types[cell_type]['phenotype']:
            raise ValueError(f"No intracellular model found for cell type '{cell_type}'")
        
        inputs = self.cell_types[cell_type]['phenotype']['intracellular']['mapping']['inputs']
        inputs.append({
            'physicell_name': physicell_name,
            'intracellular_name': intracellular_name,
            'settings': {
                'action': action,
                'threshold': threshold,
                'smoothing': smoothing
            }
        })
    
    def add_intracellular_output(self, cell_type: str, physicell_name: str, intracellular_name: str,
                                action: str = 'activation', value: float = 1000000, 
                                base_value: float = 0, smoothing: int = 0) -> None:
        """Add an output mapping for the intracellular model."""
        if cell_type not in self.cell_types:
            raise ValueError(f"Cell type '{cell_type}' not found")
        
        if 'intracellular' not in self.cell_types[cell_type]['phenotype']:
            raise ValueError(f"No intracellular model found for cell type '{cell_type}'")
        
        outputs = self.cell_types[cell_type]['phenotype']['intracellular']['mapping']['outputs']
        outputs.append({
            'physicell_name': physicell_name,
            'intracellular_name': intracellular_name,
            'settings': {
                'action': action,
                'value': value,
                'base_value': base_value,
                'smoothing': smoothing
            }
        })
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add cell types configuration to XML."""
        if not self.cell_types:
            return
        
        cell_defs_elem = self._create_element(parent, "cell_definitions")
        
        for name, cell_type in self.cell_types.items():
            cell_def_elem = self._create_element(cell_defs_elem, "cell_definition")
            cell_def_elem.set("name", name)
            cell_def_elem.set("ID", str(list(self.cell_types.keys()).index(name)))
            
            # Add phenotype
            phenotype_elem = self._create_element(cell_def_elem, "phenotype")
            
            # Cycle
            self._add_cycle_xml(phenotype_elem, cell_type['phenotype']['cycle'])
            
            # Death
            self._add_death_xml(phenotype_elem, cell_type['phenotype']['death'])
            
            # Volume
            self._add_volume_xml(phenotype_elem, cell_type['phenotype']['volume'])
            
            # Mechanics
            self._add_mechanics_xml(phenotype_elem, cell_type['phenotype']['mechanics'])
            
            # Motility
            self._add_motility_xml(phenotype_elem, cell_type['phenotype']['motility'])
            
            # Secretion
            self._add_secretion_xml(phenotype_elem, cell_type['phenotype']['secretion'])
            
            # Cell Interactions
            self._add_cell_interactions_xml(phenotype_elem, cell_type['phenotype']['cell_interactions'])
            
            # Transformations
            self._add_cell_transformations_xml(phenotype_elem, cell_type['phenotype']['cell_transformations'])
            
            # Integrity
            self._add_cell_integrity_xml(phenotype_elem, cell_type['phenotype']['cell_integrity'])
            
            # Intracellular (if present)
            if 'intracellular' in cell_type['phenotype']:
                self._add_intracellular_xml(phenotype_elem, cell_type['phenotype']['intracellular'])
            
            # Custom data
            if cell_type['custom_data']:
                self._add_custom_data_xml(cell_def_elem, cell_type['custom_data'])
            
            # Initial parameter distributions
            self._add_initial_parameter_distributions_xml(cell_def_elem, cell_type['initial_parameter_distributions'])
    
    def _add_cycle_xml(self, parent: ET.Element, cycle: Dict[str, Any]) -> None:
        """Add cycle XML elements with comprehensive cell cycle model support."""
        cycle_elem = self._create_element(parent, "cycle")
        
        # Get model name and look up configuration
        model_name = cycle.get('model', 'live')
        
        try:
            model_config = config_loader.get_cycle_model(model_name)
            cycle_elem.set("code", model_config.get('code', '5'))
            cycle_elem.set("name", model_config.get('name', model_name))
        except ValueError:
            # Fallback for unknown models
            cycle_elem.set("code", cycle.get('code', '5'))
            cycle_elem.set("name", cycle.get('name', model_name))
            model_config = {}
        
        # Add phase transition rates (new comprehensive format)
        transition_rates = cycle.get('transition_rates', model_config.get('transition_rates', []))
        if transition_rates:
            rates_elem = self._create_element(cycle_elem, "phase_transition_rates")
            rates_elem.set("units", "1/min")
            
            for transition in transition_rates:
                rate_elem = self._create_element(rates_elem, "rate", str(transition['rate']))
                rate_elem.set("start_index", str(transition['from']))
                rate_elem.set("end_index", str(transition['to']))
                
                # Check if this transition has fixed duration from phase_links
                phase_links = model_config.get('phase_links', [])
                fixed_duration = False
                for link in phase_links:
                    if link['from'] == transition['from'] and link['to'] == transition['to']:
                        fixed_duration = link.get('fixed_duration', False)
                        break
                
                rate_elem.set("fixed_duration", str(fixed_duration).lower())
        
        # Legacy support for old phase_durations format (deprecated but kept for compatibility)
        elif 'phase_durations' in cycle and cycle['phase_durations']:
            phase_durations_elem = self._create_element(cycle_elem, "phase_durations")
            phase_durations_elem.set("units", "min")
            
            for phase in cycle['phase_durations']:
                duration_elem = self._create_element(phase_durations_elem, "duration", str(phase['duration']))
                duration_elem.set("index", str(phase['index']))
                duration_elem.set("fixed_duration", str(phase['fixed_duration']).lower())
        
        # Legacy support for old phase_transition_rates format
        elif 'phase_transition_rates' in cycle and cycle['phase_transition_rates']:
            rates_elem = self._create_element(cycle_elem, "phase_transition_rates")
            rates_elem.set("units", "1/min")
            
            if isinstance(cycle['phase_transition_rates'], dict):
                for rate_key, rate_value in cycle['phase_transition_rates'].items():
                    if isinstance(rate_value, dict) and 'start_index' in rate_value:
                        rate_elem = self._create_element(rates_elem, "rate", str(rate_value['rate']))
                        rate_elem.set("start_index", str(rate_value['start_index']))
                        rate_elem.set("end_index", str(rate_value['end_index']))
                        rate_elem.set("fixed_duration", str(rate_value.get('fixed_duration', False)).lower())
    
    def _add_death_xml(self, parent: ET.Element, death: Dict[str, Any]) -> None:
        """Add death XML elements."""
        death_elem = self._create_element(parent, "death")
        
        # Apoptosis model
        if 'apoptosis' in death:
            apoptosis_data = death['apoptosis']
            apoptosis_elem = self._create_element(death_elem, "model")
            apoptosis_elem.set("code", apoptosis_data.get('code', '100'))
            apoptosis_elem.set("name", apoptosis_data.get('name', 'apoptosis'))
            
            # Death rate
            rate_elem = self._create_element(apoptosis_elem, "death_rate", apoptosis_data.get('default_rate', apoptosis_data.get('rate', 5.31667e-05)))
            rate_elem.set("units", "1/min")
            
            # Phase durations
            if 'phase_durations' in apoptosis_data:
                phase_durations_elem = self._create_element(apoptosis_elem, "phase_durations")
                phase_durations_elem.set("units", "min")
                for phase in apoptosis_data['phase_durations']:
                    duration_elem = self._create_element(phase_durations_elem, "duration", phase['duration'])
                    duration_elem.set("index", str(phase['index']))
                    duration_elem.set("fixed_duration", str(phase['fixed_duration']).lower())
            
            # Parameters
            if 'parameters' in apoptosis_data:
                params_elem = self._create_element(apoptosis_elem, "parameters")
                for param_name, param_value in apoptosis_data['parameters'].items():
                    param_elem = self._create_element(params_elem, param_name, param_value)
                    if 'rate' in param_name:
                        param_elem.set("units", "1/min")
                    elif param_name == 'relative_rupture_volume':
                        param_elem.set("units", "dimensionless")
        
        # Necrosis model
        if 'necrosis' in death:
            necrosis_data = death['necrosis']
            necrosis_elem = self._create_element(death_elem, "model")
            necrosis_elem.set("code", necrosis_data.get('code', '101'))
            necrosis_elem.set("name", necrosis_data.get('name', 'necrosis'))
            
            # Death rate
            rate_elem = self._create_element(necrosis_elem, "death_rate", necrosis_data.get('default_rate', necrosis_data.get('rate', 0.0)))
            rate_elem.set("units", "1/min")
            
            # Phase durations
            if 'phase_durations' in necrosis_data:
                phase_durations_elem = self._create_element(necrosis_elem, "phase_durations")
                phase_durations_elem.set("units", "min")
                for phase in necrosis_data['phase_durations']:
                    duration_elem = self._create_element(phase_durations_elem, "duration", phase['duration'])
                    duration_elem.set("index", str(phase['index']))
                    duration_elem.set("fixed_duration", str(phase['fixed_duration']).lower())
            
            # Parameters
            if 'parameters' in necrosis_data:
                params_elem = self._create_element(necrosis_elem, "parameters")
                for param_name, param_value in necrosis_data['parameters'].items():
                    param_elem = self._create_element(params_elem, param_name, param_value)
                    if 'rate' in param_name:
                        param_elem.set("units", "1/min")
                    elif param_name == 'relative_rupture_volume':
                        param_elem.set("units", "dimensionless")
    
    def _add_volume_xml(self, parent: ET.Element, volume: Dict[str, Any]) -> None:
        """Add volume XML elements."""
        volume_elem = self._create_element(parent, "volume")
        
        total_elem = self._create_element(volume_elem, "total", volume['total'])
        total_elem.set("units", "micron^3")
        
        fluid_frac_elem = self._create_element(volume_elem, "fluid_fraction", volume['fluid_fraction'])
        
        nuclear_elem = self._create_element(volume_elem, "nuclear", volume['nuclear'])
        nuclear_elem.set("units", "micron^3")
        
        # Add other volume parameters
        for param in ['fluid_change_rate', 'cytoplasmic_biomass_change_rate', 
                     'nuclear_biomass_change_rate', 'calcified_fraction',
                     'calcification_rate', 'relative_rupture_volume']:
            if param in volume:
                elem = self._create_element(volume_elem, param, volume[param])
                if 'rate' in param:
                    elem.set("units", "1/min")
    
    def _add_mechanics_xml(self, parent: ET.Element, mechanics: Dict[str, Any]) -> None:
        """Add mechanics XML elements."""
        mechanics_elem = self._create_element(parent, "mechanics")
        
        adhesion_elem = self._create_element(mechanics_elem, "cell_cell_adhesion_strength", 
                                           mechanics['cell_cell_adhesion_strength'])
        adhesion_elem.set("units", "micron/min")
        
        repulsion_elem = self._create_element(mechanics_elem, "cell_cell_repulsion_strength",
                                            mechanics['cell_cell_repulsion_strength'])
        repulsion_elem.set("units", "micron/min")
        
        distance_elem = self._create_element(mechanics_elem, "relative_maximum_adhesion_distance",
                                           mechanics['relative_maximum_adhesion_distance'])
        distance_elem.set("units", "dimensionless")
        
        # Cell adhesion affinities
        if mechanics['cell_adhesion_affinities']:
            affinities_elem = self._create_element(mechanics_elem, "cell_adhesion_affinities")
            for cell_type, affinity in mechanics['cell_adhesion_affinities'].items():
                affinity_elem = self._create_element(affinities_elem, "cell_adhesion_affinity", affinity)
                affinity_elem.set("name", cell_type)
        
        # Options
        if 'options' in mechanics:
            options_elem = self._create_element(mechanics_elem, "options")
            for option, value in mechanics['options'].items():
                if isinstance(value, dict):
                    option_elem = self._create_element(options_elem, option, value['value'])
                    option_elem.set("enabled", str(value['enabled']).lower())
                    if option == 'set_relative_equilibrium_distance':
                        option_elem.set("units", "dimensionless")
                    elif option == 'set_absolute_equilibrium_distance':
                        option_elem.set("units", "micron")
                else:
                    self._create_element(options_elem, option, str(value).lower())
        
        # Additional mechanics parameters
        if 'attachment_elastic_constant' in mechanics:
            elem = self._create_element(mechanics_elem, "attachment_elastic_constant", mechanics['attachment_elastic_constant'])
            elem.set("units", "1/min")
        
        if 'attachment_rate' in mechanics:
            elem = self._create_element(mechanics_elem, "attachment_rate", mechanics['attachment_rate'])
            elem.set("units", "1/min")
        
        if 'detachment_rate' in mechanics:
            elem = self._create_element(mechanics_elem, "detachment_rate", mechanics['detachment_rate'])
            elem.set("units", "1/min")
        
        if 'maximum_number_of_attachments' in mechanics:
            self._create_element(mechanics_elem, "maximum_number_of_attachments", mechanics['maximum_number_of_attachments'])
    
    def _add_motility_xml(self, parent: ET.Element, motility: Dict[str, Any]) -> None:
        """Add motility XML elements."""
        motility_elem = self._create_element(parent, "motility")
        
        speed_elem = self._create_element(motility_elem, "speed", motility['speed'])
        speed_elem.set("units", "micron/min")
        
        persistence_elem = self._create_element(motility_elem, "persistence_time", motility['persistence_time'])
        persistence_elem.set("units", "min")
        
        bias_elem = self._create_element(motility_elem, "migration_bias", motility['migration_bias'])
        bias_elem.set("units", "dimensionless")
        
        # Options section
        options_elem = self._create_element(motility_elem, "options")
        self._create_element(options_elem, "enabled", str(motility['enabled']).lower())
        
        if 'use_2D' in motility:
            self._create_element(options_elem, "use_2D", str(motility['use_2D']).lower())
        
        # Chemotaxis - Always include this section as PhysiCell requires it
        chemo_elem = self._create_element(options_elem, "chemotaxis")
        if 'chemotaxis' in motility:
            chemo_data = motility['chemotaxis']
            self._create_element(chemo_elem, "enabled", str(chemo_data.get('enabled', False)).lower())
            
            # Handle substrate - use specified substrate or first available substrate
            substrate_name = None
            if 'substrate' in chemo_data and chemo_data['substrate'] != 'substrate':
                substrate_name = chemo_data['substrate']
            else:
                # Get first available substrate as default
                available_substrates = self._config.substrates.get_substrates()
                if available_substrates:
                    substrate_name = list(available_substrates.keys())[0]
            
            if substrate_name:
                self._create_element(chemo_elem, "substrate", substrate_name)
            
            if 'direction' in chemo_data:
                self._create_element(chemo_elem, "direction", chemo_data['direction'])
            else:
                self._create_element(chemo_elem, "direction", "1")  # Default direction
        else:
            # No chemotaxis specified - create default disabled chemotaxis with first substrate
            self._create_element(chemo_elem, "enabled", "false")
            available_substrates = self._config.substrates.get_substrates()
            if available_substrates:
                substrate_name = list(available_substrates.keys())[0]
                self._create_element(chemo_elem, "substrate", substrate_name)
            self._create_element(chemo_elem, "direction", "1")
        
        # Advanced chemotaxis
        if 'advanced_chemotaxis' in motility:
            adv_chemo_elem = self._create_element(options_elem, "advanced_chemotaxis")
            adv_data = motility['advanced_chemotaxis']
            self._create_element(adv_chemo_elem, "enabled", str(adv_data.get('enabled', False)).lower())
            self._create_element(adv_chemo_elem, "normalize_each_gradient", str(adv_data.get('normalize_each_gradient', False)).lower())
            
            if 'chemotactic_sensitivities' in adv_data:
                sens_elem = self._create_element(adv_chemo_elem, "chemotactic_sensitivities")
                for substrate, sensitivity in adv_data['chemotactic_sensitivities'].items():
                    # Include all substrates, including the default 'substrate'
                    sens_substrate_elem = self._create_element(sens_elem, "chemotactic_sensitivity", sensitivity)
                    sens_substrate_elem.set("substrate", substrate)
    
    def _add_secretion_xml(self, parent: ET.Element, secretion: Dict[str, Any]) -> None:
        """Add secretion XML elements."""
        secretion_elem = self._create_element(parent, "secretion")
        
        for substrate, params in secretion.items():
            substrate_elem = self._create_element(secretion_elem, "substrate")
            substrate_elem.set("name", substrate)
            
            rate_elem = self._create_element(substrate_elem, "secretion_rate", params['secretion_rate'])
            rate_elem.set("units", "1/min")
            
            # Use secretion_target from config, but support saturation_density for backward compatibility
            target_value = params.get('secretion_target', params.get('saturation_density', 1.0))
            target_elem = self._create_element(substrate_elem, "secretion_target", target_value)
            target_elem.set("units", "substrate density")
            
            uptake_elem = self._create_element(substrate_elem, "uptake_rate", params['uptake_rate'])
            uptake_elem.set("units", "1/min")
            
            export_elem = self._create_element(substrate_elem, "net_export_rate", params['net_export_rate'])
            export_elem.set("units", "total substrate/min")
    
    def _add_cell_interactions_xml(self, parent: ET.Element, interactions: Dict[str, Any]) -> None:
        """Add cell interactions XML elements."""
        interactions_elem = self._create_element(parent, "cell_interactions")
        
        # Phagocytosis rates
        if 'apoptotic_phagocytosis_rate' in interactions:
            elem = self._create_element(interactions_elem, "apoptotic_phagocytosis_rate", interactions['apoptotic_phagocytosis_rate'])
            elem.set("units", "1/min")
        
        if 'necrotic_phagocytosis_rate' in interactions:
            elem = self._create_element(interactions_elem, "necrotic_phagocytosis_rate", interactions['necrotic_phagocytosis_rate'])
            elem.set("units", "1/min")
        
        if 'other_dead_phagocytosis_rate' in interactions:
            elem = self._create_element(interactions_elem, "other_dead_phagocytosis_rate", interactions['other_dead_phagocytosis_rate'])
            elem.set("units", "1/min")
        
        # Live phagocytosis rates
        if 'live_phagocytosis_rates' in interactions:
            live_phago_elem = self._create_element(interactions_elem, "live_phagocytosis_rates")
            for cell_type, rate in interactions['live_phagocytosis_rates'].items():
                rate_elem = self._create_element(live_phago_elem, "phagocytosis_rate", rate)
                rate_elem.set("name", cell_type)
                rate_elem.set("units", "1/min")
        
        # Attack rates
        if 'attack_rates' in interactions:
            attack_elem = self._create_element(interactions_elem, "attack_rates")
            for cell_type, rate in interactions['attack_rates'].items():
                rate_elem = self._create_element(attack_elem, "attack_rate", rate)
                rate_elem.set("name", cell_type)
                rate_elem.set("units", "1/min")
        
        # Attack damage and duration
        if 'attack_damage_rate' in interactions:
            elem = self._create_element(interactions_elem, "attack_damage_rate", interactions['attack_damage_rate'])
            elem.set("units", "1/min")
        
        if 'attack_duration' in interactions:
            elem = self._create_element(interactions_elem, "attack_duration", interactions['attack_duration'])
            elem.set("units", "min")
        
        # Fusion rates
        if 'fusion_rates' in interactions:
            fusion_elem = self._create_element(interactions_elem, "fusion_rates")
            for cell_type, rate in interactions['fusion_rates'].items():
                rate_elem = self._create_element(fusion_elem, "fusion_rate", rate)
                rate_elem.set("name", cell_type)
                rate_elem.set("units", "1/min")
    
    def _add_cell_transformations_xml(self, parent: ET.Element, transformations: Dict[str, Any]) -> None:
        """Add cell transformations XML elements."""
        transformations_elem = self._create_element(parent, "cell_transformations")
        
        if 'transformation_rates' in transformations:
            rates_elem = self._create_element(transformations_elem, "transformation_rates")
            for target_type, rate in transformations['transformation_rates'].items():
                rate_elem = self._create_element(rates_elem, "transformation_rate", rate)
                rate_elem.set("name", target_type)
                rate_elem.set("units", "1/min")
    
    def _add_cell_integrity_xml(self, parent: ET.Element, integrity: Dict[str, Any]) -> None:
        """Add cell integrity XML elements."""
        integrity_elem = self._create_element(parent, "cell_integrity")
        
        if 'damage_rate' in integrity:
            elem = self._create_element(integrity_elem, "damage_rate", integrity['damage_rate'])
            elem.set("units", "1/min")
        
        if 'damage_repair_rate' in integrity:
            elem = self._create_element(integrity_elem, "damage_repair_rate", integrity['damage_repair_rate'])
            elem.set("units", "1/min")
    
    def _add_initial_parameter_distributions_xml(self, parent: ET.Element, distributions: Dict[str, Any]) -> None:
        """Add initial parameter distributions."""
        distributions_elem = self._create_element(parent, "initial_parameter_distributions")
        distributions_elem.set("enabled", str(distributions.get("enabled", False)).lower())
        
        # Add distributions if they exist
        if "distributions" in distributions:
            for dist in distributions["distributions"]:
                dist_elem = self._create_element(distributions_elem, "distribution")
                dist_elem.set("enabled", str(dist.get("enabled", False)).lower())
                dist_elem.set("type", dist.get("type", "Log10Normal"))
                dist_elem.set("check_base", str(dist.get("check_base", True)).lower())
                
                # Add distribution parameters
                if "behavior" in dist:
                    self._create_element(dist_elem, "behavior", dist["behavior"])
                
                if dist.get("type") == "Log10Normal":
                    if "mu" in dist:
                        self._create_element(dist_elem, "mu", dist["mu"])
                    if "sigma" in dist:
                        self._create_element(dist_elem, "sigma", dist["sigma"])
                    if "upper_bound" in dist:
                        self._create_element(dist_elem, "upper_bound", dist["upper_bound"])
                elif dist.get("type") == "LogUniform":
                    if "min" in dist:
                        self._create_element(dist_elem, "min", dist["min"])
                    if "max" in dist:
                        self._create_element(dist_elem, "max", dist["max"])
    
    def _add_custom_data_xml(self, parent: ET.Element, custom_data: Dict[str, Any]) -> None:
        """Add custom data XML elements."""
        custom_data_elem = self._create_element(parent, "custom_data")
        
        for key, value in custom_data.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                nested_elem = self._create_element(custom_data_elem, key)
                for sub_key, sub_value in value.items():
                    self._create_element(nested_elem, sub_key, sub_value)
            else:
                self._create_element(custom_data_elem, key, value)
    
    def _add_intracellular_xml(self, parent: ET.Element, intracellular: Dict[str, Any]) -> None:
        """Add intracellular model XML elements."""
        intracellular_elem = self._create_element(parent, "intracellular")
        intracellular_elem.set("type", intracellular.get('type', 'maboss'))
        
        # Add file names
        if 'bnd_filename' in intracellular:
            self._create_element(intracellular_elem, "bnd_filename", intracellular['bnd_filename'])
        if 'cfg_filename' in intracellular:
            self._create_element(intracellular_elem, "cfg_filename", intracellular['cfg_filename'])
        
        # Add initial values
        if 'initial_values' in intracellular and intracellular['initial_values']:
            initial_values_elem = self._create_element(intracellular_elem, "initial_values")
            for init_val in intracellular['initial_values']:
                init_elem = self._create_element(initial_values_elem, "initial_value", init_val['value'])
                init_elem.set("intracellular_name", init_val['intracellular_name'])
        
        # Add settings
        if 'settings' in intracellular:
            settings_elem = self._create_element(intracellular_elem, "settings")
            settings = intracellular['settings']
            
            if 'intracellular_dt' in settings:
                self._create_element(settings_elem, "intracellular_dt", settings['intracellular_dt'])
            if 'time_stochasticity' in settings:
                self._create_element(settings_elem, "time_stochasticity", settings['time_stochasticity'])
            if 'scaling' in settings:
                self._create_element(settings_elem, "scaling", settings['scaling'])
            if 'start_time' in settings:
                self._create_element(settings_elem, "start_time", settings['start_time'])
            if 'inheritance' in settings:
                inheritance_elem = self._create_element(settings_elem, "inheritance")
                inheritance_elem.set("global", str(settings['inheritance'].get('global', False)))
            
            # Add mutations if present
            if 'mutations' in settings and settings['mutations']:
                mutations_elem = self._create_element(settings_elem, "mutations")
                for mutation in settings['mutations']:
                    mutation_elem = self._create_element(mutations_elem, "mutation", mutation['value'])
                    mutation_elem.set("intracellular_name", mutation['intracellular_name'])
        
        # Add mapping
        if 'mapping' in intracellular:
            mapping_elem = self._create_element(intracellular_elem, "mapping")
            mapping = intracellular['mapping']
            
            # Add inputs
            if 'inputs' in mapping:
                for input_map in mapping['inputs']:
                    input_elem = self._create_element(mapping_elem, "input")
                    input_elem.set("physicell_name", input_map['physicell_name'])
                    input_elem.set("intracellular_name", input_map['intracellular_name'])
                    
                    if 'settings' in input_map:
                        settings_elem = self._create_element(input_elem, "settings")
                        inp_settings = input_map['settings']
                        if 'action' in inp_settings:
                            self._create_element(settings_elem, "action", inp_settings['action'])
                        if 'threshold' in inp_settings:
                            self._create_element(settings_elem, "threshold", inp_settings['threshold'])
                        if 'smoothing' in inp_settings:
                            self._create_element(settings_elem, "smoothing", inp_settings['smoothing'])
            
            # Add outputs
            if 'outputs' in mapping:
                for output_map in mapping['outputs']:
                    output_elem = self._create_element(mapping_elem, "output")
                    output_elem.set("physicell_name", output_map['physicell_name'])
                    output_elem.set("intracellular_name", output_map['intracellular_name'])
                    
                    if 'settings' in output_map:
                        settings_elem = self._create_element(output_elem, "settings")
                        out_settings = output_map['settings']
                        if 'action' in out_settings:
                            self._create_element(settings_elem, "action", out_settings['action'])
                        if 'value' in out_settings:
                            self._create_element(settings_elem, "value", out_settings['value'])
                        if 'base_value' in out_settings:
                            self._create_element(settings_elem, "base_value", out_settings['base_value'])
                        if 'smoothing' in out_settings:
                            self._create_element(settings_elem, "smoothing", out_settings['smoothing'])
    
    def get_cell_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all cell types."""
        return self.cell_types.copy()
