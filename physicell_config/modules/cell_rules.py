"""
Cell rules configuration module for PhysiCell.
"""

from typing import Dict, Any, List, Optional, Tuple
import xml.etree.ElementTree as ET
import csv
from .base import BaseModule


class CellRulesModule(BaseModule):
    """Handles cell rules configuration for PhysiCell simulations."""
    
    def __init__(self, config):
        super().__init__(config)
        self.rulesets = {}
        self.rules = []
    
    def add_ruleset(self, name: str, folder: str = "./config", 
                   filename: str = "rules.csv", enabled: bool = True) -> None:
        """Add a ruleset to the configuration."""
        self.rulesets[name] = {
            'folder': folder,
            'filename': filename,
            'enabled': enabled
        }
    
    def add_rule(self, signal: str, behavior: str, cell_type: str,
                min_signal: float = 0.0, max_signal: float = 1.0,
                min_behavior: float = 0.0, max_behavior: float = 1.0,
                hill_power: float = 1.0, half_max: float = 0.5,
                applies_to_dead: bool = False) -> None:
        """Add a cell rule."""
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
        """Load rules from a CSV file."""
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
        """Save rules to a CSV file."""
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
        """Add cell rules configuration to XML."""
        # Always add cell_rules section, even if empty or disabled
        cell_rules_elem = self._create_element(parent, "cell_rules")
        
        # Add rulesets
        rulesets_elem = self._create_element(cell_rules_elem, "rulesets")
        
        if self.rulesets:
            for name, ruleset in self.rulesets.items():
                ruleset_elem = self._create_element(rulesets_elem, "ruleset")
                ruleset_elem.set("protocol", "CBHG")
                ruleset_elem.set("version", "3.0")
                ruleset_elem.set("format", "csv")
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
        
        # Add settings (empty for now)
        self._create_element(cell_rules_elem, "settings")
        
        # Add settings (empty for now)
        self._create_element(cell_rules_elem, "settings")
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all rules."""
        return self.rules.copy()
    
    def get_rulesets(self) -> Dict[str, Dict[str, Any]]:
        """Get all rulesets."""
        return self.rulesets.copy()
    
    def clear_rules(self) -> None:
        """Clear all rules."""
        self.rules.clear()
    
    def clear_rulesets(self) -> None:
        """Clear all rulesets."""
        self.rulesets.clear()
