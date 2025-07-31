# --- Automatic Context Extraction from Config ---
def update_signals_behaviors_context_from_config(config):
    """
    Automatically update SIGNALS_BEHAVIORS context from a PhysiCellConfig object.
    Extracts cell types, substrates, and cell-type-bounded custom variables.
    """
    # Extract cell types
    cell_types = []
    custom_variables = {}
    
    # Try to get cell types from config.cell_types
    if hasattr(config, 'cell_types'):
        if hasattr(config.cell_types, 'cell_types'):
            # Access config.cell_types.cell_types (the actual dict)
            ct_obj = config.cell_types.cell_types
            if isinstance(ct_obj, dict):
                cell_types = list(ct_obj.keys())
                for ct, ct_data in ct_obj.items():
                    custom_variables[ct] = []
        elif isinstance(config.cell_types, dict):
            cell_types = list(config.cell_types.keys())
            for ct, ct_obj in config.cell_types.items():
                # Try to get custom variables for each cell type
                vars_list = []
                if hasattr(ct_obj, 'custom_data') and isinstance(ct_obj.custom_data, dict):
                    vars_list = list(ct_obj.custom_data.keys())
                custom_variables[ct] = vars_list
        elif isinstance(config.cell_types, list):
            cell_types = config.cell_types
            for ct in cell_types:
                custom_variables[ct] = []
    
    # Extract substrates
    substrates = []
    if hasattr(config, 'substrates'):
        if hasattr(config.substrates, 'substrates'):
            # Access config.substrates.substrates (the actual dict)
            subs_obj = config.substrates.substrates
            if isinstance(subs_obj, dict):
                substrates = list(subs_obj.keys())
        elif isinstance(config.substrates, dict):
            substrates = list(config.substrates.keys())
        elif isinstance(config.substrates, list):
            substrates = config.substrates
    
    # Update context
    SIGNALS_BEHAVIORS["context"]["cell_types"] = cell_types
    SIGNALS_BEHAVIORS["context"]["substrates"] = substrates
    SIGNALS_BEHAVIORS["context"]["custom_variables"] = custom_variables
# --- Context Management and Expansion Utilities ---
def update_signals_behaviors_context(cell_types=None, substrates=None, custom_variables=None):
    """
    Update the context in SIGNALS_BEHAVIORS with current cell types, substrates, and custom variables.
    """
    if cell_types is not None:
        SIGNALS_BEHAVIORS["context"]["cell_types"] = cell_types
    if substrates is not None:
        SIGNALS_BEHAVIORS["context"]["substrates"] = substrates
    if custom_variables is not None:
        SIGNALS_BEHAVIORS["context"]["custom_variables"] = custom_variables

def get_expanded_signals():
    """
    Return a list of all signals, expanded using the current context (cell types, substrates, custom variables).
    """
    context = SIGNALS_BEHAVIORS["context"]
    expanded = []
    for signal in SIGNALS_BEHAVIORS["signals"].values():
        # Substrate expansion
        if "substrate_name" in signal["requires"]:
            for substrate in context["substrates"]:
                s = signal.copy()
                # For 'substrate', use substrate name directly
                if signal["name"] == "substrate":
                    s["name"] = substrate
                elif signal["name"] == "intracellular substrate":
                    s["name"] = f"intracellular {substrate}"
                elif signal["name"] == "substrate gradient":
                    s["name"] = f"{substrate} gradient"
                else:
                    s["name"] = signal["name"].replace("substrate", substrate)
                expanded.append(s)
        # Cell type expansion
        elif "cell_type" in signal["requires"]:
            for cell_type in context["cell_types"]:
                s = signal.copy()
                # Replace 'cell type' with actual cell type
                s["name"] = signal["name"].replace("cell type", cell_type)
                expanded.append(s)
        # Custom variable expansion
        elif "custom_variable" in signal["requires"]:
            for ct, var_list in context["custom_variables"].items():
                for custom_var in var_list:
                    s = signal.copy()
                    s["name"] = f"custom:{custom_var}"
                    expanded.append(s)
        else:
            expanded.append(signal)
    # Ensure all context-driven signals are present, even if not in templates
    # Add 'contact with {ct}' for each cell type if not already present
    contact_template = "contact with {ct}"
    for ct in context["cell_types"]:
        expected_name = f"contact with {ct}"
        if not any(s["name"] == expected_name for s in expanded):
            s = {
                "name": expected_name,
                "type": "contact",
                "requires": ["cell_type"],
                "description": f"Contact with {ct}"
            }
            expanded.append(s)
    # Add 'transform to {ct}' for each cell type if not already present
    for ct in context["cell_types"]:
        expected_name = f"transform to {ct}"
        if not any(s["name"] == expected_name for s in expanded):
            s = {
                "name": expected_name,
                "type": "transformation",
                "requires": ["cell_type"],
                "description": f"Transform to {ct}"
            }
            expanded.append(s)
    return expanded

