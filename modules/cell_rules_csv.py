"""
Cell Rules CSV Generation Module

This module provides functionality to create PhysiCell-compatible cell rules CSV files.
It maintains a JSON registry of all available signals and behaviors, dynamically updates
context based on the current configuration, and generates CSV files in the exact format
expected by PhysiCell.
"""

import json
import os
import csv
from typing import Dict, List, Any, Optional, Union
from .base import BaseModule


class CellRulesCSV(BaseModule):
    """
    Manages cell rules and generates PhysiCell-compatible CSV files.
    
    The CSV format follows: cell_type,signal,direction,behavior,base_value,half_max,hill_power,apply_to_dead
    """
    
    def __init__(self, config_instance=None):
        """
        Initialize the CellRulesCSV module.
        
        Args:
            config_instance: Optional PhysiCellConfig instance to auto-update context
        """
        if config_instance:
            super().__init__(config_instance)
        self.rules = []
        self.signals_behaviors = self._load_signals_behaviors()
        
        if config_instance:
            self.update_context_from_config(config_instance)
    
    def _load_signals_behaviors(self) -> Dict[str, Any]:
        """Load the signals and behaviors configuration from JSON file."""
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'signals_behaviors.json'
        )
        
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"signals_behaviors.json not found at {json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in signals_behaviors.json: {e}")
    
    def update_context_from_config(self, config) -> None:
        """
        Update available cell types and substrates from the main config.
        
        Args:
            config: PhysiCellConfig instance
        """
        # Update cell types
        if hasattr(config, 'cell_types') and config.cell_types.cell_types:
            self.signals_behaviors['context']['cell_types'] = list(config.cell_types.cell_types.keys())
        
        # Update substrates
        if hasattr(config, 'substrates') and config.substrates.substrates:
            self.signals_behaviors['context']['substrates'] = list(config.substrates.substrates.keys())
        
        # Update custom variables from cell types custom data
        custom_vars = set()
        if hasattr(config, 'cell_types') and config.cell_types.cell_types:
            for cell_type_data in config.cell_types.cell_types.values():
                if 'custom_data' in cell_type_data:
                    custom_vars.update(cell_type_data['custom_data'].keys())
        
        self.signals_behaviors['context']['custom_variables'] = list(custom_vars)
    
    def get_available_signals(self, filter_by_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get available signals, optionally filtered by type.
        
        Args:
            filter_by_type: Optional signal type to filter by (e.g., 'contact', 'substrate')
            
        Returns:
            Dictionary of available signals with their metadata
        """
        signals = self.signals_behaviors['signals']
        
        if filter_by_type:
            return {k: v for k, v in signals.items() if v['type'] == filter_by_type}
        
        return signals.copy()
    
    def get_available_behaviors(self, filter_by_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get available behaviors, optionally filtered by type.
        
        Args:
            filter_by_type: Optional behavior type to filter by (e.g., 'interaction', 'motility')
            
        Returns:
            Dictionary of available behaviors with their metadata
        """
        behaviors = self.signals_behaviors['behaviors']
        
        if filter_by_type:
            return {k: v for k, v in behaviors.items() if v['type'] == filter_by_type}
        
        return behaviors.copy()
    
    def get_context(self) -> Dict[str, List[str]]:
        """
        Get current context (available cell types, substrates, custom variables).
        
        Returns:
            Dictionary containing lists of available cell types, substrates, and custom variables
        """
        return self.signals_behaviors['context'].copy()
    
    def get_signal_by_name(self, signal_name: str) -> Optional[Dict[str, Any]]:
        """
        Find signal information by name.
        
        Args:
            signal_name: Name of the signal to find
            
        Returns:
            Signal information dictionary or None if not found
        """
        for signal_id, signal_info in self.signals_behaviors['signals'].items():
            if signal_info['name'] == signal_name:
                return {'id': signal_id, **signal_info}
        return None
    
    def _is_valid_context_signal(self, signal_name: str) -> bool:
        """
        Check if a signal is valid based on current context.
        
        This handles context-dependent signals like substrate names,
        contact with specific cell types, etc.
        """
        # Check if it's a direct registry match first
        if self.get_signal_by_name(signal_name):
            return True
        
        context = self.signals_behaviors['context']
        
        # Check if it's a substrate name (substrate signal)
        if signal_name in context['substrates']:
            return True
            
        # Check if it's "contact with [cell_type]"
        if signal_name.startswith('contact with '):
            cell_type = signal_name[13:]  # Remove "contact with "
            if cell_type in context['cell_types']:
                return True
        
        # Check if it's a custom variable
        if signal_name.startswith('custom:'):
            var_name = signal_name[7:]  # Remove "custom:"
            if var_name in context['custom_variables']:
                return True
        
        # Check for other context-dependent patterns
        # e.g., "apoptotic" and "necrotic" are valid state signals
        if signal_name in ['apoptotic', 'necrotic', 'dead', 'pressure', 'volume', 'damage', 'attacking', 'time']:
            return True
            
        return False
    
    def get_behavior_by_name(self, behavior_name: str) -> Optional[Dict[str, Any]]:
        """
        Find behavior information by name.
        
        Args:
            behavior_name: Name of the behavior to find
            
        Returns:
            Behavior information dictionary or None if not found
        """
        for behavior_id, behavior_info in self.signals_behaviors['behaviors'].items():
            if behavior_info['name'] == behavior_name:
                return {'id': behavior_id, **behavior_info}
        return None
    
    def _is_valid_context_behavior(self, behavior_name: str) -> bool:
        """
        Check if a behavior is valid based on current context.
        
        This handles context-dependent behaviors like substrate secretion,
        transform to specific cell types, attack specific cell types, etc.
        """
        # Check if it's a direct registry match first
        if self.get_behavior_by_name(behavior_name):
            return True
        
        context = self.signals_behaviors['context']
        
        # Check substrate-related behaviors
        for substrate in context['substrates']:
            if behavior_name in [f"{substrate} secretion", f"{substrate} uptake", f"{substrate} export"]:
                return True
            if behavior_name == f"chemotactic response to {substrate}":
                return True
        
        # Check cell type-related behaviors
        for cell_type in context['cell_types']:
            if behavior_name.startswith(f"transform to {cell_type}") or behavior_name == f"transition to {cell_type}":
                return True
            if behavior_name == f"attack {cell_type}":
                return True
            if behavior_name == f"phagocytose {cell_type}":
                return True
            if behavior_name == f"fuse to {cell_type}":
                return True
            if behavior_name == f"adhesive affinity to {cell_type}":
                return True
            if behavior_name == f"immunogenicity to {cell_type}":
                return True
        
        # Check for substrate secretion variants (e.g., "apoptotic debris secretion")
        if behavior_name.endswith(" secretion"):
            substrate_name = behavior_name[:-10]  # Remove " secretion"
            if substrate_name in context['substrates']:
                return True
        
        # Check for custom behaviors
        if behavior_name.startswith('custom:'):
            var_name = behavior_name[7:]  # Remove "custom:"
            if var_name in context['custom_variables']:
                return True
        
        return False
    
    def add_rule(self, cell_type: str, signal: str, direction: str, behavior: str,
                base_value: float, half_max: float, hill_power: float, 
                apply_to_dead: int) -> None:
        """
        Add a cell rule following the exact CSV format.
        
        Args:
            cell_type: Name of the cell type
            signal: Signal name (e.g., 'oxygen', 'contact with tumor')
            direction: 'increases' or 'decreases'
            behavior: Behavior name (e.g., 'cycle entry', 'apoptosis')
            base_value: Base value for the rule
            half_max: Half-maximum value
            hill_power: Hill power coefficient
            apply_to_dead: Whether to apply to dead cells (0 or 1)
        """
        # Validate inputs
        self._validate_rule(cell_type, signal, direction, behavior, 
                          base_value, half_max, hill_power, apply_to_dead)
        
        # Add the rule
        rule = {
            'cell_type': cell_type,
            'signal': signal,
            'direction': direction,
            'behavior': behavior,
            'base_value': base_value,
            'half_max': half_max,
            'hill_power': hill_power,
            'apply_to_dead': apply_to_dead
        }
        
        self.rules.append(rule)
    
    def _validate_rule(self, cell_type: str, signal: str, direction: str, behavior: str,
                      base_value: float, half_max: float, hill_power: float, 
                      apply_to_dead: int) -> None:
        """Validate a rule's parameters."""
        # Check direction
        if direction not in self.signals_behaviors['directions']:
            raise ValueError(f"Invalid direction '{direction}'. Must be one of: {self.signals_behaviors['directions']}")
        
        # Check apply_to_dead
        if apply_to_dead not in [0, 1]:
            raise ValueError(f"Invalid apply_to_dead value '{apply_to_dead}'. Must be 0 or 1")
        
        # Check if signal is valid (either in registry or valid in context)
        if not self._is_valid_context_signal(signal):
            print(f"Warning: Signal '{signal}' not recognized. Make sure it's a valid PhysiCell signal or matches your context.")
        
        # Check if behavior is valid (either in registry or valid in context)
        if not self._is_valid_context_behavior(behavior):
            print(f"Warning: Behavior '{behavior}' not recognized. Make sure it's a valid PhysiCell behavior or matches your context.")
        
        # Check cell type availability
        available_cell_types = self.signals_behaviors['context']['cell_types']
        if available_cell_types and cell_type not in available_cell_types:
            print(f"Warning: Cell type '{cell_type}' not found in current context. Available: {available_cell_types}")
        
        # Validate numeric parameters
        try:
            float(base_value)
            float(half_max)
            float(hill_power)
        except (ValueError, TypeError):
            raise ValueError("base_value, half_max, and hill_power must be numeric")
    
    def remove_rule(self, index: int) -> None:
        """
        Remove a rule by its index.
        
        Args:
            index: Index of the rule to remove
        """
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
        else:
            raise IndexError(f"Rule index {index} out of range. Available: 0-{len(self.rules)-1}")
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get all current rules.
        
        Returns:
            List of rule dictionaries
        """
        return self.rules.copy()
    
    def clear_rules(self) -> None:
        """Clear all rules."""
        self.rules = []
    
    def generate_csv(self, filename: str) -> str:
        """
        Generate PhysiCell-compatible CSV file.
        
        Args:
            filename: Path where to save the CSV file
            
        Returns:
            Path to the generated CSV file
        """
        if not self.rules:
            raise ValueError("No rules to generate. Add rules first using add_rule()")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Write CSV file (no header, following PhysiCell format)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            for rule in self.rules:
                row = [
                    rule['cell_type'],
                    rule['signal'],
                    rule['direction'], 
                    rule['behavior'],
                    rule['base_value'],
                    rule['half_max'],
                    rule['hill_power'],
                    rule['apply_to_dead']
                ]
                writer.writerow(row)
        
        print(f"Generated cell rules CSV: {filename}")
        return filename
    
    def validate_rules(self) -> List[str]:
        """
        Validate all rules and return any warnings or errors.
        
        Returns:
            List of validation messages
        """
        messages = []
        
        for i, rule in enumerate(self.rules):
            try:
                self._validate_rule(
                    rule['cell_type'], rule['signal'], rule['direction'], 
                    rule['behavior'], rule['base_value'], rule['half_max'], 
                    rule['hill_power'], rule['apply_to_dead']
                )
            except ValueError as e:
                messages.append(f"Rule {i}: {e}")
        
        return messages
    
    def print_available_signals(self, filter_by_type: Optional[str] = None) -> None:
        """Print available signals in a readable format."""
        signals = self.get_available_signals(filter_by_type)
        
        print(f"\nAvailable Signals{f' (type: {filter_by_type})' if filter_by_type else ''}:")
        print("-" * 60)
        
        for signal_id, info in signals.items():
            requires_text = f" (requires: {', '.join(info['requires'])})" if info['requires'] else ""
            print(f"{signal_id:2}: {info['name']}{requires_text}")
            print(f"    Type: {info['type']} - {info['description']}")
    
    def print_available_behaviors(self, filter_by_type: Optional[str] = None) -> None:
        """Print available behaviors in a readable format."""
        behaviors = self.get_available_behaviors(filter_by_type)
        
        print(f"\nAvailable Behaviors{f' (type: {filter_by_type})' if filter_by_type else ''}:")
        print("-" * 60)
        
        for behavior_id, info in behaviors.items():
            requires_text = f" (requires: {', '.join(info['requires'])})" if info['requires'] else ""
            print(f"{behavior_id:2}: {info['name']}{requires_text}")
            print(f"    Type: {info['type']} - {info['description']}")
    
    def print_context(self) -> None:
        """Print current context (cell types, substrates, custom variables)."""
        context = self.get_context()
        
        print("\nCurrent Context:")
        print("-" * 30)
        print(f"Cell Types: {context['cell_types'] if context['cell_types'] else 'None defined'}")
        print(f"Substrates: {context['substrates'] if context['substrates'] else 'None defined'}")
        print(f"Custom Variables: {context['custom_variables'] if context['custom_variables'] else 'None defined'}")
    
    def print_rules(self) -> None:
        """Print all current rules in a readable format."""
        if not self.rules:
            print("No rules defined.")
            return
        
        print(f"\nCurrent Rules ({len(self.rules)} total):")
        print("-" * 80)
        print(f"{'#':<3} {'Cell Type':<20} {'Signal':<20} {'Dir':<9} {'Behavior':<20} {'Base':<8} {'Half':<8} {'Hill':<5} {'Dead':<4}")
        print("-" * 80)
        
        for i, rule in enumerate(self.rules):
            print(f"{i:<3} {rule['cell_type']:<20} {rule['signal']:<20} {rule['direction']:<9} "
                  f"{rule['behavior']:<20} {rule['base_value']:<8} {rule['half_max']:<8} "
                  f"{rule['hill_power']:<5} {rule['apply_to_dead']:<4}")
    
    def add_to_xml(self, parent) -> None:
        """
        This module generates CSV files, not XML.
        The XML cell_rules section is handled by the main cell_rules module.
        """
        pass
