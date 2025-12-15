"""Placement of cells at the start of the simulation."""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from copy import deepcopy
from .base import BaseModule


class InitialConditionsModule(BaseModule):
    """Define initial cell locations and placement files."""
    
    def __init__(self, config):
        super().__init__(config)
        self.initial_conditions: List[Dict[str, Any]] = []
        self.csv_config = {
            'type': 'csv',
            'filename': 'cells.csv',
            'folder': './config',
            'enabled': False
        }
    
    def add_cell_cluster(self, cell_type: str, x: float, y: float, z: float = 0.0,
                        radius: float = 100.0, num_cells: int = 100) -> None:
        """Place a spherical cluster of cells.

        Parameters
        ----------
        cell_type:
            Cell type name.
        x, y, z:
            Coordinates of the cluster centre.
        radius:
            Sphere radius in microns.
        num_cells:
            Number of cells to generate.
        """
        condition = {
            'type': 'cluster',
            'cell_type': cell_type,
            'x': x,
            'y': y,
            'z': z,
            'radius': radius,
            'num_cells': num_cells
        }
        self.initial_conditions.append(condition)
    
    def add_single_cell(self, cell_type: str, x: float, y: float, z: float = 0.0) -> None:
        """Place one cell in the simulation domain.

        Parameters
        ----------
        cell_type:
            Cell type name.
        x, y, z:
            Coordinates of the cell.
        """
        condition = {
            'type': 'single',
            'cell_type': cell_type,
            'x': x,
            'y': y,
            'z': z
        }
        self.initial_conditions.append(condition)
    
    def add_rectangular_region(self, cell_type: str, x_min: float, x_max: float,
                              y_min: float, y_max: float, z_min: float = -5.0,
                              z_max: float = 5.0, density: float = 0.8) -> None:
        """Fill a rectangular region with randomly placed cells.

        Parameters
        ----------
        cell_type:
            Name of the cell type.
        x_min, x_max, y_min, y_max, z_min, z_max:
            Bounds of the region.
        density:
            Fraction of the region volume filled with cells (0-1).
        """
        condition = {
            'type': 'rectangle',
            'cell_type': cell_type,
            'x_min': x_min,
            'x_max': x_max,
            'y_min': y_min,
            'y_max': y_max,
            'z_min': z_min,
            'z_max': z_max,
            'density': density
        }
        self.initial_conditions.append(condition)
    
    def add_csv_file(self, filename: str, folder: str = "./config", enabled: bool = False) -> None:
        """Specify an external CSV file for cell positions.

        Parameters
        ----------
        filename:
            CSV file name.
        folder:
            Folder containing the file.
        enabled:
            Whether PhysiCell should load the file.
        """
        self.csv_config = {
            'type': 'csv',
            'filename': filename,
            'folder': folder,
            'enabled': enabled
        }
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add initial conditions configuration to XML."""
        initial_elem = self._create_element(parent, "initial_conditions")
        
        # CSV cell positions structure
        cell_positions_elem = self._create_element(initial_elem, "cell_positions")
        cell_positions_elem.set("type", self.csv_config.get('type', 'csv'))
        cell_positions_elem.set("enabled", str(self.csv_config.get('enabled', False)).lower())
        self._create_element(cell_positions_elem, "folder", self.csv_config.get('folder', './config'))
        self._create_element(cell_positions_elem, "filename", self.csv_config.get('filename', 'cells.csv'))
        
        # Add explicit placements, if any
        for condition in self.initial_conditions:
            ctype = condition.get('type')
            if ctype == 'cluster':
                self._add_cluster_xml(initial_elem, condition)
            elif ctype == 'single':
                self._add_single_cell_xml(initial_elem, condition)
            elif ctype == 'rectangle':
                self._add_rectangle_xml(initial_elem, condition)
    
    def _add_cluster_xml(self, parent: ET.Element, condition: Dict[str, Any]) -> None:
        """Add cluster XML element."""
        cluster_elem = self._create_element(parent, "cell_cluster")
        cluster_elem.set("type", condition['cell_type'])
        
        self._create_element(cluster_elem, "x", condition['x'])
        self._create_element(cluster_elem, "y", condition['y'])
        self._create_element(cluster_elem, "z", condition['z'])
        self._create_element(cluster_elem, "radius", condition['radius'])
        self._create_element(cluster_elem, "num_cells", condition['num_cells'])
    
    def _add_single_cell_xml(self, parent: ET.Element, condition: Dict[str, Any]) -> None:
        """Add single cell XML element."""
        cell_elem = self._create_element(parent, "cell")
        cell_elem.set("type", condition['cell_type'])
        
        self._create_element(cell_elem, "x", condition['x'])
        self._create_element(cell_elem, "y", condition['y'])
        self._create_element(cell_elem, "z", condition['z'])
    
    def _add_rectangle_xml(self, parent: ET.Element, condition: Dict[str, Any]) -> None:
        """Add rectangular region XML element."""
        region_elem = self._create_element(parent, "cell_region")
        region_elem.set("type", condition['cell_type'])
        
        self._create_element(region_elem, "x_min", condition['x_min'])
        self._create_element(region_elem, "x_max", condition['x_max'])
        self._create_element(region_elem, "y_min", condition['y_min'])
        self._create_element(region_elem, "y_max", condition['y_max'])
        self._create_element(region_elem, "z_min", condition['z_min'])
        self._create_element(region_elem, "z_max", condition['z_max'])
        self._create_element(region_elem, "density", condition['density'])
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load initial conditions configuration from XML element.
        
        Args:
            xml_element: XML element containing initial conditions configuration, or None if missing
        """
        if xml_element is None:
            # No initial conditions section, keep defaults
            return
            
        # Look for cell_positions element
        cell_positions_elem = xml_element.find('cell_positions')
        if cell_positions_elem is not None:
            # Parse attributes
            position_type = cell_positions_elem.get('type', 'csv')
            enabled = cell_positions_elem.get('enabled', 'false').lower() == 'true'
            
            folder_elem = cell_positions_elem.find('folder')
            filename_elem = cell_positions_elem.find('filename')
            
            folder = folder_elem.text.strip() if folder_elem is not None and folder_elem.text else "./config"
            filename = filename_elem.text.strip() if filename_elem is not None and filename_elem.text else "cells.csv"
            
            self.csv_config = {
                'type': position_type,
                'folder': folder,
                'filename': filename,
                'enabled': enabled
            }
        
        # Clear existing explicit placements and parse new ones
        self.initial_conditions = []
        
        for cluster_elem in xml_element.findall('cell_cluster'):
            cell_type = cluster_elem.get('type', '')
            condition = {
                'type': 'cluster',
                'cell_type': cell_type,
                'x': self._safe_get_text(cluster_elem, 'x', 0.0, float),
                'y': self._safe_get_text(cluster_elem, 'y', 0.0, float),
                'z': self._safe_get_text(cluster_elem, 'z', 0.0, float),
                'radius': self._safe_get_text(cluster_elem, 'radius', 100.0, float),
                'num_cells': self._safe_get_text(cluster_elem, 'num_cells', 0, int)
            }
            self.initial_conditions.append(condition)
        
        for cell_elem in xml_element.findall('cell'):
            cell_type = cell_elem.get('type', '')
            condition = {
                'type': 'single',
                'cell_type': cell_type,
                'x': self._safe_get_text(cell_elem, 'x', 0.0, float),
                'y': self._safe_get_text(cell_elem, 'y', 0.0, float),
                'z': self._safe_get_text(cell_elem, 'z', 0.0, float)
            }
            self.initial_conditions.append(condition)
        
        for region_elem in xml_element.findall('cell_region'):
            cell_type = region_elem.get('type', '')
            condition = {
                'type': 'rectangle',
                'cell_type': cell_type,
                'x_min': self._safe_get_text(region_elem, 'x_min', 0.0, float),
                'x_max': self._safe_get_text(region_elem, 'x_max', 0.0, float),
                'y_min': self._safe_get_text(region_elem, 'y_min', 0.0, float),
                'y_max': self._safe_get_text(region_elem, 'y_max', 0.0, float),
                'z_min': self._safe_get_text(region_elem, 'z_min', -5.0, float),
                'z_max': self._safe_get_text(region_elem, 'z_max', 5.0, float),
                'density': self._safe_get_text(region_elem, 'density', 0.8, float)
            }
            self.initial_conditions.append(condition)
    
    def get_conditions(self) -> List[Dict[str, Any]]:
        """Return a copy of all currently defined explicit placements."""
        return deepcopy(self.initial_conditions)
    
    def clear_conditions(self) -> None:
        """Remove all stored initial conditions."""
        self.initial_conditions.clear()