def get_expanded_behaviors():
    """
    Return a list of all behaviors, expanded using the current context (cell types, substrates, custom variables).
    """
    context = SIGNALS_BEHAVIORS["context"]
    expanded = []
    for behavior in SIGNALS_BEHAVIORS["behaviors"].values():
        if "substrate_name" in behavior["requires"]:
            for substrate in context["substrates"]:
                b = behavior.copy()
                # For behaviors, use substrate name directly for 'substrate secretion', and replace in other templates
                if behavior["name"] == "substrate secretion":
                    b["name"] = f"{substrate} secretion"
                else:
                    b["name"] = behavior["name"].replace("substrate", substrate)
                expanded.append(b)
        elif "cell_type" in behavior["requires"]:
            for cell_type in context["cell_types"]:
                b = behavior.copy()
                b["name"] = behavior["name"].replace("cell type", cell_type)
                expanded.append(b)
        elif "custom_variable" in behavior["requires"]:
            for ct, var_list in context["custom_variables"].items():
                for custom_var in var_list:
                    b = behavior.copy()
                    b["name"] = f"custom:{custom_var}"
                    expanded.append(b)
        else:
            expanded.append(behavior)
    return expanded
"""
Embedded signals and behaviors definitions for PhysiCell rules generation.

This module contains all signal and behavior definitions previously stored in 
signals_behaviors.json, now embedded directly in Python code to avoid file system
dependencies in containerized environments like MCP agents.

Generated from signals_behaviors.json on 2025-07-20
"""

from typing import Dict, Any, List

