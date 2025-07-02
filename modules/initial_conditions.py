"""
Initial conditions configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .base import BaseModule


class InitialConditionsModule(BaseModule):
    """Handles initial conditions configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.initial_conditions = []
    
    def add_cell_cluster(self, cell_type: str, x: float, y: float, z: float = 0.0,
                        radius: float = 100.0, num_cells: int = 100) -> None:
        """Add a cluster of cells at specified location."""
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
        """Add a single cell at specified location."""
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
        """Add cells in a rectangular region."""
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
        """Add CSV file for cell positions."""
        self.initial_conditions = {
            'type': 'csv',
            'filename': filename,
            'folder': folder,
            'enabled': enabled
        }
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Add initial conditions configuration to XML."""
        initial_elem = self._create_element(parent, "initial_conditions")
        
        # Default CSV cell positions structure
        cell_positions_elem = self._create_element(initial_elem, "cell_positions")
        cell_positions_elem.set("type", "csv")
        
        if hasattr(self, 'initial_conditions') and isinstance(self.initial_conditions, dict):
            cell_positions_elem.set("enabled", str(self.initial_conditions.get('enabled', False)).lower())
            if self.initial_conditions.get('folder'):
                self._create_element(cell_positions_elem, "folder", self.initial_conditions['folder'])
            if self.initial_conditions.get('filename'):
                self._create_element(cell_positions_elem, "filename", self.initial_conditions['filename'])
        else:
            cell_positions_elem.set("enabled", "false")
            self._create_element(cell_positions_elem, "folder", "./config")
            self._create_element(cell_positions_elem, "filename", "cells.csv")
    
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
    
    def _add_file_xml(self, parent: ET.Element, condition: Dict[str, Any]) -> None:
        """Add file-based initial condition XML element."""
        file_elem = self._create_element(parent, "cell_positions")
        file_elem.set("type", condition['cell_type'])
        file_elem.set("enabled", "true")
        
        self._create_element(file_elem, "filename", condition['filename'])
    
    def get_conditions(self) -> List[Dict[str, Any]]:
        """Get all initial conditions."""
        return self.initial_conditions.copy()
    
    def clear_conditions(self) -> None:
        """Clear all initial conditions."""
        self.initial_conditions.clear()
