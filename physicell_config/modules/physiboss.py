"""Intracellular boolean network support via PhysiBoSS."""

from typing import Dict, Any, List, Optional, Union
import xml.etree.ElementTree as ET
from .base import BaseModule


class PhysiBoSSModule(BaseModule):
    """Configure PhysiBoSS integration for per-cell-type intracellular models."""
    
    def __init__(self, config):
        super().__init__(config)
        self.enabled = False
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _get_cell_type(self, cell_type_name: str) -> Dict[str, Any]:
        """Get cell type data from the cell types module."""
        if cell_type_name not in self._config.cell_types.cell_types:
            raise ValueError(f"Cell type '{cell_type_name}' not found")
        return self._config.cell_types.cell_types[cell_type_name]
    
    # ============================================================================
    # PER-CELL-TYPE INTRACELLULAR FUNCTIONALITY
    # ============================================================================
    
    def add_intracellular_model(self, cell_type_name: str, model_type: str = 'maboss', 
                               bnd_filename: str = '', cfg_filename: str = '') -> None:
        """Add intracellular model to a cell type.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        model_type : str
            Type of intracellular model (default: 'maboss')
        bnd_filename : str
            Boolean network file name
        cfg_filename : str
            Configuration file name
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        cell_type['phenotype']['intracellular'] = {
            'type': model_type,
            'bnd_filename': bnd_filename,
            'cfg_filename': cfg_filename,
            'settings': {},
            'mapping': {'inputs': [], 'outputs': []},
            'initial_values': []
        }
        self.enabled = True
    
    def set_intracellular_settings(self, cell_type_name: str, intracellular_dt: float = None,
                                  time_stochasticity: int = None, scaling: float = None,
                                  start_time: float = None, inheritance_global: bool = None) -> None:
        """Set intracellular model settings for a cell type.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        intracellular_dt : float, optional
            Intracellular time step
        time_stochasticity : int, optional
            Time stochasticity parameter
        scaling : float, optional
            Scaling factor
        start_time : float, optional
            Start time
        inheritance_global : bool, optional
            Global inheritance setting
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            raise ValueError(f"No intracellular model configured for cell type '{cell_type_name}'")
        
        settings = cell_type['phenotype']['intracellular']['settings']
        
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
    
    def add_intracellular_initial_value(self, cell_type_name: str, intracellular_name: str, value: float) -> None:
        """Set initial value for an intracellular node.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        intracellular_name : str
            Name of the intracellular node
        value : float
            Initial value
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            raise ValueError(f"No intracellular model configured for cell type '{cell_type_name}'")
            
        if 'initial_values' not in cell_type['phenotype']['intracellular']:
            cell_type['phenotype']['intracellular']['initial_values'] = []
            
        cell_type['phenotype']['intracellular']['initial_values'].append({
            'intracellular_name': intracellular_name,
            'value': value
        })

    def add_intracellular_input(self, cell_type_name: str, physicell_name: str, intracellular_name: str,
                               action: str = 'activation', threshold: float = 1, smoothing: int = 0) -> None:
        """Add an input mapping for the intracellular model.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        physicell_name : str
            PhysiCell variable name
        intracellular_name : str
            Intracellular variable name
        action : str
            Action type (default: 'activation')
        threshold : float
            Threshold value (default: 1)
        smoothing : int
            Smoothing parameter (default: 0)
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            raise ValueError(f"No intracellular model configured for cell type '{cell_type_name}'")
        
        inputs = cell_type['phenotype']['intracellular']['mapping']['inputs']
        inputs.append({
            'physicell_name': physicell_name,
            'intracellular_name': intracellular_name,
            'settings': {
                'action': action,
                'threshold': threshold,
                'smoothing': smoothing
            }
        })
    
    def add_intracellular_output(self, cell_type_name: str, physicell_name: str, intracellular_name: str,
                                action: str = 'activation', value: float = 1000000, 
                                base_value: float = 0, smoothing: int = 0) -> None:
        """Add an output mapping for the intracellular model.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        physicell_name : str
            PhysiCell variable name
        intracellular_name : str
            Intracellular variable name
        action : str
            Action type (default: 'activation')
        value : float
            Output value (default: 1000000)
        base_value : float
            Base value (default: 0)
        smoothing : int
            Smoothing parameter (default: 0)
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            raise ValueError(f"No intracellular model configured for cell type '{cell_type_name}'")
        
        outputs = cell_type['phenotype']['intracellular']['mapping']['outputs']
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
    
    def add_intracellular_mutation(self, cell_type_name: str, intracellular_name: str, value: Union[str, bool]) -> None:
        """Add an intracellular mutation for a cell type.
        
        Parameters
        ----------
        cell_type_name : str
            Name of the cell type
        intracellular_name : str 
            Name of the intracellular variable
        value : Union[str, bool]
            Value for the mutation
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            raise ValueError(f"No intracellular model configured for cell type '{cell_type_name}'")
        
        # Initialize mutations if not present
        if 'settings' not in cell_type['phenotype']['intracellular']:
            cell_type['phenotype']['intracellular']['settings'] = {}
        if 'mutations' not in cell_type['phenotype']['intracellular']['settings']:
            cell_type['phenotype']['intracellular']['settings']['mutations'] = []
        
        # Add mutation
        mutation = {
            'intracellular_name': intracellular_name,
            'value': str(value).lower() if isinstance(value, bool) else str(value)
        }
        cell_type['phenotype']['intracellular']['settings']['mutations'].append(mutation)

    # ============================================================================
    # XML GENERATION
    # ============================================================================
    
    def add_intracellular_xml(self, parent_elem, cell_type_name: str) -> None:
        """Add intracellular model XML elements for a specific cell type.
        
        Parameters
        ----------
        parent_elem : ET.Element
            Parent XML element (typically phenotype)
        cell_type_name : str
            Name of the cell type
        """
        cell_type = self._get_cell_type(cell_type_name)
        
        if 'intracellular' not in cell_type['phenotype']:
            return  # No intracellular model for this cell type
        
        intracellular = cell_type['phenotype']['intracellular']
        intracellular_elem = self._create_element(parent_elem, "intracellular")
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

    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load PhysiBoSS configuration from XML element.
        
        Args:
            xml_element: XML element containing intracellular configuration, or None if missing
        """
        # TODO: Implement PhysiBoSS XML loading in Phase 2
        # For now, keep existing defaults
        pass

    def is_enabled(self) -> bool:
        """Check if PhysiBoSS is enabled.
        
        Returns True if any cell type has intracellular models configured.
        """
        # Check if any cell type has intracellular models
        if hasattr(self._config, 'cell_types') and self._config.cell_types:
            cell_types = self._config.cell_types.get_cell_types()
            for cell_name, cell_data in cell_types.items():
                phenotype = cell_data.get('phenotype', {})
                if 'intracellular' in phenotype:
                    return True
        
        # Fallback to manual enabled flag
        return self.enabled 