SIGNALS_BEHAVIORS: Dict[str, Any] = {
    "signals": {
        "0": {
            "name": "substrate",
            "type": "substrate",
            "requires": ["substrate_name"],
            "description": "Level of a specific substrate"
        },
        "1": {
            "name": "intracellular substrate",
            "type": "intracellular",
            "requires": ["substrate_name"],
            "description": "Intracellular level of a specific substrate"
        },
        "2": {
            "name": "substrate gradient",
            "type": "gradient",
            "requires": ["substrate_name"],
            "description": "Gradient of a specific substrate"
        },
        "3": {
            "name": "pressure",
            "type": "physical",
            "requires": [],
            "description": "Local pressure experienced by the cell"
        },
        "4": {
            "name": "volume",
            "type": "physical",
            "requires": [],
            "description": "Cell volume"
        },
        "5": {
            "name": "contact with cell type",
            "type": "contact",
            "requires": ["cell_type"],
            "description": "Contact with a specific cell type"
        },
        "21": {
            "name": "transform to cell type",
            "type": "transformation",
            "requires": ["cell_type"],
            "description": "Transform to a specific cell type"
        },
        "6": {
            "name": "contact with live cell",
            "type": "contact",
            "requires": [],
            "description": "Contact with any live cell"
        },
        "7": {
            "name": "contact with dead cell",
            "type": "contact",
            "requires": [],
            "description": "Contact with any dead cell"
        },
        "8": {
            "name": "contact with apoptotic cell",
            "type": "contact",
            "requires": [],
            "description": "Contact with apoptotic cell"
        },
        "9": {
            "name": "contact with necrotic cell",
            "type": "contact",
            "requires": [],
            "description": "Contact with necrotic cell"
        },
        "10": {
            "name": "contact with other dead cell",
            "type": "contact",
            "requires": [],
            "description": "Contact with other dead cell types"
        },
        "11": {
            "name": "contact with basement membrane",
            "type": "contact",
            "requires": [],
            "description": "Contact with basement membrane"
        },
        "12": {
            "name": "damage",
            "type": "physical",
            "requires": [],
            "description": "Damage level accumulated by the cell"
        },
        "13": {
            "name": "damage delivered",
            "type": "physical",
            "requires": [],
            "description": "Damage delivered by the cell to others"
        },
        "14": {
            "name": "attacking",
            "type": "behavioral",
            "requires": [],
            "description": "Whether the cell is currently attacking"
        },
        "15": {
            "name": "dead",
            "type": "state",
            "requires": [],
            "description": "Whether the cell is dead"
        },
        "16": {
            "name": "total attack time",
            "type": "temporal",
            "requires": [],
            "description": "Total time spent attacking"
        },
        "17": {
            "name": "time",
            "type": "temporal",
            "requires": [],
            "description": "Simulation time"
        },
        "18": {
            "name": "custom:sample",
            "type": "custom",
            "requires": ["custom_variable"],
            "description": "Custom variable (replace 'sample' with actual variable name)"
        },
        "19": {
            "name": "apoptotic",
            "type": "state",
            "requires": [],
            "description": "Whether the cell is apoptotic"
        },
        "20": {
            "name": "necrotic",
            "type": "state",
            "requires": [],
            "description": "Whether the cell is necrotic"
        }
    },
    "behaviors": {
        "0": {
            "name": "substrate secretion",
            "type": "secretion",
            "requires": ["substrate_name"],
            "description": "Secretion rate of a specific substrate"
        },
        "1": {
            "name": "substrate secretion target",
            "type": "secretion",
            "requires": ["substrate_name"],
            "description": "Target secretion level of a specific substrate"
        },
        "2": {
            "name": "substrate uptake",
            "type": "secretion",
            "requires": ["substrate_name"],
            "description": "Uptake rate of a specific substrate"
        },
        "3": {
            "name": "substrate export",
            "type": "secretion",
            "requires": ["substrate_name"],
            "description": "Export rate of a specific substrate"
        },
        "4": {
            "name": "cycle entry",
            "type": "cycle",
            "requires": [],
            "description": "Entry into cell cycle"
        },
        "5": {
            "name": "exit from cycle phase 1",
            "type": "cycle",
            "requires": [],
            "description": "Exit from cell cycle phase 1"
        },
        "6": {
            "name": "exit from cycle phase 2",
            "type": "cycle",
            "requires": [],
            "description": "Exit from cell cycle phase 2"
        },
        "7": {
            "name": "exit from cycle phase 3",
            "type": "cycle",
            "requires": [],
            "description": "Exit from cell cycle phase 3"
        },
        "8": {
            "name": "exit from cycle phase 4",
            "type": "cycle",
            "requires": [],
            "description": "Exit from cell cycle phase 4"
        },
        "9": {
            "name": "exit from cycle phase 5",
            "type": "cycle",
            "requires": [],
            "description": "Exit from cell cycle phase 5"
        },
        "10": {
            "name": "apoptosis",
            "type": "death",
            "requires": [],
            "description": "Trigger apoptotic cell death"
        },
        "11": {
            "name": "necrosis",
            "type": "death",
            "requires": [],
            "description": "Trigger necrotic cell death"
        },
        "12": {
            "name": "migration speed",
            "type": "motility",
            "requires": [],
            "description": "Cell migration speed"
        },
        "13": {
            "name": "migration bias",
            "type": "motility",
            "requires": [],
            "description": "Directional bias in migration"
        },
        "14": {
            "name": "migration persistence time",
            "type": "motility",
            "requires": [],
            "description": "Persistence time for migration direction"
        },
        "15": {
            "name": "chemotactic response to substrate",
            "type": "motility",
            "requires": ["substrate_name"],
            "description": "Chemotactic response to a specific substrate"
        },
        "16": {
            "name": "cell-cell adhesion",
            "type": "mechanics",
            "requires": [],
            "description": "Cell-cell adhesion strength"
        },
        "17": {
            "name": "cell-cell adhesion elastic constant",
            "type": "mechanics",
            "requires": [],
            "description": "Elastic constant for cell-cell adhesion"
        },
        "18": {
            "name": "adhesive affinity to cell type",
            "type": "mechanics",
            "requires": ["cell_type"],
            "description": "Adhesive affinity to a specific cell type"
        },
        "19": {
            "name": "relative maximum adhesion distance",
            "type": "mechanics",
            "requires": [],
            "description": "Maximum distance for cell adhesion"
        },
        "20": {
            "name": "cell-cell repulsion",
            "type": "mechanics",
            "requires": [],
            "description": "Cell-cell repulsion strength"
        },
        "21": {
            "name": "cell-BM adhesion",
            "type": "mechanics",
            "requires": [],
            "description": "Cell-basement membrane adhesion"
        },
        "22": {
            "name": "cell-BM repulsion",
            "type": "mechanics",
            "requires": [],
            "description": "Cell-basement membrane repulsion"
        },
        "23": {
            "name": "phagocytose apoptotic cell",
            "type": "interaction",
            "requires": [],
            "description": "Phagocytosis of apoptotic cells"
        },
        "24": {
            "name": "phagocytose necrotic cell",
            "type": "interaction",
            "requires": [],
            "description": "Phagocytosis of necrotic cells"
        },
        "25": {
            "name": "phagocytose other dead cell",
            "type": "interaction",
            "requires": [],
            "description": "Phagocytosis of other dead cells"
        },
        "26": {
            "name": "phagocytose cell type",
            "type": "interaction",
            "requires": ["cell_type"],
            "description": "Phagocytosis of a specific cell type"
        },
        "27": {
            "name": "attack cell type",
            "type": "interaction",
            "requires": ["cell_type"],
            "description": "Attack a specific cell type"
        },
        "28": {
            "name": "fuse to cell type",
            "type": "interaction",
            "requires": ["cell_type"],
            "description": "Fuse with a specific cell type"
        },
        "29": {
            "name": "transition to cell type",
            "type": "transformation",
            "requires": ["cell_type"],
            "description": "Transform to a specific cell type"
        },
        "30": {
            "name": "asymmetric division to cell type",
            "type": "transformation",
            "requires": ["cell_type"],
            "description": "Asymmetric division producing a specific cell type"
        },
        "31": {
            "name": "custom:sample",
            "type": "custom",
            "requires": ["custom_variable"],
            "description": "Custom behavior (replace 'sample' with actual variable name)"
        },
        "32": {
            "name": "is_movable",
            "type": "physical",
            "requires": [],
            "description": "Whether the cell can move"
        },
        "33": {
            "name": "immunogenicity to cell type",
            "type": "interaction",
            "requires": ["cell_type"],
            "description": "Immunogenicity towards a specific cell type"
        },
        "34": {
            "name": "cell attachment rate",
            "type": "mechanics",
            "requires": [],
            "description": "Rate of cell attachment"
        },
        "35": {
            "name": "cell detachment rate",
            "type": "mechanics",
            "requires": [],
            "description": "Rate of cell detachment"
        },
        "36": {
            "name": "maximum number of cell attachments",
            "type": "mechanics",
            "requires": [],
            "description": "Maximum number of cell attachments"
        },
        "37": {
            "name": "attack damage rate",
            "type": "interaction",
            "requires": [],
            "description": "Rate of damage during attack"
        },
        "38": {
            "name": "attack duration",
            "type": "interaction",
            "requires": [],
            "description": "Duration of attack"
        },
        "39": {
            "name": "damage rate",
            "type": "physical",
            "requires": [],
            "description": "Rate of damage accumulation"
        },
        "40": {
            "name": "damage repair rate",
            "type": "physical",
            "requires": [],
            "description": "Rate of damage repair"
        }
    },
    "directions": ["increases", "decreases"],
    "context": {
        "cell_types": [],
        "substrates": [],
        "custom_variables": []
    }
}


