"""
Cell rules configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
import csv
import os
from .base import BaseModule


class CellRulesModule(BaseModule):
    """Handles cell rules configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.rulesets = {}
        self.rules = []
    
    def add_ruleset(self, name: str, folder: str = "./config",
                   filename: str = "rules.csv", enabled: bool = True) -> None:
        """Register a CSV ruleset.

        Parameters
        ----------
        name:
            Identifier for the ruleset.
        folder:
            Folder where the CSV file resides.
        filename:
            Name of the CSV file containing the rules.
        enabled:
            Whether the ruleset should be loaded by PhysiCell.
        """
        self.rulesets[name] = {
            'folder': folder,
            'filename': filename,
            'enabled': enabled,
            'protocol': 'CBHG',
            'version': '3.0',
            'format': 'csv'
        }
    
    def add_rule(self, signal: str, behavior: str, cell_type: str,
                min_signal: float = 0.0, max_signal: float = 1.0,
                min_behavior: float = 0.0, max_behavior: float = 1.0,
                hill_power: float = 1.0, half_max: float = 0.5,
                applies_to_dead: bool = False) -> None:
        """Add a single rule to ``cell_rules``.

        Parameters
        ----------
        signal, behavior, cell_type:
            Entities involved in the rule definition.
        min_signal, max_signal:
            Signal range that triggers the behaviour.
        min_behavior, max_behavior:
            Bounds for the resulting behaviour value.
        hill_power, half_max:
            Parameters of the Hill function controlling the response.
        applies_to_dead:
            Set to ``True`` if the rule should be evaluated for dead cells.
        """
        rule = {
            'signal': signal,
            'behavior': behavior,
            'cell_type': cell_type,
            'min_signal': min_signal,
            'max_signal': max_signal,
            'min_behavior': min_behavior,
            'max_behavior': max_behavior,
            'hill_power': hill_power,
            'half_max': half_max,
            'applies_to_dead': applies_to_dead
        }
        self.rules.append(rule)
    
    def load_rules_from_csv(self, filename: str) -> None:
        """Read rule definitions from an external CSV file.

        Parameters
        ----------
        filename:
            Path to the CSV file produced by tools such as :class:`CellRulesCSV`.
        """
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Convert string values to appropriate types
                    rule = {
                        'signal': row.get('signal', ''),
                        'behavior': row.get('behavior', ''),
                        'cell_type': row.get('cell_type', ''),
                        'min_signal': float(row.get('min_signal', 0.0)),
                        'max_signal': float(row.get('max_signal', 1.0)),
                        'min_behavior': float(row.get('min_behavior', 0.0)),
                        'max_behavior': float(row.get('max_behavior', 1.0)),
                        'hill_power': float(row.get('hill_power', 1.0)),
                        'half_max': float(row.get('half_max', 0.5)),
                        'applies_to_dead': row.get('applies_to_dead', 'false').lower() == 'true'
                    }
                    self.rules.append(rule)
        except FileNotFoundError:
            raise FileNotFoundError(f"Rules file '{filename}' not found")
        except Exception as e:
            raise ValueError(f"Error loading rules from '{filename}': {str(e)}")
    
    def save_rules_to_csv(self, filename: str) -> None:
        """Write all currently stored rules to a CSV file.

        Parameters
        ----------
        filename:
            Destination path for the generated CSV.
        """
        if not self.rules:
            raise ValueError("No rules to save")
        
        fieldnames = ['signal', 'behavior', 'cell_type', 'min_signal', 'max_signal',
                     'min_behavior', 'max_behavior', 'hill_power', 'half_max', 'applies_to_dead']
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for rule in self.rules:
                    writer.writerow(rule)
        except Exception as e:
            raise ValueError(f"Error saving rules to '{filename}': {str(e)}")
    
    def add_to_xml(self, parent: ET.Element) -> None:
        """Serialize cell rules into the PhysiCell XML tree.

        Parameters
        ----------
        parent:
            Parent XML element representing ``microenvironment_setup``.
        """
        # Always add cell_rules section, even if empty or disabled
        cell_rules_elem = self._create_element(parent, "cell_rules")
        
        # Add rulesets
        rulesets_elem = self._create_element(cell_rules_elem, "rulesets")
        
        if self.rulesets:
            for name, ruleset in self.rulesets.items():
                ruleset_elem = self._create_element(rulesets_elem, "ruleset")
                ruleset_elem.set("protocol", ruleset.get('protocol', 'CBHG'))
                ruleset_elem.set("version", ruleset.get('version', '3.0'))
                ruleset_elem.set("format", ruleset.get('format', 'csv'))
                ruleset_elem.set("enabled", str(ruleset['enabled']).lower())
                
                self._create_element(ruleset_elem, "folder", ruleset['folder'])
                self._create_element(ruleset_elem, "filename", ruleset['filename'])
        else:
            # Add default disabled ruleset for standard structure
            ruleset_elem = self._create_element(rulesets_elem, "ruleset")
            ruleset_elem.set("protocol", "CBHG")
            ruleset_elem.set("version", "3.0")
            ruleset_elem.set("format", "csv")
            ruleset_elem.set("enabled", "false")
            
            self._create_element(ruleset_elem, "folder", "./config")
            self._create_element(ruleset_elem, "filename", "cell_rules.csv")
    
    def load_from_xml(self, xml_element: Optional[ET.Element]) -> None:
        """Load cell rules configuration from XML element.
        
        Args:
            xml_element: XML element containing cell rules configuration, or None if missing
        """
        if xml_element is None:
            return
            
        # Clear existing rulesets
        self.rulesets = {}
        
        # Parse rulesets
        rulesets_elem = xml_element.find('rulesets')
        if rulesets_elem is not None:
            for ruleset_elem in rulesets_elem.findall('ruleset'):
                # Get attributes
                protocol = ruleset_elem.get('protocol', 'CBHG')
                version = ruleset_elem.get('version', '3.0')
                format_type = ruleset_elem.get('format', 'csv')
                enabled = ruleset_elem.get('enabled', 'false').lower() == 'true'
                
                # Get folder and filename
                folder_elem = ruleset_elem.find('folder')
                filename_elem = ruleset_elem.find('filename')
                
                if folder_elem is not None and filename_elem is not None:
                    folder = folder_elem.text.strip() if folder_elem.text else './config'
                    filename = filename_elem.text.strip() if filename_elem.text else 'cell_rules.csv'
                    
                    base_name = os.path.splitext(filename)[0]
                    ruleset_name = base_name
                    counter = 1
                    while ruleset_name in self.rulesets:
                        ruleset_name = f"{base_name}_{counter}"
                        counter += 1
                    
                    # Add the ruleset
                    self.rulesets[ruleset_name] = {
                        'folder': folder,
                        'filename': filename,
                        'enabled': enabled,
                        'protocol': protocol,
                        'version': version,
                        'format': format_type
                    }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Return a copy of all stored rule dictionaries."""
        return self.rules.copy()
    
    def get_rulesets(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the registered rulesets."""
        return self.rulesets.copy()
    
    def clear_rules(self) -> None:
        """Remove every rule from the internal list."""
        self.rules.clear()
    
    def clear_rulesets(self) -> None:
        """Remove all registered rulesets."""
        self.rulesets.clear()
