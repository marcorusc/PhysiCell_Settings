"""
Save options configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from .base import BaseModule


class SaveOptionsModule(BaseModule):
    """Handles save options configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.save_options = {
            'folder': './output',
            'full_data': {
                'interval': 60.0,
                'enable': True
            },
            'SVG': {
                'interval': 60.0,
                'enable': True,
                'plot_substrate': {
                    'enabled': False,
                    'limits': False,
                    'substrate': 'substrate',
                    'colormap': 'YlOrRd',
                    'min_conc': 0,
                    'max_conc': 1
                },
                'legend': {
                    'enabled': False,
                    'cell_phase': False,
                    'cell_type': True
                }
            },
            'legacy_data': {
                'enable': False
            }
        }
    
    def set_output_folder(self, folder: str) -> None:
        """Set output folder."""
        self.save_options['folder'] = folder
    
    def set_full_data_options(self, interval: float = None, enable: bool = None,
                             settings_interval: float = None) -> None:
        """Set full data save options."""
        if interval is not None:
            self._validate_positive_number(interval, "interval")
            self.save_options['full_data']['interval'] = interval
        
        if enable is not None:
            self.save_options['full_data']['enable'] = enable
        
        if settings_interval is not None:
            self._validate_positive_number(settings_interval, "settings_interval")
            self.save_options['full_data']['settings_interval'] = settings_interval
    
    def set_svg_options(self, interval: float = None, enable: bool = None) -> None:
        """Set SVG save options."""
        if interval is not None:
            self._validate_positive_number(interval, "interval")
            self.save_options['SVG']['interval'] = interval
        
        if enable is not None:
            self.save_options['SVG']['enable'] = enable
    
    def set_svg_plot_substrate(self, enabled: bool = False, limits: bool = False,
                              substrate: str = 'substrate', colormap: str = 'YlOrRd',
                              min_conc: float = 0, max_conc: float = 1) -> None:
        """Set SVG substrate plotting options."""
        self.save_options['SVG']['plot_substrate'] = {
            'enabled': enabled,
            'limits': limits,
            'substrate': substrate,
            'colormap': colormap,
            'min_conc': min_conc,
            'max_conc': max_conc
        }
    
    def set_svg_legend(self, enabled: bool = False, cell_phase: bool = False,
                      cell_type: bool = True) -> None:
        """Set SVG legend options."""
        self.save_options['SVG']['legend'] = {
            'enabled': enabled,
            'cell_phase': cell_phase,
            'cell_type': cell_type
        }
    
    def set_legacy_data(self, enable: bool) -> None:
        """Set legacy data save option."""
        self.save_options['legacy_data']['enable'] = enable
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add save options configuration to XML."""
        save_elem = self._create_element(parent, "save")
        
        # Folder
        self._create_element(save_elem, "folder", self.save_options['folder'])
        
        # Full data
        full_data_elem = self._create_element(save_elem, "full_data")
        
        interval_elem = self._create_element(full_data_elem, "interval", 
                                           self.save_options['full_data']['interval'])
        interval_elem.set("units", "min")
        
        enable_elem = self._create_element(full_data_elem, "enable", 
                                         str(self.save_options['full_data']['enable']).lower())
        
        # SVG
        svg_elem = self._create_element(save_elem, "SVG")
        
        svg_interval_elem = self._create_element(svg_elem, "interval", 
                                               self.save_options['SVG']['interval'])
        svg_interval_elem.set("units", "min")
        
        svg_enable_elem = self._create_element(svg_elem, "enable", 
                                             str(self.save_options['SVG']['enable']).lower())
        
        # SVG legend (if enabled)
        legend_opts = self.save_options['SVG']['legend']
        if legend_opts['enabled']:
            legend_elem = self._create_element(svg_elem, "legend")
            legend_elem.set("enabled", "true")
            self._create_element(legend_elem, "cell_phase", str(legend_opts['cell_phase']).lower())
            self._create_element(legend_elem, "cell_type", str(legend_opts['cell_type']).lower())
        
        # SVG substrate plotting
        plot_opts = self.save_options['SVG']['plot_substrate']
        plot_substrate_elem = self._create_element(svg_elem, "plot_substrate")
        plot_substrate_elem.set("enabled", str(plot_opts['enabled']).lower())
        plot_substrate_elem.set("limits", str(plot_opts['limits']).lower())
        
        self._create_element(plot_substrate_elem, "substrate", plot_opts['substrate'])
        
        # Handle empty values properly for colormap, min_conc, max_conc
        if plot_opts['colormap']:
            self._create_element(plot_substrate_elem, "colormap", plot_opts['colormap'])
        else:
            # Create empty self-closing tag
            colormap_elem = ET.SubElement(plot_substrate_elem, "colormap")
            
        if plot_opts['min_conc'] is not None or plot_opts['min_conc'] == 0:
            self._create_element(plot_substrate_elem, "min_conc", str(plot_opts['min_conc']))
        
        if plot_opts['max_conc'] is not None or plot_opts['max_conc'] == 0:
            self._create_element(plot_substrate_elem, "max_conc", str(plot_opts['max_conc']))
        
        # Legacy data
        legacy_elem = self._create_element(save_elem, "legacy_data")
        self._create_element(legacy_elem, "enable", str(self.save_options['legacy_data']['enable']).lower())
    
    def get_save_options(self) -> Dict[str, Any]:
        """Get all save options."""
        return self.save_options.copy()
