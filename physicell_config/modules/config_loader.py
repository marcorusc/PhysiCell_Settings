"""
Configuration loader for PhysiCell default parameters.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Loads and manages default PhysiCell configuration parameters."""
    
    def __init__(self):
        self._config = None
        self._config_path = Path(__file__).parent.parent / "config" / "default_parameters.json"
    
    @property
    def config(self) -> Dict[str, Any]:
        """Lazy load configuration from JSON file."""
        if self._config is None:
            self._load_config()
        return self._config
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self._config_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self._config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def get_cycle_model(self, model_name: str) -> Dict[str, Any]:
        """Get cycle model configuration by name."""
        models = self.config.get("cell_cycle_models", {})
        if model_name not in models:
            raise ValueError(f"Unknown cycle model: {model_name}")
        return models[model_name].copy()
    
    def get_death_model(self, model_name: str) -> Dict[str, Any]:
        """Get death model configuration by name."""
        models = self.config.get("death_models", {})
        if model_name not in models:
            raise ValueError(f"Unknown death model: {model_name}")
        return models[model_name].copy()
    
    def get_volume_defaults(self) -> Dict[str, Any]:
        """Get default volume parameters."""
        return self.config.get("volume_defaults", {}).copy()
    
    def get_mechanics_defaults(self) -> Dict[str, Any]:
        """Get default mechanics parameters."""
        return self.config.get("mechanics_defaults", {}).copy()
    
    def get_motility_defaults(self) -> Dict[str, Any]:
        """Get default motility parameters."""
        return self.config.get("motility_defaults", {}).copy()
    
    def get_secretion_defaults(self) -> Dict[str, Any]:
        """Get default secretion parameters."""
        return self.config.get("secretion_defaults", {}).copy()
    
    def get_cell_interactions_defaults(self) -> Dict[str, Any]:
        """Get default cell interactions parameters."""
        return self.config.get("cell_interactions_defaults", {}).copy()
    
    def get_cell_transformations_defaults(self) -> Dict[str, Any]:
        """Get default cell transformations parameters."""
        return self.config.get("cell_transformations_defaults", {}).copy()
    
    def get_cell_integrity_defaults(self) -> Dict[str, Any]:
        """Get default cell integrity parameters."""
        return self.config.get("cell_integrity_defaults", {}).copy()
    
    def get_custom_data_defaults(self, data_type: str = "sample") -> Dict[str, Any]:
        """Get default custom data parameters."""
        defaults = self.config.get("custom_data_defaults", {})
        if data_type in defaults:
            return defaults[data_type].copy()
        return defaults.get("sample", {}).copy()
    
    def get_initial_parameter_distributions_defaults(self) -> Dict[str, Any]:
        """Get default initial parameter distributions."""
        return self.config.get("initial_parameter_distributions_defaults", {}).copy()
    
    def get_intracellular_defaults(self, intracellular_type: str = "maboss") -> Dict[str, Any]:
        """Get default intracellular parameters."""
        defaults = self.config.get("intracellular_defaults", {})
        if intracellular_type in defaults:
            return defaults[intracellular_type].copy()
        return {}
    
    def get_cell_type_template(self, template_name: str) -> Dict[str, Any]:
        """Get cell type template configuration."""
        templates = self.config.get("cell_type_templates", {})
        if template_name not in templates:
            raise ValueError(f"Unknown cell type template: {template_name}")
        return templates[template_name].copy()
    
    def get_substrate_defaults(self, substrate_name: str = "substrate") -> Dict[str, Any]:
        """Get default substrate parameters."""
        defaults = self.config.get("substrate_defaults", {})
        if substrate_name in defaults:
            return defaults[substrate_name].copy()
        return defaults.get("substrate", {}).copy()
    
    def get_default_phenotype(self, template: str = "default") -> Dict[str, Any]:
        """Create a complete default phenotype based on template."""
        # Get the template configuration
        try:
            template_config = self.get_cell_type_template(template)
        except ValueError:
            template_config = self.get_cell_type_template("default")
        
        # Build phenotype from defaults
        phenotype = {
            "cycle": self.get_cycle_model(template_config.get("cycle", "flow_cytometry_separated")),
            "death": {
                "apoptosis": self.get_death_model("apoptosis"),
                "necrosis": self.get_death_model("necrosis")
            },
            "volume": self.get_volume_defaults(),
            "mechanics": self.get_mechanics_defaults(),
            "motility": self.get_motility_defaults(),
            "secretion": self.get_secretion_defaults(),
            "cell_interactions": self.get_cell_interactions_defaults(),
            "cell_transformations": self.get_cell_transformations_defaults(),
            "cell_integrity": self.get_cell_integrity_defaults()
        }
        
        # Add intracellular if specified
        if "intracellular" in template_config:
            phenotype["intracellular"] = self.get_intracellular_defaults(template_config["intracellular"])
        
        return phenotype


# Global instance
config_loader = ConfigLoader()
