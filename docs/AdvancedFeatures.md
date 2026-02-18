# Advanced Features Guide

This document expands upon `docs/API.md` and describes the advanced capabilities
of the `physicell_config` package. The goal is to provide enough detail for
another agent or service to automate complex PhysiCell configuration tasks,
including building MCP (Model Context Protocol) servers around the API.

## ConfigLoader
`physicell_config/modules/config_loader.py`

`ConfigLoader` is a singleton responsible for loading JSON defaults used by the
modules. It exposes methods such as:

- `get_cycle_model(name)` – retrieve default cell cycle model data
- `get_death_model(name)` – retrieve apoptosis/necrosis defaults
- `get_volume_defaults()` / `get_mechanics_defaults()` / `get_motility_defaults()`
  – volume and mechanics templates used when creating cell types
- `get_cell_type_template(template_name)` – access full cell type presets
- `get_substrate_defaults(name)` – default substrate physical parameters

These defaults are defined in `config/default_parameters.json` and
`config/signals_behaviors.json` and are used whenever a module needs a
predefined structure. Services can load the same JSON if custom defaults are
required.

### JSON Templates
The package ships two main JSON files under `physicell_config/config` that
provide all default settings used by the modules:

- **`default_parameters.json`** – contains reusable snippets for
  `cell_cycle_models`, `death_models`, phenotype defaults (volume, mechanics,
  motility, secretion, interactions, transformations and integrity),
  `intracellular_defaults` and a list of `cell_type_templates`. Each cell type
  template groups these snippets so that calling
  `CellTypeModule.add_cell_type(name, template="live_cell")` will create a new
  cell type pre‑populated with the values stored under the corresponding entry in
  the JSON file.
- The packaged templates are `default`, `live_cell` and `maboss_cell`.

#### Cell Type Template Details

Each entry in `cell_type_templates` bundles default phenotype components,
cycle models and optional intracellular settings that are used by
`CellTypeModule.add_cell_type`.  Below is a summary of the shipped templates:

- **`default`** – uses the `flow_cytometry_separated` cycle model with the
  standard phenotype defaults from this JSON.  Only the custom data field
  `sample` is included, leaving room for additional user variables.  This is the
  most generic starting point for user-defined cell types.
- **`live_cell`** – specifies the minimal `live` cycle model so cells never
  divide by default.  The phenotype defaults are identical to the `default`
  template but the custom data section contains a single `somedata` entry.  It
  is intended for simple simulations focusing on secretion or motility without
  cell proliferation.
- **`maboss_cell`** – extends `live_cell` by also enabling an intracellular
  MaBoSS network (`intracellular` set to `maboss`).  When a cell type is created
  from this template, the Boolean network described under
  `intracellular_defaults.maboss` is attached automatically, ready for further
  mutations or parameter tweaks.
- **`signals_behaviors.json`** – lists all known rule signals and behaviors along
  with IDs and descriptions. `CellRulesCSV` reads this registry so that new
  rules always reference valid names and required context variables.

Inspecting or editing these JSON files allows you to customise defaults or
extend the available rule definitions without modifying the Python code.

## Advanced Cell Type Operations
`physicell_config/modules/cell_types.py`

Beyond the basic `add_cell_type`, this module provides extensive control over
phenotype and intracellular models:

- `set_cycle_model(cell_type, model)` – switch to any of the built in cycle
  models loaded from `ConfigLoader`
- `set_cycle_transition_rate(cell_type, from_phase, to_phase, rate)` – modify
  specific phase transitions
- `set_death_rate(cell_type, death_type, rate)` – adjust apoptosis or necrosis
  rates
- `set_volume_parameters(cell_type, total=None, nuclear=None, fluid_fraction=None)`
  – tweak volume properties
- `set_motility(cell_type, speed=None, persistence_time=None, migration_bias=None,
  enabled=None)`
- `set_chemotaxis(cell_type, substrate, enabled=True, direction=1)` – simple
  chemotaxis toward a substrate