def get_signals_behaviors() -> Dict[str, Any]:
    """
    Get a deep copy of the signals and behaviors definitions.
    
    Returns:
        Dict containing all signals, behaviors, directions, and context
    """
    import copy
    return copy.deepcopy(SIGNALS_BEHAVIORS)


def validate_signals_behaviors() -> bool:
    """
    Validate the integrity of embedded signals and behaviors data.
    
    Returns:
        True if all required sections are present and valid
    """
    required_sections = ["signals", "behaviors", "directions", "context"]
    
    for section in required_sections:
        if section not in SIGNALS_BEHAVIORS:
            return False
    
    # Validate that all signals have required fields
    for signal_id, signal_data in SIGNALS_BEHAVIORS["signals"].items():
        required_fields = ["name", "type", "requires", "description"]
        for field in required_fields:
            if field not in signal_data:
                return False
    
    # Validate that all behaviors have required fields
    for behavior_id, behavior_data in SIGNALS_BEHAVIORS["behaviors"].items():
        required_fields = ["name", "type", "requires", "description"]
        for field in required_fields:
            if field not in behavior_data:
                return False
    
    return True


def get_signal_by_name(signal_name: str) -> Dict[str, Any]:
    """
    Get signal definition by name.
    
    Args:
        signal_name: Name of the signal to find
        
    Returns:
        Signal definition dict or None if not found
    """
    for signal_data in SIGNALS_BEHAVIORS["signals"].values():
        if signal_data["name"] == signal_name:
            return signal_data.copy()
    return None


