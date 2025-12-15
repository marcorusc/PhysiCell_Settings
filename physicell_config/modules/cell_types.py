"""Cell type configuration helpers for PhysiCell.

This module exposes :class:`CellTypeModule` which stores phenotype and custom
data for each defined cell type.  Helper methods are provided for setting cycle
models, death rates, motility parameters, secretion, and intracellular models.
The class ultimately serializes all definitions to XML under the
``cell_definitions`` section.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .base import BaseModule
from .config_loader import config_loader


class CellTypeModule(BaseModule):
    """Manage multiple cell types and their phenotypes."""
    
    def __init__(self, config):
        super().__init__(config)
        self.cell_types = {}
    
    def add_cell_type(self, name: str, parent_type: str = "default", template: str = "default") -> None:
        """Create a new cell type entry.

        Parameters
        ----------
        name:
            Unique identifier for the cell type.
        parent_type:
            Name of the parent type to inherit from, usually ``"default"``.
        template:
            Template key from ``cell_type_templates`` defined in
            embedded default parameters. Each entry bundles the cycle model,
            phenotype defaults and optional intracellular settings used to
            populate the new cell type.
        """
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
                sensitivities.clear()
                sensitivities['substrate'] = 0.0
            else:
                user_defined = any(name != 'substrate' for name in sensitivities.keys())
                
                if not user_defined:
                    # Replace placeholder with actual microenvironment substrates
                    sensitivities.clear()
                    for substrate_name in all_substrates.keys():
                        sensitivities[substrate_name] = 0.0
                else:
                    # User provided explicit substrates—remove placeholder if it still exists
                    if 'substrate' in sensitivities:
                        del sensitivities['substrate']
    
    def _default_phenotype(self) -> Dict[str, Any]:
        """Create default phenotype parameters."""
        # This method is now deprecated - use config_loader.get_default_phenotype() instead
        return config_loader.get_default_phenotype("default")
    
    def set_cycle_model(self, cell_type: str, model: str) -> None:
        """Assign a predefined cell cycle model to ``cell_type``.

        Parameters
        ----------
        cell_type:
            Name of the cell type to modify.
        model:
            One of the models available via :func:`ConfigLoader.get_cycle_model`.
        """
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
            
            # Intracellular (if present) - handled by PhysiBoSS module
            if 'intracellular' in cell_type['phenotype']:
                self._config.physiboss.add_intracellular_xml(phenotype_elem, name)
            
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
            if isinstance(value, dict) and 'value' in value:
                elem = self._create_element(custom_data_elem, key, value.get('value', ""))
                if 'units' in value:
                    elem.set("units", str(value['units']))
                if 'description' in value:
                    elem.set("description", str(value['description']))
                if 'conserved' in value:
                    elem.set("conserved", str(value['conserved']).lower())
            elif isinstance(value, dict):
                # Handle nested dictionaries that do not follow the standard schema
                nested_elem = self._create_element(custom_data_elem, key)
                for sub_key, sub_value in value.items():
                    self._create_element(nested_elem, sub_key, sub_value)
            else:
                self._create_element(custom_data_elem, key, value)
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load cell type definitions from XML element.
        
        Args:
            xml_element: XML element containing cell definitions, or None if missing
        """
        if xml_element is None:
            return
            
        # Clear existing cell types
        self.cell_types = {}
        
        # Parse each cell definition
        cell_definitions = xml_element.findall('cell_definition')
        for cell_def in cell_definitions:
            name = cell_def.get('name')
            if not name:
                continue
                
            cell_id = int(cell_def.get('ID', 0))
            parent_type = cell_def.get('parent_type')
            
            # Create cell type with basic structure
            self._create_cell_type_structure(name, parent_type)
            
            # Update ID
            self.cell_types[name]['ID'] = cell_id
            
            # Parse phenotype
            phenotype_elem = cell_def.find('phenotype')
            if phenotype_elem is not None:
                self._parse_phenotype(name, phenotype_elem)
            
            # Parse custom data
            custom_data_elem = cell_def.find('custom_data')
            if custom_data_elem is not None:
                self._parse_custom_data(name, custom_data_elem)
    
    def _create_cell_type_structure(self, name: str, parent_type: Optional[str]) -> None:
        """Create the basic cell type data structure."""
        # Use existing add_cell_type method which handles templates and structure
        self.add_cell_type(name, parent_type or "default", "default")
    
    def _parse_phenotype(self, cell_name: str, phenotype_elem: ET.Element) -> None:
        """Parse phenotype section for a cell type."""
        cell_data = self.cell_types[cell_name]
        phenotype = cell_data['phenotype']
        
        # Parse cycle
        cycle_elem = phenotype_elem.find('cycle')
        if cycle_elem is not None:
            self._parse_cycle(phenotype['cycle'], cycle_elem)
        
        # Parse death 
        death_elem = phenotype_elem.find('death')
        if death_elem is not None:
            self._parse_death(phenotype['death'], death_elem)
        
        # Parse volume
        volume_elem = phenotype_elem.find('volume')
        if volume_elem is not None:
            self._parse_volume(phenotype['volume'], volume_elem)
        
        # Parse mechanics
        mechanics_elem = phenotype_elem.find('mechanics')
        if mechanics_elem is not None:
            self._parse_mechanics(phenotype['mechanics'], mechanics_elem)
        
        # Parse motility
        motility_elem = phenotype_elem.find('motility')
        if motility_elem is not None:
            self._parse_motility(phenotype['motility'], motility_elem)
        
        # Parse secretion
        secretion_elem = phenotype_elem.find('secretion')
        if secretion_elem is not None:
            self._parse_secretion(phenotype['secretion'], secretion_elem)
        
        # Parse intracellular (PhysiBOSS)
        intracellular_elem = phenotype_elem.find('intracellular')
        if intracellular_elem is not None:
            self._parse_intracellular(phenotype, intracellular_elem)
    
    def _parse_cycle(self, cycle_data: Dict[str, Any], cycle_elem: ET.Element) -> None:
        """Parse cycle model and parameters."""
        # Parse model name
        model_elem = cycle_elem.find('model')
        if model_elem is not None and model_elem.text and model_elem.text.strip():
            cycle_data['model'] = model_elem.text.strip()
            
        # Parse phase transition rates
        rates_elem = cycle_elem.find('phase_transition_rates')
        if rates_elem is not None:
            rates = rates_elem.findall('rate')
            cycle_data['phase_transition_rates'] = []
            for rate in rates:
                try:
                    start_index = int(rate.get('start_index', 0))
                    end_index = int(rate.get('end_index', 0))
                    rate_value = float(rate.text.strip()) if rate.text and rate.text.strip() else 0.0
                    fixed_duration = rate.get('fixed_duration', 'false').lower() == 'true'
                    
                    cycle_data['phase_transition_rates'].append({
                        'start_index': start_index,
                        'end_index': end_index,
                        'rate': rate_value,
                        'fixed_duration': fixed_duration
                    })
                except (ValueError, AttributeError):
                    # Skip invalid rate entries
                    pass
    
    def _parse_death(self, death_data: Dict[str, Any], death_elem: ET.Element) -> None:
        """Parse death model parameters."""
        # Parse death models
        for model_elem in death_elem.findall('model'):
            model_name = model_elem.get('name')
            if model_name and model_name in death_data:
                # Parse rate
                rate_elem = model_elem.find('death_rate') or model_elem.find('rate')
                if rate_elem is not None and rate_elem.text and rate_elem.text.strip():
                    try:
                        rate_value = float(rate_elem.text.strip())
                        death_data[model_name]['default_rate'] = rate_value
                    except ValueError:
                        pass
                
                # Parse parameters
                params_elem = model_elem.find('parameters')
                if params_elem is not None:
                    parameters = death_data[model_name].setdefault('parameters', {})
                    for param in params_elem:
                        param_name = param.tag
                        if param.text and param.text.strip():
                            try:
                                value = float(param.text.strip())
                            except ValueError:
                                value = param.text.strip()
                            if isinstance(parameters, dict):
                                parameters[param_name] = value
                            else:
                                death_data[model_name][param_name] = value
                
                # Parse phase durations
                phase_elem = model_elem.find('phase_durations')
                if phase_elem is not None:
                    durations = []
                    for duration_elem in phase_elem.findall('duration'):
                        try:
                            duration_value = float(duration_elem.text.strip()) if duration_elem.text and duration_elem.text.strip() else 0.0
                            index = int(duration_elem.get('index', 0))
                            fixed = duration_elem.get('fixed_duration', 'false').lower() == 'true'
                            durations.append({
                                'index': index,
                                'duration': duration_value,
                                'fixed_duration': fixed
                            })
                        except ValueError:
                            pass
                    if durations:
                        death_data[model_name]['phase_durations'] = durations
    
    def _parse_volume(self, volume_data: Dict[str, Any], volume_elem: ET.Element) -> None:
        """Parse volume parameters."""
        for child in volume_elem:
            if child.tag in volume_data and child.text and child.text.strip():
                try:
                    volume_data[child.tag] = float(child.text.strip())
                except ValueError:
                    # Skip invalid numeric values
                    pass
    
    def _parse_mechanics(self, mechanics_data: Dict[str, Any], mechanics_elem: ET.Element) -> None:
        """Parse mechanics parameters."""
        # Define which fields are simple numeric values vs complex structures
        simple_numeric_fields = {
            'cell_cell_adhesion_strength',
            'cell_cell_repulsion_strength', 
            'relative_maximum_adhesion_distance',
            'attachment_elastic_constant',
            'attachment_rate',
            'detachment_rate',
            'maximum_number_of_attachments'
        }
        
        for child in mechanics_elem:
            if child.tag in mechanics_data and child.text and child.text.strip():
                # Only try to parse as float if it's a known simple numeric field
                if child.tag in simple_numeric_fields:
                    try:
                        mechanics_data[child.tag] = float(child.text.strip())
                    except ValueError:
                        # Skip invalid numeric values
                        pass
            elif child.tag in ['cell_adhesion_affinities', 'options']:
                # Skip complex structure fields that only contain whitespace
                # These would need special parsing logic
                pass
    
    def _parse_motility(self, motility_data: Dict[str, Any], motility_elem: ET.Element) -> None:
        """Parse motility parameters."""
        for child in motility_elem:
            if child.tag in motility_data and child.text and child.text.strip():
                try:
                    if child.tag in ['enabled', 'use_2D']:
                        motility_data[child.tag] = child.text.strip().lower() == 'true'
                    else:
                        motility_data[child.tag] = float(child.text.strip())
                except ValueError:
                    # Skip invalid values
                    pass
    
    def _parse_secretion(self, secretion_data: Dict[str, Any], secretion_elem: ET.Element) -> None:
        """Parse secretion parameters."""
        # Parse substrate secretion rates
        for substrate_elem in secretion_elem.findall('substrate'):
            substrate_name = substrate_elem.get('name')
            if substrate_name:
                substrate_data = {}
                
                for param in substrate_elem:
                    if param.text and param.text.strip():
                        try:
                            substrate_data[param.tag] = float(param.text.strip())
                        except ValueError:
                            # Skip invalid numeric values
                            pass
                
                if substrate_data:  # Only add if we have valid data
                    secretion_data[substrate_name] = substrate_data
    
    def _parse_custom_data(self, cell_name: str, custom_data_elem: ET.Element) -> None:
        """Parse custom data variables."""
        custom_data = self.cell_types[cell_name]['custom_data']
        
        for var_elem in custom_data_elem:
            var_name = var_elem.get('name', var_elem.tag)
            if not var_name:
                continue
            
            children = list(var_elem)
            
            # Support legacy nested structure (<sample><value>...</value>...</sample>)
            if children:
                legacy_data = {}
                for child in children:
                    if child.text and child.text.strip():
                        legacy_data[child.tag] = child.text.strip()
                if 'value' in legacy_data:
                    value = self._convert_custom_value(legacy_data.get('value'))
                    custom_data[var_name] = {
                        'value': value,
                        'units': legacy_data.get('units', 'dimensionless'),
                        'description': legacy_data.get('description', ''),
                        'conserved': legacy_data.get('conserved', 'false').lower() == 'true'
                    }
                    continue
                # Unknown nested structure: store raw
                custom_data[var_name] = legacy_data
                continue
            
            value_text = var_elem.text.strip() if var_elem.text else ""
            value = self._convert_custom_value(value_text)
            conserved_attr = var_elem.get('conserved', 'false')
            custom_data[var_name] = {
                'value': value,
                'units': var_elem.get('units', 'dimensionless'),
                'description': var_elem.get('description', ''),
                'conserved': conserved_attr.lower() in ('true', '1', 'yes')
            }
    
    def _convert_custom_value(self, text: str) -> Any:
        """Attempt to convert custom data value to int/float when possible."""
        if text == "":
            return ""
        try:
            value = float(text)
            if value.is_integer():
                return int(value)
            return value
        except ValueError:
            return text
    
    def _parse_intracellular(self, phenotype_data: Dict[str, Any], intracellular_elem: ET.Element) -> None:
        """Parse intracellular/PhysiBOSS model configuration."""
        intracellular_data = {
            'type': intracellular_elem.get('type', 'maboss'),
            'bnd_filename': '',
            'cfg_filename': '',
            'settings': {},
            'mapping': {
                'inputs': [],
                'outputs': []
            }
        }
        
        # Parse file references
        bnd_elem = intracellular_elem.find('bnd_filename')
        if bnd_elem is not None and bnd_elem.text:
            intracellular_data['bnd_filename'] = bnd_elem.text.strip()
        
        cfg_elem = intracellular_elem.find('cfg_filename')
        if cfg_elem is not None and cfg_elem.text:
            intracellular_data['cfg_filename'] = cfg_elem.text.strip()
        
        # Parse settings
        settings_elem = intracellular_elem.find('settings')
        if settings_elem is not None:
            self._parse_intracellular_settings(intracellular_data['settings'], settings_elem)
        
        # Parse mapping
        mapping_elem = intracellular_elem.find('mapping')
        if mapping_elem is not None:
            self._parse_intracellular_mapping(intracellular_data['mapping'], mapping_elem)
        
        # Store in phenotype
        phenotype_data['intracellular'] = intracellular_data
    
    def _parse_intracellular_settings(self, settings_data: Dict[str, Any], settings_elem: ET.Element) -> None:
        """Parse intracellular settings section."""
        # Parse simple numeric/string settings
        for child in settings_elem:
            if child.tag in ['intracellular_dt', 'time_stochasticity', 'scaling', 'start_time']:
                if child.text and child.text.strip():
                    try:
                        settings_data[child.tag] = float(child.text.strip())
                    except ValueError:
                        settings_data[child.tag] = child.text.strip()
            elif child.tag == 'inheritance':
                # Parse inheritance settings
                inheritance_data = {}
                if child.get('global'):
                    inheritance_data['global'] = child.get('global').lower() == 'true'
                settings_data['inheritance'] = inheritance_data
            elif child.tag == 'mutations':
                # Parse mutations
                mutations = []
                for mutation in child.findall('mutation'):
                    intracellular_name = mutation.get('intracellular_name')
                    if intracellular_name and mutation.text and mutation.text.strip():
                        try:
                            value = float(mutation.text.strip())
                            if value.is_integer():
                                value = int(value)
                        except ValueError:
                            value = mutation.text.strip()
                        mutations.append({
                            'intracellular_name': intracellular_name,
                            'value': value
                        })
                settings_data['mutations'] = mutations
            elif child.tag == 'initial_values':
                # Parse initial values
                initial_values = []
                for initial in child.findall('initial_value'):
                    intracellular_name = initial.get('intracellular_name')
                    if intracellular_name and initial.text and initial.text.strip():
                        try:
                            value = float(initial.text.strip())
                        except ValueError:
                            value = initial.text.strip()
                        initial_values.append({
                            'intracellular_name': intracellular_name,
                            'value': value
                        })
                settings_data['initial_values'] = initial_values
    
    def _parse_intracellular_mapping(self, mapping_data: Dict[str, Any], mapping_elem: ET.Element) -> None:
        """Parse intracellular input/output mapping."""
        # Parse inputs
        for input_elem in mapping_elem.findall('input'):
            physicell_name = input_elem.get('physicell_name')
            intracellular_name = input_elem.get('intracellular_name')
            
            if physicell_name and intracellular_name:
                input_data = {
                    'physicell_name': physicell_name,
                    'intracellular_name': intracellular_name,
                    'settings': {}
                }
                
                # Parse input settings
                settings_elem = input_elem.find('settings')
                if settings_elem is not None:
                    for setting in settings_elem:
                        if setting.text and setting.text.strip():
                            try:
                                value = float(setting.text.strip())
                                if value.is_integer():
                                    value = int(value)
                            except ValueError:
                                value = setting.text.strip()
                            input_data['settings'][setting.tag] = value
                
                mapping_data['inputs'].append(input_data)
        
        # Parse outputs
        for output_elem in mapping_elem.findall('output'):
            physicell_name = output_elem.get('physicell_name')
            intracellular_name = output_elem.get('intracellular_name')
            
            if physicell_name and intracellular_name:
                output_data = {
                    'physicell_name': physicell_name,
                    'intracellular_name': intracellular_name,
                    'settings': {}
                }
                
                # Parse output settings
                settings_elem = output_elem.find('settings')
                if settings_elem is not None:
                    for setting in settings_elem:
                        if setting.text and setting.text.strip():
                            try:
                                value = float(setting.text.strip())
                                if value.is_integer():
                                    value = int(value)
                            except ValueError:
                                value = setting.text.strip()
                            output_data['settings'][setting.tag] = value
                
                mapping_data['outputs'].append(output_data)
    
    def get_cell_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all cell types."""
        return self.cell_types.copy()
    
    def cell_type_exists(self, cell_type: str) -> bool:
        """Check if a cell type exists."""
        return cell_type in self.cell_types
