"""Output file and visualization settings."""

from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
import copy
from .base import BaseModule


class SaveOptionsModule(BaseModule):
    """Configure data output intervals and formats."""
    
    def __init__(self, config):
        super().__init__(config)
        self.save_options = {
            'folder': './output',
            'full_data': {
                'interval': 60.0,
                'enable': True,
                'settings_interval': None
            },
            'SVG': {
                'interval': 60.0,
                'enable': True,
                'plot_substrate': {
                    'enabled': False,
                    'limits': False,
                    'substrate': 'substrate',
                    'colormap': 'YlOrRd',
                    'min_conc': "",
                    'max_conc': ""
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
        """Configure plotting of a substrate concentration in SVG outputs.

        Parameters
        ----------
        enabled:
            Turn substrate plots on or off.
        limits:
            Whether min/max concentration limits are enforced.
        substrate:
            Name of the substrate to visualise.
        colormap:
            Matplotlib-style colormap name.
        min_conc, max_conc:
            Colour scale bounds.
        """
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
        """Control the presence and contents of the SVG legend."""
        self.save_options['SVG']['legend'] = {
            'enabled': enabled,
            'cell_phase': cell_phase,
            'cell_type': cell_type
        }
    
    def set_legacy_data(self, enable: bool) -> None:
        """Output additional legacy-format data files."""
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
        
        settings_interval = self.save_options['full_data'].get('settings_interval')
        if settings_interval is not None:
            settings_elem = self._create_element(full_data_elem, "settings_interval", settings_interval)
            settings_elem.set("units", "min")
        
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
        
        if plot_opts['min_conc'] is not None or plot_opts['min_conc'] == 0:
            self._create_element(plot_substrate_elem, "min_conc", str(plot_opts['min_conc']))
            
        if plot_opts['max_conc'] is not None or plot_opts['max_conc'] == 0:
            self._create_element(plot_substrate_elem, "max_conc", str(plot_opts['max_conc']))

        # Handle empty values properly for colormap, min_conc, max_conc
        if plot_opts['colormap']:
            self._create_element(plot_substrate_elem, "colormap", plot_opts['colormap'])
        else:
            # Create empty self-closing tag
            colormap_elem = ET.SubElement(plot_substrate_elem, "colormap")
        
        # Legacy data
        legacy_elem = self._create_element(save_elem, "legacy_data")
        self._create_element(legacy_elem, "enable", str(self.save_options['legacy_data']['enable']).lower())
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load save options configuration from XML element.
        
        Args:
            xml_element: XML element containing save options configuration, or None if missing
        """
        if xml_element is None:
            return
            
        # Parse folder
        folder_elem = xml_element.find('folder')
        if folder_elem is not None and folder_elem.text:
            self.save_options['folder'] = folder_elem.text.strip()
            
        # Parse full_data
        full_data_elem = xml_element.find('full_data')
        if full_data_elem is not None:
            interval_elem = full_data_elem.find('interval')
            if interval_elem is not None and interval_elem.text:
                self.save_options['full_data']['interval'] = float(interval_elem.text.strip())
                
            enable_elem = full_data_elem.find('enable')
            if enable_elem is not None and enable_elem.text:
                self.save_options['full_data']['enable'] = enable_elem.text.strip().lower() == 'true'
            
            settings_elem = full_data_elem.find('settings_interval')
            if settings_elem is not None and settings_elem.text:
                self.save_options['full_data']['settings_interval'] = float(settings_elem.text.strip())
                
        # Parse SVG
        svg_elem = xml_element.find('SVG')
        if svg_elem is not None:
            # SVG interval and enable
            svg_interval_elem = svg_elem.find('interval')
            if svg_interval_elem is not None and svg_interval_elem.text:
                self.save_options['SVG']['interval'] = float(svg_interval_elem.text.strip())
                
            svg_enable_elem = svg_elem.find('enable')
            if svg_enable_elem is not None and svg_enable_elem.text:
                self.save_options['SVG']['enable'] = svg_enable_elem.text.strip().lower() == 'true'
                
            # Parse plot_substrate
            plot_substrate_elem = svg_elem.find('plot_substrate')
            if plot_substrate_elem is not None:
                enabled_attr = plot_substrate_elem.get('enabled')
                if enabled_attr:
                    self.save_options['SVG']['plot_substrate']['enabled'] = enabled_attr.lower() == 'true'
                    
                limits_attr = plot_substrate_elem.get('limits')
                if limits_attr:
                    self.save_options['SVG']['plot_substrate']['limits'] = limits_attr.lower() == 'true'
                    
                substrate_elem = plot_substrate_elem.find('substrate')
                if substrate_elem is not None and substrate_elem.text:
                    self.save_options['SVG']['plot_substrate']['substrate'] = substrate_elem.text.strip()
                    
                colormap_elem = plot_substrate_elem.find('colormap')
                if colormap_elem is not None and colormap_elem.text:
                    self.save_options['SVG']['plot_substrate']['colormap'] = colormap_elem.text.strip()
                    
                min_conc_elem = plot_substrate_elem.find('min_conc')
                if min_conc_elem is not None and min_conc_elem.text:
                    self.save_options['SVG']['plot_substrate']['min_conc'] = float(min_conc_elem.text.strip())
                    
                max_conc_elem = plot_substrate_elem.find('max_conc')
                if max_conc_elem is not None and max_conc_elem.text:
                    self.save_options['SVG']['plot_substrate']['max_conc'] = float(max_conc_elem.text.strip())
                    
            # Parse legend (optional, only if present)
            legend_elem = svg_elem.find('legend')
            if legend_elem is not None:
                enabled_attr = legend_elem.get('enabled')
                if enabled_attr:
                    self.save_options['SVG']['legend']['enabled'] = enabled_attr.lower() == 'true'
                    
                cell_phase_elem = legend_elem.find('cell_phase')
                if cell_phase_elem is not None and cell_phase_elem.text:
                    self.save_options['SVG']['legend']['cell_phase'] = cell_phase_elem.text.strip().lower() == 'true'
                    
                cell_type_elem = legend_elem.find('cell_type')
                if cell_type_elem is not None and cell_type_elem.text:
                    self.save_options['SVG']['legend']['cell_type'] = cell_type_elem.text.strip().lower() == 'true'
                    
        # Parse legacy_data
        legacy_elem = xml_element.find('legacy_data')
        if legacy_elem is not None:
            enable_elem = legacy_elem.find('enable')
            if enable_elem is not None and enable_elem.text:
                self.save_options['legacy_data']['enable'] = enable_elem.text.strip().lower() == 'true'
    
    def get_save_options(self) -> Dict[str, Any]:
        """Get all save options."""
        return copy.deepcopy(self.save_options)
