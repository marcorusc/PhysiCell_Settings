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
    
    def add_rule(self, cell_type: str, signal: str, direction: str,
                behavior: str, saturation_value: float = 0.0,
                half_max: float = 0.5, hill_power: float = 4.0,
                apply_to_dead: int = 0) -> None:
        """Add a single rule to ``cell_rules``.

        The rule follows the PhysiCell CBHG v3.0 CSV format:
        ``cell_type, signal, direction, behavior, saturation_value, half_max, hill_power, apply_to_dead``

        Parameters
        ----------
        cell_type:
            Name of the cell type this rule applies to.
        signal:
            Signal that triggers the behavior (e.g., ``'oxygen'``,
            ``'contact with tumor'``).
        direction:
            ``'increases'`` or ``'decreases'`` — how the signal affects
            the behavior.
        behavior:
            The behavior being modulated (e.g., ``'cycle entry'``,
            ``'apoptosis'``, ``'migration speed'``).
        saturation_value:
            Value of the behavior when the signal is at saturation.
        half_max:
            Signal value at which the behavior is halfway between its
            base value and the saturation value.
        hill_power:
            Exponent of the Hill function controlling the response curve.
        apply_to_dead:
            ``1`` if the rule should be evaluated for dead cells, ``0``
            otherwise.
        """
        if direction not in ('increases', 'decreases'):
            raise ValueError(
                f"Invalid direction '{direction}'. Must be 'increases' or 'decreases'")
        if apply_to_dead not in (0, 1):
            raise ValueError(
                f"Invalid apply_to_dead value '{apply_to_dead}'. Must be 0 or 1")
        rule = {
            'cell_type': cell_type,
            'signal': signal,
            'direction': direction,
            'behavior': behavior,
            'saturation_value': saturation_value,
            'half_max': half_max,
            'hill_power': hill_power,
            'apply_to_dead': apply_to_dead
        }
        self.rules.append(rule)
    
    def load_rules_from_csv(self, filename: str) -> None:
        """Read rule definitions from a PhysiCell rules CSV file.

        The CSV is expected to have **no header row** and follow the
        CBHG v3.0 column order::

            cell_type,signal,direction,behavior,saturation_value,half_max,hill_power,apply_to_dead

        Parameters
        ----------
        filename:
            Path to the CSV file (e.g., produced by :class:`CellRulesCSV`).
        """
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    # Skip empty lines
                    if not row or all(c.strip() == '' for c in row):
                        continue
                    if len(row) < 8:
                        raise ValueError(
                            f"Expected 8 columns but got {len(row)}: {row}")
                    rule = {
                        'cell_type': row[0].strip(),
                        'signal': row[1].strip(),
                        'direction': row[2].strip(),
                        'behavior': row[3].strip(),
                        'saturation_value': float(row[4]),
                        'half_max': float(row[5]),
                        'hill_power': float(row[6]),
                        'apply_to_dead': int(row[7])
                    }
                    self.rules.append(rule)
        except FileNotFoundError:
            raise FileNotFoundError(f"Rules file '{filename}' not found")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error loading rules from '{filename}': {str(e)}")
    
    def save_rules_to_csv(self, filename: str) -> None:
        """Write all currently stored rules to a PhysiCell-compatible CSV file.

        The output has **no header row** and follows the CBHG v3.0 column
        order::

            cell_type,signal,direction,behavior,saturation_value,half_max,hill_power,apply_to_dead

        Parameters
        ----------
        filename:
            Destination path for the generated CSV.
        """
        if not self.rules:
            raise ValueError("No rules to save")

        try:
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for rule in self.rules:
                    writer.writerow([
                        rule['cell_type'],
                        rule['signal'],
                        rule['direction'],
                        rule['behavior'],
                        rule['saturation_value'],
                        rule['half_max'],
                        rule['hill_power'],
                        rule['apply_to_dead']
                    ])
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

        # Add settings element (required by PhysiCell)
        self._create_element(cell_rules_elem, "settings")

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
