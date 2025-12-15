"""
Embedded default parameters for PhysiCell configuration.

This module contains all default parameters previously stored in default_parameters.json,
now embedded directly in Python code to avoid file system dependencies in containerized
environments like MCP agents.

Generated from default_parameters.json on 2025-07-20
"""

from typing import Dict, Any

DEFAULT_PARAMETERS: Dict[str, Any] = {
    "cell_cycle_models": {
        "Ki67_basic": {
            "code": "1",
            "name": "Ki67 (basic)",
            "time_units": "min",
            "phases": [
                {"index": 0, "code": "3", "name": "Ki67-", "division_at_phase_exit": False},
                {"index": 1, "code": "2", "name": "Ki67+", "division_at_phase_exit": True}
            ],
            "phase_links": [
                {"from": 0, "to": 1, "fixed_duration": False},
                {"from": 1, "to": 0, "fixed_duration": True}
            ],
            "transition_rates": [
                {"from": 0, "to": 1, "rate": 0.003623188},
                {"from": 1, "to": 0, "rate": 0.001075269}
            ]
        },
        "Ki67_advanced": {
            "code": "0", 
            "name": "Ki67 (advanced)",
            "time_units": "min",
            "phases": [
                {"index": 0, "code": "3", "name": "Ki67-", "division_at_phase_exit": False},
                {"index": 1, "code": "0", "name": "Ki67+ (premitotic)", "division_at_phase_exit": True},
                {"index": 2, "code": "1", "name": "Ki67+ (postmitotic)", "division_at_phase_exit": False}
            ],
            "phase_links": [
                {"from": 0, "to": 1, "fixed_duration": False},
                {"from": 1, "to": 2, "fixed_duration": True},
                {"from": 2, "to": 0, "fixed_duration": True}
            ],
            "transition_rates": [
                {"from": 0, "to": 1, "rate": 0.004608295},
                {"from": 1, "to": 2, "rate": 0.001282051},
                {"from": 2, "to": 0, "rate": 0.006666667}
            ]
        },
        "live": {
            "code": "5",
            "name": "live",
            "time_units": "min", 
            "phases": [
                {"index": 0, "code": "14", "name": "live", "division_at_phase_exit": True}
            ],
            "phase_links": [
                {"from": 0, "to": 0, "fixed_duration": False}
            ],
            "transition_rates": [
                {"from": 0, "to": 0, "rate": 0.0}
            ]
        },
        "cycling_quiescent": {
            "code": "7",
            "name": "Cycling-Quiescent model",
            "time_units": "min",
            "phases": [
                {"index": 0, "code": "18", "name": "Quiescent", "division_at_phase_exit": False},
                {"index": 1, "code": "17", "name": "Cycling", "division_at_phase_exit": True}
            ],
            "phase_links": [
                {"from": 0, "to": 1, "fixed_duration": False},
                {"from": 1, "to": 0, "fixed_duration": True}
            ],
            "transition_rates": [
                {"from": 0, "to": 1, "rate": 0.003623188},
                {"from": 1, "to": 0, "rate": 0.001075269}
            ]
        },
        "flow_cytometry": {
            "code": "2",
            "name": "Flow cytometry model (basic)",
            "time_units": "min",
            "phases": [
                {"index": 0, "code": "4", "name": "G0/G1", "division_at_phase_exit": False},
                {"index": 1, "code": "10", "name": "S", "division_at_phase_exit": False},
                {"index": 2, "code": "11", "name": "G2/M", "division_at_phase_exit": True}
            ],
            "phase_links": [
                {"from": 0, "to": 1, "fixed_duration": False},
                {"from": 1, "to": 2, "fixed_duration": False},
                {"from": 2, "to": 0, "fixed_duration": False}
            ],
            "transition_rates": [
                {"from": 0, "to": 1, "rate": 0.00324},
                {"from": 1, "to": 2, "rate": 0.00208},
                {"from": 2, "to": 0, "rate": 0.00333}
            ]
        },
        "flow_cytometry_separated": {
            "code": "6",
            "name": "Flow cytometry model (separated)",
            "time_units": "min",
            "phases": [
                {"index": 0, "code": "4", "name": "G0/G1", "division_at_phase_exit": False},
                {"index": 1, "code": "10", "name": "S", "division_at_phase_exit": False},
                {"index": 2, "code": "12", "name": "G2", "division_at_phase_exit": False},
                {"index": 3, "code": "13", "name": "M", "division_at_phase_exit": True}
            ],
            "phase_links": [
                {"from": 0, "to": 1, "fixed_duration": False},
                {"from": 1, "to": 2, "fixed_duration": True},
                {"from": 2, "to": 3, "fixed_duration": True},
                {"from": 3, "to": 0, "fixed_duration": True}
            ],
            "transition_rates": [
                {"from": 0, "to": 1, "rate": 0.00335},
                {"from": 1, "to": 2, "rate": 0.002083},
                {"from": 2, "to": 3, "rate": 0.004167},
                {"from": 3, "to": 0, "rate": 0.016667}
            ]
        }
    },
    "death_models": {
        "apoptosis": {
            "code": "100",
            "name": "apoptosis",
            "default_rate": 5.31667e-05,
            "phase_durations": [
                {"index": 0, "duration": 516.0, "fixed_duration": True}
            ],
            "parameters": {
                "unlysed_fluid_change_rate": 0.05,
                "lysed_fluid_change_rate": 0.0,
                "cytoplasmic_biomass_change_rate": 1.66667e-02,
                "nuclear_biomass_change_rate": 5.83333e-03,
                "calcification_rate": 0.0,
                "relative_rupture_volume": 2.0
            }
        },
        "necrosis": {
            "code": "101",
            "name": "necrosis",
            "default_rate": 0.0,
            "phase_durations": [
                {"index": 0, "duration": 0.0, "fixed_duration": True},
                {"index": 1, "duration": 86400.0, "fixed_duration": True}
            ],
            "parameters": {
                "unlysed_fluid_change_rate": 1.11667e-2,
                "lysed_fluid_change_rate": 8.33333e-4,
                "cytoplasmic_biomass_change_rate": 5.33333e-5,
                "nuclear_biomass_change_rate": 2.16667e-3,
                "calcification_rate": 0.0,
                "relative_rupture_volume": 2.0
            }
        }
    },
    "volume_defaults": {
        "total": 2494.0,
        "fluid_fraction": 0.75,
        "nuclear": 540.0,
        "fluid_change_rate": 0.05,
        "cytoplasmic_biomass_change_rate": 0.0045,
        "nuclear_biomass_change_rate": 0.0055,
        "calcified_fraction": 0.0,
        "calcification_rate": 0.0,
        "relative_rupture_volume": 2.0
    },
    "mechanics_defaults": {
        "cell_cell_adhesion_strength": 0.4,
        "cell_cell_repulsion_strength": 10.0,
        "relative_maximum_adhesion_distance": 1.25,
        "cell_adhesion_affinities": {
            "default": 1.0
        },
        "attachment_elastic_constant": 0.01,
        "attachment_rate": 0.0,
        "detachment_rate": 0.0,
        "maximum_number_of_attachments": 12,
        "options": {
            "set_relative_equilibrium_distance": {
                "enabled": False,
                "value": 1.8
            },
            "set_absolute_equilibrium_distance": {
                "enabled": False,
                "value": 15.12
            }
        }
    },
    "motility_defaults": {
        "speed": 1.0,
        "persistence_time": 1.0,
        "migration_bias": 0.5,
        "enabled": False,
        "use_2D": True,
        "chemotaxis": {
            "enabled": False,
            "substrate": "substrate",
            "direction": 1
        },
        "advanced_chemotaxis": {
            "enabled": False,
            "normalize_each_gradient": False,
            "chemotactic_sensitivities": {
                "substrate": 0.0
            }
        }
    },
    "secretion_defaults": {
        "substrate": {
            "secretion_rate": 0.0,
            "secretion_target": 1.0,
            "uptake_rate": 0.0,
            "net_export_rate": 0.0
        }
    },
    "cell_interactions_defaults": {
        "apoptotic_phagocytosis_rate": 0.0,
        "necrotic_phagocytosis_rate": 0.0,
        "other_dead_phagocytosis_rate": 0.0,
        "dead_phagocytosis_rate": 0.0,
        "live_phagocytosis_rates": {
            "default": 0.0
        },
        "attack_rates": {
            "default": 0.0
        },
        "attack_damage_rate": 1.0,
        "attack_duration": 0.1,
        "damage_rate": 1.0,
        "fusion_rates": {
            "default": 0.0
        }
    },
    "cell_transformations_defaults": {
        "transformation_rates": {
            "default": 0.0
        }
    },
    "cell_integrity_defaults": {
        "damage_rate": 0.0,
        "damage_repair_rate": 0.0
    },
    "custom_data_defaults": {
        "sample": {
            "value": 1.0,
            "conserved": False,
            "units": "dimensionless",
            "description": ""
        },
        "somedata": {
            "value": 1.0,
            "conserved": False,
            "units": "dimensionless",
            "description": ""
        }
    },
    "initial_parameter_distributions_defaults": {
        "enabled": False,
        "distributions": [
            {
                "enabled": False,
                "type": "Log10Normal",
                "check_base": True,
                "behavior": "Volume",
                "mu": 4,
                "sigma": 2,
                "upper_bound": 100000
            },
            {
                "enabled": False,
                "type": "LogUniform",
                "check_base": True,
                "behavior": "apoptosis",
                "min": 1e-6,
                "max": 1e-2
            }
        ]
    },
    "intracellular_defaults": {
        "maboss": {
            "type": "maboss",
            "bnd_filename": "config/differentiation/boolean_network/tcell_corral.bnd",
            "cfg_filename": "config/differentiation/boolean_network/tcell_corral.cfg",
            "settings": {},
            "mapping": {}
        }
    },
    "cell_type_templates": {
        "default": {
            "cycle": "flow_cytometry_separated",
            "custom_data": {
                "sample": {
                    "value": 1.0,
                    "conserved": False,
                    "units": "dimensionless",
                    "description": ""
                }
            }
        },
        "live_cell": {
            "cycle": "live",
            "custom_data": {
                "somedata": {
                    "value": 1.0,
                    "conserved": False,
                    "units": "dimensionless",
                    "description": ""
                }
            }
        },
        "maboss_cell": {
            "cycle": "live",
            "intracellular": "maboss",
            "custom_data": {
                "somedata": {
                    "value": 1.0,
                    "conserved": False,
                    "units": "dimensionless",
                    "description": ""
                }
            }
        }
    },
    "substrate_defaults": {
        "oxygen": {
            "diffusion_coefficient": 100000.0,
            "decay_rate": 0.1,
            "initial_condition": 38.0,
            "dirichlet_boundary_condition": {
                "enabled": True,
                "value": 38.0
            }
        },
        "substrate": {
            "diffusion_coefficient": 100000.0,
            "decay_rate": 10.0,
            "initial_condition": 0.0,
            "dirichlet_boundary_condition": {
                "enabled": False,
                "value": 0.0
            }
        }
    }
}


def get_default_parameters() -> Dict[str, Any]:
    """
    Get a deep copy of the default parameters.
    
    Returns:
        Dict containing all default PhysiCell parameters
    """
    import copy
    return copy.deepcopy(DEFAULT_PARAMETERS)


def validate_default_parameters() -> bool:
    """
    Validate the integrity of embedded default parameters.
    
    Returns:
        True if all required sections are present and valid
    """
    required_sections = [
        "cell_cycle_models",
        "death_models", 
        "volume_defaults",
        "mechanics_defaults",
        "motility_defaults",
        "secretion_defaults",
        "cell_interactions_defaults",
        "cell_transformations_defaults",
        "cell_integrity_defaults",
        "custom_data_defaults",
        "initial_parameter_distributions_defaults",
        "intracellular_defaults",
        "cell_type_templates",
        "substrate_defaults"
    ]
    
    for section in required_sections:
        if section not in DEFAULT_PARAMETERS:
            return False
            
    return True


# Validate data integrity on import
if not validate_default_parameters():
    raise ValueError("Invalid default parameters data - missing required sections")