- `set_advanced_chemotaxis(cell_type, substrate_sensitivities, enabled=True,
  normalize_each_gradient=False)` – define multiple substrate sensitivities
- `add_intracellular_model(cell_type, model_type='maboss', bnd_filename='',
  cfg_filename='')` – attach an intracellular network
- `set_intracellular_settings(cell_type, intracellular_dt=None, time_stochasticity=None,
  scaling=None, start_time=None, inheritance_global=None)`
- `add_intracellular_mutation(cell_type, intracellular_name, value)`
- `add_intracellular_initial_value(cell_type, intracellular_name, value)`
- `add_intracellular_input(cell_type, physicell_name, intracellular_name, action='activation',
  threshold=1, smoothing=0)`
- `add_intracellular_output(cell_type, physicell_name, intracellular_name,
  action='activation', value=1000000, base_value=0, smoothing=0)`

These methods allow programmatic construction of complex cell behaviours and
are typically required when assembling model-aware MCP servers.

## Cell Rules and CSV Generation
`physicell_config/modules/cell_rules.py`

- `add_ruleset(name, folder='./config', filename='rules.csv', enabled=True)` –
  register external rule files
- `add_rule(...)` – create rules programmatically
- `load_rules_from_csv(filename)` / `save_rules_to_csv(filename)` – interchange
  rules with CSV
- `clear_rules()` / `clear_rulesets()` – reset configuration

`cell_rules_csv.py` wraps these rules in a CSV oriented helper that is aware of
available signals and behaviors. Key calls include:

- `get_available_signals(filter_by_type=None)`
- `get_available_behaviors(filter_by_type=None)`
- `get_context()` – inspect current cell types, substrates and custom variables
- `add_rule(cell_type, signal, direction, behavior, saturation_value, half_max,
  hill_power, apply_to_dead)`
- `generate_csv(filename)` – produce a CSV ready for PhysiCell

The context awareness ensures that generated rules only reference entities
present in the configuration.

## PhysiBoSS Integration
`physicell_config/modules/physiboss.py`

`PhysiBoSSModule` enables intracellular boolean networks. Typical usage:

```python
config.physiboss.enable_physiboss('model.bnd', initial_values={'p53': True})
config.physiboss.set_time_step(6.0)
config.physiboss.add_mutation('cancer_cell', 'EGFR', False)
```

All settings are exported through `add_to_xml()` if the module is enabled.

## Initial Conditions
`physicell_config/modules/initial_conditions.py`

Methods allow direct placement of cells or reading from CSV:

- `add_cell_cluster(cell_type, x, y, z=0.0, radius=100.0, num_cells=100)`
- `add_single_cell(cell_type, x, y, z=0.0)`
- `add_rectangular_region(cell_type, x_min, x_max, y_min, y_max, z_min=-5.0,
  z_max=5.0, density=0.8)`
- `add_csv_file(filename, folder='./config', enabled=False)`

For MCP automation this module is typically populated from user provided
geometry descriptions.

## Save Options and Runtime Parameters
`physicell_config/modules/save_options.py` and `options.py`

These modules configure output frequency and core simulation options. Examples:

```python
config.save_options.set_svg_plot_substrate(True, substrate='oxygen', colormap='viridis')
config.options.set_parallel_threads(8)
```

## Building MCP Servers
To build an HTTP service that generates simulation XML from client requests you
can wrap `PhysiCellConfig` in a web framework. Below is a minimal `FastAPI`
skeleton illustrating the concept:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from physicell_config import PhysiCellConfig

app = FastAPI()

class SimulationRequest(BaseModel):
    substrates: dict
    cell_types: list

@app.post('/generate')
def generate(req: SimulationRequest):
    config = PhysiCellConfig()
    for name, params in req.substrates.items():
        config.substrates.add_substrate(name, **params)
    for ct in req.cell_types:
        config.cell_types.add_cell_type(ct['name'])
    xml_str = config.generate_xml()
    return {'xml': xml_str}
```


Further wrappers can drive such a server using natural language or structured
commands. Refer to the API reference for building blocks.


