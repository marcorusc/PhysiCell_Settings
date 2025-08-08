"""Placement of cells at the start of the simulation."""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
from .base import BaseModule


class InitialConditionsModule(BaseModule):
    """Define initial cell locations and placement files."""
    
    def __init__(self, config):
        super().__init__(config)
        self.initial_conditions = []
    
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
            
            # For CSV type, parse folder and filename
            if position_type == 'csv':
                folder_elem = cell_positions_elem.find('folder')
                filename_elem = cell_positions_elem.find('filename')
                
                folder = folder_elem.text.strip() if folder_elem is not None and folder_elem.text else "./config"
                filename = filename_elem.text.strip() if filename_elem is not None and filename_elem.text else "cells.csv"
                
                # Store as CSV configuration (overwrites any existing conditions)
                self.initial_conditions = {
                    'type': 'csv',
                    'folder': folder,
                    'filename': filename,
                    'enabled': enabled
                }
            # Future: could add support for other position types (clusters, rectangles, etc.)
            # For now, we focus on the CSV format which is what PhysiCell typically uses
    
    def get_conditions(self) -> List[Dict[str, Any]]:
        """Return a copy of all currently defined conditions."""
        return self.initial_conditions.copy()
    
    def clear_conditions(self) -> None:
        """Remove all stored initial conditions."""
        self.initial_conditions.clear()
