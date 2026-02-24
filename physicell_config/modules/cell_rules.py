"""
Cell rules configuration module for PhysiCell.

Handles both the XML ``<cell_rules>`` section (rulesets) and the actual rule
content written to CSV files, including signals/behaviors registry, context-
aware validation, and discovery helpers.
"""

from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import xml.etree.ElementTree as ET
import csv
import os
from .base import BaseModule
from ..config.embedded_signals_behaviors import get_signals_behaviors

if TYPE_CHECKING:
    from ..config_builder_modular import PhysiCellConfig


class CellRulesModule(BaseModule):
    """Handles cell rules configuration for PhysiCell simulations.

    This module manages both sides of PhysiCell's cell-rules system:

    * **XML side** – the ``<cell_rules><rulesets>`` section that tells PhysiCell
      which CSV files to load at runtime (:meth:`add_ruleset`, :meth:`add_to_xml`).
    * **CSV content side** – the actual rules written into those CSV files
      (:meth:`add_rule`, :meth:`save_rules_to_csv` / :meth:`generate_csv`).

    An embedded registry of known signals and behaviors is loaded on
    construction and used for soft validation (warnings, not hard errors).
    Call :meth:`update_context_from_config` (or access through
    ``PhysiCellConfig``) to keep the registry context in sync with the
    cell types and substrates defined in your configuration.
    """

    def __init__(self, config: 'PhysiCellConfig'):
        super().__init__(config)
        self.rulesets = {}
        self.rules = []
        self.include_settings = True  # Whether to emit <settings /> in XML

        # Load signals/behaviors registry from embedded data
        self._signals_behaviors = self._load_signals_behaviors()

        # Initialise context from the config already available
        if config is not None:
            self.update_context_from_config(config)

    # ------------------------------------------------------------------
    # Signals / behaviors registry
    # ------------------------------------------------------------------

    def _load_signals_behaviors(self) -> Dict[str, Any]:
        """Load the signals and behaviors registry from embedded data."""
        try:
            return get_signals_behaviors()
        except Exception as exc:
            raise ValueError(
                f"Failed to load embedded signals and behaviors data: {exc}"
            ) from exc

    def update_context_from_config(self, config: 'PhysiCellConfig') -> None:
        """Sync available cell types and substrates from *config*.

        Call this whenever you add new cell types or substrates so that the
        validation warnings stay accurate.

        Parameters
        ----------
        config:
            The :class:`~physicell_config.config_builder_modular.PhysiCellConfig`
            instance to read cell types and substrates from.
        """
        if hasattr(config, 'cell_types') and config.cell_types.cell_types:
            self._signals_behaviors['context']['cell_types'] = list(
                config.cell_types.cell_types.keys()
            )

        if hasattr(config, 'substrates') and config.substrates.substrates:
            self._signals_behaviors['context']['substrates'] = list(
                config.substrates.substrates.keys()
            )

        custom_vars: set = set()
        if hasattr(config, 'cell_types') and config.cell_types.cell_types:
            for ct_data in config.cell_types.cell_types.values():
                if 'custom_data' in ct_data:
                    custom_vars.update(ct_data['custom_data'].keys())
        self._signals_behaviors['context']['custom_variables'] = list(custom_vars)

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def get_available_signals(
        self, filter_by_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Return available signals, optionally filtered by type.

        Parameters
        ----------
        filter_by_type:
            If given, only signals whose ``type`` field matches this string
            are returned (e.g. ``'contact'``, ``'substrate'``).
        """
        signals = self._signals_behaviors['signals']
        if filter_by_type:
            return {k: v for k, v in signals.items() if v['type'] == filter_by_type}
        return signals.copy()

    def get_available_behaviors(
        self, filter_by_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Return available behaviors, optionally filtered by type.

        Parameters
        ----------
        filter_by_type:
            If given, only behaviors whose ``type`` field matches this string
            are returned (e.g. ``'interaction'``, ``'motility'``).
        """
        behaviors = self._signals_behaviors['behaviors']
        if filter_by_type:
            return {k: v for k, v in behaviors.items() if v['type'] == filter_by_type}
        return behaviors.copy()

    def get_context(self) -> Dict[str, List[str]]:
        """Return current context (cell types, substrates, custom variables)."""
        return self._signals_behaviors['context'].copy()

    def get_signal_by_name(self, signal_name: str) -> Optional[Dict[str, Any]]:
        """Look up a signal by its human-readable name.

        Returns
        -------
        dict or None
            Signal metadata dict (including ``'id'``) or ``None`` if not found.
        """
        for sid, info in self._signals_behaviors['signals'].items():
            if info['name'] == signal_name:
                return {'id': sid, **info}
        return None

    def get_behavior_by_name(self, behavior_name: str) -> Optional[Dict[str, Any]]:
        """Look up a behavior by its human-readable name.

        Returns
        -------
        dict or None
            Behavior metadata dict (including ``'id'``) or ``None`` if not found.
        """
        for bid, info in self._signals_behaviors['behaviors'].items():
            if info['name'] == behavior_name:
                return {'id': bid, **info}
        return None
    
    # ------------------------------------------------------------------
    # Context-aware signal / behavior validation (soft – warns only)
    # ------------------------------------------------------------------

    def _is_valid_context_signal(self, signal_name: str) -> bool:
        """Return ``True`` if *signal_name* is valid in the current context."""
        if self.get_signal_by_name(signal_name):
            return True

        context = self._signals_behaviors['context']

        if signal_name in context['substrates']:
            return True

        if signal_name.startswith('contact with '):
            cell_type = signal_name[13:]
            if cell_type in context['cell_types']:
                return True

        if signal_name.startswith('custom:'):
            var_name = signal_name[7:]
            if var_name in context['custom_variables']:
                return True

        if signal_name in {'apoptotic', 'necrotic', 'dead', 'pressure',
                           'volume', 'damage', 'attacking', 'time'}:
            return True

        return False

    def _is_valid_context_behavior(self, behavior_name: str) -> bool:
        """Return ``True`` if *behavior_name* is valid in the current context."""
        if self.get_behavior_by_name(behavior_name):
            return True

        context = self._signals_behaviors['context']

        for substrate in context['substrates']:
            if behavior_name in (
                f"{substrate} secretion",
                f"{substrate} uptake",
                f"{substrate} export",
                f"chemotactic response to {substrate}",
            ):
                return True

        for cell_type in context['cell_types']:
            if behavior_name in (
                f"transform to {cell_type}",
                f"transition to {cell_type}",
                f"attack {cell_type}",
                f"phagocytose {cell_type}",
                f"fuse to {cell_type}",
                f"adhesive affinity to {cell_type}",
                f"immunogenicity to {cell_type}",
            ):
                return True

        if behavior_name.endswith(' secretion'):
            substrate_name = behavior_name[:-10]
            if substrate_name in context['substrates']:
                return True

        if behavior_name.startswith('custom:'):
            var_name = behavior_name[7:]
            if var_name in context['custom_variables']:
                return True

        return False

    def _validate_rule(
        self,
        cell_type: str,
        signal: str,
        direction: str,
        behavior: str,
        saturation_value: float,
        half_max: float,
        hill_power: float,
        apply_to_dead: int,
    ) -> None:
        """Validate rule parameters, raising ``ValueError`` on hard failures
        and printing warnings for soft (registry) mismatches.
        """
        valid_directions = self._signals_behaviors.get('directions', ['increases', 'decreases'])
        if direction not in valid_directions:
            raise ValueError(
                f"Invalid direction '{direction}'. Must be one of: {valid_directions}"
            )

        if apply_to_dead not in (0, 1):
            raise ValueError(
                f"Invalid apply_to_dead value '{apply_to_dead}'. Must be 0 or 1"
            )

        try:
            float(saturation_value)
            float(half_max)
            float(hill_power)
        except (ValueError, TypeError):
            raise ValueError("saturation_value, half_max, and hill_power must be numeric")

        if not self._is_valid_context_signal(signal):
            print(
                f"Warning: Signal '{signal}' not recognised. "
                "Make sure it is a valid PhysiCell signal or matches your context."
            )

        if not self._is_valid_context_behavior(behavior):
            print(
                f"Warning: Behavior '{behavior}' not recognised. "
                "Make sure it is a valid PhysiCell behavior or matches your context."
            )

        available_cell_types = self._signals_behaviors['context']['cell_types']
        if available_cell_types and cell_type not in available_cell_types:
            print(
                f"Warning: Cell type '{cell_type}' not found in current context. "
                f"Available: {available_cell_types}"
            )

    # ------------------------------------------------------------------
    # Ruleset management (XML side)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Rule management (CSV content side)
    # ------------------------------------------------------------------

    def add_rule(self, cell_type: str, signal: str, direction: str,
                behavior: str, saturation_value: float = 0.0,
                half_max: float = 0.5, hill_power: float = 4.0,
                apply_to_dead: int = 0) -> None:
        """Add a single rule following the PhysiCell CBHG v3.0 CSV format.

        Hard errors are raised for invalid *direction* or *apply_to_dead*
        values. Unrecognised signal/behavior names produce a warning (the
        registry may not cover every custom name you define).

        Parameters
        ----------
        cell_type:
            Name of the cell type this rule applies to.
        signal:
            Signal that triggers the behavior (e.g. ``'oxygen'``,
            ``'contact with tumor'``).
        direction:
            ``'increases'`` or ``'decreases'`` — how the signal affects
            the behavior.
        behavior:
            The behavior being modulated (e.g. ``'cycle entry'``,
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
        self._validate_rule(
            cell_type, signal, direction, behavior,
            saturation_value, half_max, hill_power, apply_to_dead,
        )
        self.rules.append({
            'cell_type': cell_type,
            'signal': signal,
            'direction': direction,
            'behavior': behavior,
            'saturation_value': saturation_value,
            'half_max': half_max,
            'hill_power': hill_power,
            'apply_to_dead': apply_to_dead,
        })
    
    def load_rules_from_csv(self, filename: str) -> None:
        """Read rule definitions from a PhysiCell rules CSV file.

        The CSV is expected to have **no header row** and follow the
        CBHG v3.0 column order::

            cell_type,signal,direction,behavior,saturation_value,half_max,hill_power,apply_to_dead

        Parameters
        ----------
        filename:
            Path to the CSV file.
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

    def generate_csv(self, filename: str) -> str:
        """Alias for :meth:`save_rules_to_csv` that returns the filename.

        Parameters
        ----------
        filename:
            Destination path for the generated CSV.

        Returns
        -------
        str
            The *filename* that was written.
        """
        self.save_rules_to_csv(filename)
        print(f"Generated cell rules CSV: {filename}")
        return filename

    def remove_rule(self, index: int) -> None:
        """Remove a rule by its list index.

        Parameters
        ----------
        index:
            Zero-based index of the rule to remove.

        Raises
        ------
        IndexError
            If *index* is out of range.
        """
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
        else:
            raise IndexError(
                f"Rule index {index} out of range. "
                f"Available: 0–{len(self.rules) - 1}"
            )

    def validate_rules(self) -> List[str]:
        """Validate all stored rules against the registry.

        Returns
        -------
        list of str
            Validation warning/error messages.  An empty list means all
            rules passed.
        """
        messages: List[str] = []
        for i, rule in enumerate(self.rules):
            try:
                self._validate_rule(
                    rule['cell_type'], rule['signal'], rule['direction'],
                    rule['behavior'], rule['saturation_value'],
                    rule['half_max'], rule['hill_power'], rule['apply_to_dead'],
                )
            except ValueError as exc:
                messages.append(f"Rule {i}: {exc}")
        return messages

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_available_signals(self, filter_by_type: Optional[str] = None) -> None:
        """Print available signals in a readable format.

        Parameters
        ----------
        filter_by_type:
            Optional signal type to filter by (e.g. ``'contact'``,
            ``'substrate'``).
        """
        signals = self.get_available_signals(filter_by_type)
        header = f"Available Signals{f' (type: {filter_by_type})' if filter_by_type else ''}:"
        print(f"\n{header}")
        print("-" * 60)
        for sid, info in signals.items():
            req = f" (requires: {', '.join(info['requires'])})" if info['requires'] else ""
            print(f"{sid:2}: {info['name']}{req}")
            print(f"    Type: {info['type']} – {info['description']}")

    def print_available_behaviors(self, filter_by_type: Optional[str] = None) -> None:
        """Print available behaviors in a readable format.

        Parameters
        ----------
        filter_by_type:
            Optional behavior type to filter by (e.g. ``'interaction'``,
            ``'motility'``).
        """
        behaviors = self.get_available_behaviors(filter_by_type)
        header = f"Available Behaviors{f' (type: {filter_by_type})' if filter_by_type else ''}:"
        print(f"\n{header}")
        print("-" * 60)
        for bid, info in behaviors.items():
            req = f" (requires: {', '.join(info['requires'])})" if info['requires'] else ""
            print(f"{bid:2}: {info['name']}{req}")
            print(f"    Type: {info['type']} – {info['description']}")

    def print_context(self) -> None:
        """Print the current context (cell types, substrates, custom variables)."""
        ctx = self.get_context()
        print("\nCurrent Context:")
        print("-" * 30)
        print(f"Cell Types: {ctx['cell_types'] or 'None defined'}")
        print(f"Substrates: {ctx['substrates'] or 'None defined'}")
        print(f"Custom Variables: {ctx['custom_variables'] or 'None defined'}")

    def print_rules(self) -> None:
        """Print all current rules in a readable table."""
        if not self.rules:
            print("No rules defined.")
            return

        print(f"\nCurrent Rules ({len(self.rules)} total):")
        print("-" * 80)
        print(
            f"{'#':<3} {'Cell Type':<20} {'Signal':<20} {'Dir':<9} "
            f"{'Behavior':<20} {'Sat':<8} {'Half':<8} {'Hill':<5} {'Dead':<4}"
        )
        print("-" * 80)
        for i, rule in enumerate(self.rules):
            print(
                f"{i:<3} {rule['cell_type']:<20} {rule['signal']:<20} "
                f"{rule['direction']:<9} {rule['behavior']:<20} "
                f"{rule['saturation_value']:<8} {rule['half_max']:<8} "
                f"{rule['hill_power']:<5} {rule['apply_to_dead']:<4}"
            )

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

        # Add settings element (only when requested)
        if self.include_settings:
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
