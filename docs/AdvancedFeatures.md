# Advanced Features Guide

This document expands upon `docs/API.md` and describes the advanced capabilities
of the `physicell_config` package.

## ConfigLoader

`physicell_config/modules/config_loader.py`

`ConfigLoader` is a singleton responsible for supplying default parameters used
by all modules. It exposes methods such as:

- `get_cycle_model(name)` – retrieve default cell cycle model data
- `get_death_model(name)` – retrieve apoptosis/necrosis defaults
- `get_volume_defaults()` / `get_mechanics_defaults()` / `get_motility_defaults()`
  – volume and mechanics templates used when creating cell types
- `get_cell_type_template(template_name)` – access full cell type presets
- `get_substrate_defaults(name)` – default substrate physical parameters

These defaults are defined in the embedded Python modules
`physicell_config/config/embedded_defaults.py` and
`physicell_config/config/embedded_signals_behaviors.py` and are used whenever a
module needs a predefined structure.

### Embedded Default Templates

All default settings are stored as Python data structures in
`physicell_config/config/embedded_defaults.py`:

- Contains reusable snippets for `cell_cycle_models`, `death_models`, phenotype
  defaults (volume, mechanics, motility, secretion, interactions,
  transformations and integrity), `intracellular_defaults` and a list of
  `cell_type_templates`. Each cell type template groups these snippets so that
  calling `CellTypeModule.add_cell_type(name, template="live_cell")` will create
  a new cell type pre‑populated with the corresponding default values.
- The available templates are `default`, `live_cell` and `maboss_cell`.

`physicell_config/config/embedded_signals_behaviors.py` lists all known rule
signals and behaviors with IDs and descriptions. `CellRulesCSV` reads this
registry so that new rules always reference valid names.

## Advanced Cell Type Operations

`physicell_config/modules/cell_types.py`

Beyond the basic `add_cell_type`, this module provides extensive control over
phenotype and intracellular models:

- `set_cycle_model(cell_type, model)` – switch to any of the built-in cycle models.
- `set_cycle_transition_rate(cell_type, from_phase, to_phase, rate)` – override a specific phase transition rate.
- `set_cycle_phase_durations(cell_type, durations)` – set cycle phase durations (list of `{index, duration, fixed_duration}`); clears transition rates so `<phase_durations>` is used.
- `set_death_rate(cell_type, death_type, rate)` – adjust the base apoptosis or necrosis rate.
- `set_death_parameters(cell_type, death_type, **params)` – set death sub-parameters without direct dict access.
- `set_death_phase_durations(cell_type, death_type, durations)` – set death phase durations; removes any `phase_transition_rates`.
- `set_death_phase_transition_rates(cell_type, death_type, rates)` – set death phase transition rates; removes any `phase_durations`.
- `set_volume_parameters(cell_type, total=None, nuclear=None, fluid_fraction=None)` – tweak volume properties.
- `set_mechanics_parameters(cell_type, **params)` – set mechanics parameters (`cell_cell_adhesion_strength`, `relative_maximum_adhesion_distance`, `attachment_elastic_constant`, etc.).
- `set_cell_adhesion_affinities(cell_type, affinities)` – set per-cell-type adhesion affinities from a dict.
- `update_all_cell_types_for_adhesion_affinities(default_affinity=1.0)` – populate affinities for every cell type pair.
- `set_phagocytosis_rates(cell_type, apoptotic, necrotic, other_dead)` – set dead-cell phagocytosis rates.
- `set_attack_rate(cell_type, target_cell_type, rate)` – set an attack rate against a target.
- `set_attack_parameters(cell_type, damage_rate, duration)` – set attack damage rate and duration.
- `set_transformation_rate(cell_type, target_cell_type, rate)` – set a cell type transformation rate.
- `set_custom_data(cell_type, key, value, units, description, conserved)` – add or update a custom data entry.
- `clear_custom_data(cell_type)` – remove all custom data entries.

For the full method reference see [`docs/API.md`](API.md).

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
- `add_rule(cell_type, signal, direction, behavior, saturation_value, half_max, hill_power, apply_to_dead)`
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
- `add_rectangular_region(cell_type, x_min, x_max, y_min, y_max, z_min=-5.0, z_max=5.0, density=0.8)`
- `add_csv_file(filename, folder='./config', enabled=False)`

## Save Options and Runtime Parameters

`physicell_config/modules/save_options.py` and `options.py`

These modules configure output frequency and core simulation options. Examples:

```python
config.save_options.set_svg_plot_substrate(True, substrate='oxygen', colormap='viridis')
config.options.set_parallel_threads(8)
```