def get_behavior_by_name(behavior_name: str) -> Dict[str, Any]:
    """
    Get behavior definition by name.
    
    Args:
        behavior_name: Name of the behavior to find
        
    Returns:
        Behavior definition dict or None if not found
    """
    for behavior_data in SIGNALS_BEHAVIORS["behaviors"].values():
        if behavior_data["name"] == behavior_name:
            return behavior_data.copy()
    return None


def get_signals_by_type(signal_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all signals of a specific type.
    
    Args:
        signal_type: Type of signals to filter (e.g., 'substrate', 'contact', 'physical')
        
    Returns:
        Dict of signal IDs to signal definitions
    """
    return {
        signal_id: signal_data.copy()
        for signal_id, signal_data in SIGNALS_BEHAVIORS["signals"].items()
        if signal_data["type"] == signal_type
    }


def get_behaviors_by_type(behavior_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all behaviors of a specific type.
    
    Args:
        behavior_type: Type of behaviors to filter (e.g., 'secretion', 'motility', 'cycle')
        
    Returns:
        Dict of behavior IDs to behavior definitions
    """
    return {
        behavior_id: behavior_data.copy()
        for behavior_id, behavior_data in SIGNALS_BEHAVIORS["behaviors"].items()
        if behavior_data["type"] == behavior_type
    }


# Validate data integrity on import
if not validate_signals_behaviors():
    raise ValueError("Invalid signals and behaviors data - missing required sections or fields")