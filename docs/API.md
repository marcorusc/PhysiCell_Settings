# PhysiCell Settings API Reference

This page summarizes the public API provided by the `physicell_config` package.
Each section lists the available classes and methods along with a short
explanation of their purpose and parameters.

## PhysiCellConfig
Located in `physicell_config/config_builder_modular.py`.
This class orchestrates all configuration modules and provides convenience
helpers to generate and save complete PhysiCell XML files.

### Methods
- `__init__()` – instantiate the builder and all modules.
- `cell_rules_csv` – property returning a `CellRulesCSV` helper with updated context.
- `add_user_parameter(name, value, units='dimensionless', description='', parameter_type='double')` – register a custom user parameter.
- `set_number_of_cells(count)` – convenience setter for the standard `number_of_cells` parameter.
- `setup_basic_simulation(x_range=(-500,500), y_range=(-500,500), mesh_spacing=20.0, max_time=8640.0)` – configure domain, options and output for a common simulation.
- `add_simple_substrate(name, diffusion_coeff=1000.0, decay_rate=0.1, initial_value=0.0)` – quick helper to create a substrate with basic parameters.
- `add_simple_cell_type(name, secretion_substrate=None, secretion_rate=0.0, motile=False)` – add a cell type with optional secretion and motility settings.
- `generate_xml()` – assemble the XML tree for the current configuration and return it as a string.
- `save_xml(filename)` – generate and write the XML to disk.
- `get_summary()` – return a dictionary summarizing domain, substrates, cell types and options.
- `validate()` – basic sanity checks returning a list of issues found.
- legacy helpers `set_domain`, `add_substrate`, `add_cell_type` mirror module methods.
- `set_parallel_settings(omp_num_threads=4)` – set OpenMP thread count.

## Modules
The builder is composed of several modules located under `physicell_config/modules`.
Each module exposes a small API focused on a single aspect of the configuration.

### DomainModule
- `set_bounds(x_min, x_max, y_min, y_max, z_min=-10.0, z_max=10.0)` – set the simulation domain limits.
- `set_mesh(dx, dy, dz=20.0)` – mesh spacing in each dimension.
- `set_2D(use_2D=True)` – toggle 2‑D mode.
- `add_to_xml(parent)` – append domain settings to an XML element.
- `get_info()` – return the currently stored domain values.

### SubstrateModule
- `set_track_internalized_substrates(enabled)` – include internalized substrate tracking flag.
- `add_substrate(name, diffusion_coefficient=1000.0, decay_rate=0.1, initial_condition=0.0, dirichlet_enabled=False, dirichlet_value=0.0, units='dimensionless', initial_units='mmHg')` – register a new substrate and its physical parameters.
- `set_dirichlet_boundary(substrate_name, boundary, enabled, value=0.0)` – configure boundary conditions per face.
- `remove_substrate(name)` – delete a substrate definition.
- `add_to_xml(parent)` – write microenvironment data to XML.
- `get_substrates()` – return the internal dictionary of substrates.

### CellTypeModule
Handles phenotype and behavioral properties for all cell types.
- `add_cell_type(name, parent_type='default', template='default')` – create a cell type using a predefined template.
- Numerous setter helpers exist for cycle model, death rates, volume, motility, secretion and intracellular models (see source for full list).
- `update_all_cell_types_for_substrates()` – ensure secretion parameters exist for all substrates.
- `add_to_xml(parent)` – serialize all cell type definitions to XML.
- `get_cell_types()` – return the stored cell type definitions.

### CellRulesModule
- `add_ruleset(name, folder='./config', filename='rules.csv', enabled=True)` – declare a CSV ruleset to load during simulation.
- `add_rule(signal, behavior, cell_type, min_signal=0.0, max_signal=1.0, min_behavior=0.0, max_behavior=1.0, hill_power=1.0, half_max=0.5, applies_to_dead=False)` – add an individual rule description.
- `load_rules_from_csv(filename)` / `save_rules_to_csv(filename)` – import or export rules in CSV format.
- `add_to_xml(parent)` – write the cell rules structure to XML.
- `get_rules()` / `get_rulesets()` – return defined rules and rulesets.

### CellRulesCSV
Utility class for creating valid `cell_rules.csv` files.
- Methods to list available signals/behaviors (`get_available_signals`, `get_available_behaviors`).
- Context helpers (`update_context_from_config`, `get_context`).
- `add_rule(cell_type, signal, direction, behavior, base_value, half_max, hill_power, apply_to_dead)` – add a rule in CSV layout and `generate_csv(filename)` to export.
- Includes convenience `print_*` methods to display registry information.

### OptionsModule
- `set_max_time(max_time, units='min')` – total simulation time.
- `set_time_steps(dt_diffusion=None, dt_mechanics=None, dt_phenotype=None)` – adjust internal time steps.
- `set_virtual_wall(enabled)` and other toggles like `set_automated_spring_adhesions`, `set_random_seed`, `set_parallel_threads`.
- `add_to_xml(parent)` – append options to XML.
- `get_options()` – return the stored options dictionary.

### InitialConditionsModule
- `add_cell_cluster(cell_type, x, y, z=0.0, radius=100.0, num_cells=100)` – place a sphere of cells.
- `add_single_cell(cell_type, x, y, z=0.0)` – place a single cell.
- `add_rectangular_region(cell_type, x_min, x_max, y_min, y_max, z_min=-5.0, z_max=5.0, density=0.8)` – fill a region with random cells.
- `add_csv_file(filename, folder='./config', enabled=False)` – use an external CSV for initial positions.
- `add_to_xml(parent)` – write initial conditions to XML.
- `get_conditions()` – return the defined conditions.

### SaveOptionsModule
- `set_output_folder(folder)` – output path for simulation results.
- `set_full_data_options(interval=None, enable=None, settings_interval=None)` – configure full data output.
- `set_svg_options(interval=None, enable=None)` and `set_svg_plot_substrate(enabled=False, limits=False, substrate='substrate', colormap='YlOrRd', min_conc=0, max_conc=1)` for visualisation.
- `set_svg_legend(enabled=False, cell_phase=False, cell_type=True)` – legend options.
- `set_legacy_data(enable)` – toggle legacy format output.
- `add_to_xml(parent)` – append save configuration.
- `get_save_options()` – return internal save options.

### PhysiBoSSModule
- `enable_physiboss(model_file='boolean_model.bnd', initial_values=None, mutations=None, parameters=None)` – activate PhysiBoSS integration with initial settings.
- `set_time_step(value)` and `set_scaling(value)` – adjust simulation step and scaling.
- `add_initial_value(node, value)` / `add_mutation(cell_line, node, value)` / `add_parameter(name, value)` – modify network settings.
- `add_to_xml(parent)` – serialize PhysiBoSS configuration when enabled.
- `is_enabled()` – check status.
- `get_settings()` – retrieve current options.

### ConfigLoader
Utility singleton in `physicell_config/modules/config_loader.py` used by all
modules to pull default parameters from JSON files.

- `get_cycle_model(name)` – return cycle model templates
- `get_death_model(name)` – apoptosis or necrosis defaults
- `get_volume_defaults()` / `get_mechanics_defaults()` / `get_motility_defaults()`
  – phenotype defaults
- `get_cell_type_template(template_name)` – load cell type presets
- Built-in cell type templates: `default`, `live_cell`, `maboss_cell`
- `get_substrate_defaults(name)` – standard substrate parameters

See `docs/AdvancedFeatures.md` for more details on advanced usage.

## Detailed Module Functions
Below is a complete list of public helpers available in each module.

### DomainModule
- `set_bounds(x_min, x_max, y_min, y_max, z_min=-10.0, z_max=10.0)` – define the spatial extents of the domain.
- `set_mesh(dx, dy, dz=20.0)` – specify grid spacing in microns.
- `set_2D(use_2D=True)` – enable 2‑D simulations.
- `add_to_xml(parent)` – append domain settings to an XML element.
- `get_info()` – return current configuration as a dictionary.

### SubstrateModule
- `set_track_internalized_substrates(enabled)` – toggle tracking of internalised substrates.
- `add_substrate(name, diffusion_coefficient=1000.0, decay_rate=0.1, initial_condition=0.0, dirichlet_enabled=False, dirichlet_value=0.0, units='dimensionless', initial_units='mmHg')` – create a substrate definition.
- `set_dirichlet_boundary(substrate_name, boundary, enabled, value=0.0)` – set per‑face Dirichlet conditions.
- `remove_substrate(name)` – delete an existing substrate.
- `add_to_xml(parent)` – write microenvironment data to XML.
- `get_substrates()` – return all defined substrates.

### CellTypeModule
- `add_cell_type(name, parent_type='default', template='default')` – create a new cell type from a template.
- `set_cycle_model(cell_type, model)` – assign a cycle model.
- `set_cycle_transition_rate(cell_type, from_phase, to_phase, rate)` – override specific cycle transitions.
- `set_death_rate(cell_type, death_type, rate)` – change apoptosis or necrosis rates.
- `set_volume_parameters(cell_type, total=None, nuclear=None, fluid_fraction=None)` – adjust volume attributes.
- `set_motility(cell_type, speed=None, persistence_time=None, migration_bias=None, enabled=None)` – configure motility.
- `set_chemotaxis(cell_type, substrate, enabled=True, direction=1)` – simple chemotaxis towards a substrate.
- `set_advanced_chemotaxis(cell_type, substrate_sensitivities, enabled=True, normalize_each_gradient=False)` – multi‑substrate chemotaxis.
- `add_secretion(cell_type, substrate, secretion_rate, secretion_target=1.0, uptake_rate=0.0, net_export_rate=0.0)` – add secretion parameters.
- `update_all_cell_types_for_substrates()` – ensure secretion parameters exist for all substrates.
- `add_intracellular_model(cell_type, model_type='maboss', bnd_filename='', cfg_filename='')` – attach an intracellular model.
- `set_intracellular_settings(cell_type, intracellular_dt=None, time_stochasticity=None, scaling=None, start_time=None, inheritance_global=None)` – tweak intracellular options.
- `add_intracellular_mutation(cell_type, intracellular_name, value)` – force a node value.
- `add_intracellular_initial_value(cell_type, intracellular_name, value)` – set initial node value.
- `add_intracellular_input(cell_type, physicell_name, intracellular_name, action='activation', threshold=1, smoothing=0)` – map a substrate or variable to a node.
- `add_intracellular_output(cell_type, physicell_name, intracellular_name, action='activation', value=1000000, base_value=0, smoothing=0)` – map a node to a behavior.
- `add_to_xml(parent)` – serialize cell definitions to XML.
- `get_cell_types()` – return all stored cell type data.

### CellRulesModule
- `add_ruleset(name, folder='./config', filename='rules.csv', enabled=True)` – register a CSV ruleset file.
- `add_rule(signal, behavior, cell_type, min_signal=0.0, max_signal=1.0, min_behavior=0.0, max_behavior=1.0, hill_power=1.0, half_max=0.5, applies_to_dead=False)` – store a rule description.
- `load_rules_from_csv(filename)` – import rules from CSV.
- `save_rules_to_csv(filename)` – export current rules to CSV.
- `add_to_xml(parent)` – write the cell rules section.
- `get_rules()` – list rule dictionaries.
- `get_rulesets()` – list registered rulesets.
- `clear_rules()` – remove all rules.
- `clear_rulesets()` – remove all rulesets.

### CellRulesCSV
- `update_context_from_config(config)` – refresh cell types and substrates from a config instance.
- `get_available_signals(filter_by_type=None)` – list known signals.
- `get_available_behaviors(filter_by_type=None)` – list known behaviors.
- `get_context()` – inspect current context.
- `get_signal_by_name(signal_name)` – look up a signal by name.
- `get_behavior_by_name(behavior_name)` – look up a behavior by name.
- `add_rule(cell_type, signal, direction, behavior, base_value, half_max, hill_power, apply_to_dead)` – append a CSV rule.
- `remove_rule(index)` – delete a rule by index.
- `get_rules()` – list stored rules.
- `clear_rules()` – remove all rules.
- `generate_csv(filename)` – export a PhysiCell compatible CSV.
- `validate_rules()` – return warnings or errors for the current rule set.
- `print_available_signals(filter_by_type=None)` – print signals table.
- `print_available_behaviors(filter_by_type=None)` – print behaviors table.
- `print_context()` – display current context.
- `print_rules()` – display the rule list.
- `add_to_xml(parent)` – no-op placeholder for compatibility.

### OptionsModule
- `set_max_time(max_time, units='min')` – simulation duration.
- `set_time_steps(dt_diffusion=None, dt_mechanics=None, dt_phenotype=None)` – override solver time steps.
- `set_virtual_wall(enabled)` – toggle boundary walls.
- `set_automated_spring_adhesions(disabled)` – disable automated adhesions.
- `set_random_seed(seed)` – RNG seed.
- `set_legacy_random_points(enabled)` – use legacy division points.
- `set_parallel_threads(num_threads)` – OpenMP thread count.
- `add_to_xml(parent)` – append options to XML.
- `get_options()` – retrieve the options dictionary.

### InitialConditionsModule
- `add_cell_cluster(cell_type, x, y, z=0.0, radius=100.0, num_cells=100)` – place a spherical cluster.
- `add_single_cell(cell_type, x, y, z=0.0)` – place one cell.
- `add_rectangular_region(cell_type, x_min, x_max, y_min, y_max, z_min=-5.0, z_max=5.0, density=0.8)` – populate a region.
- `add_csv_file(filename, folder='./config', enabled=False)` – import positions from CSV.
- `add_to_xml(parent)` – write initial conditions to XML.
- `get_conditions()` – return configured conditions.
- `clear_conditions()` – remove all conditions.

### SaveOptionsModule
- `set_output_folder(folder)` – output directory.
- `set_full_data_options(interval=None, enable=None, settings_interval=None)` – full data dump settings.
- `set_svg_options(interval=None, enable=None)` – global SVG settings.
- `set_svg_plot_substrate(enabled=False, limits=False, substrate='substrate', colormap='YlOrRd', min_conc=0, max_conc=1)` – substrate plot control.
- `set_svg_legend(enabled=False, cell_phase=False, cell_type=True)` – legend visibility.
- `set_legacy_data(enable)` – legacy output files.
- `add_to_xml(parent)` – append save configuration.
- `get_save_options()` – return save options.

### PhysiBoSSModule
- `enable_physiboss(model_file='boolean_model.bnd', initial_values=None, mutations=None, parameters=None)` – activate the Boolean network.
- `set_time_step(value)` – network step size in minutes.
- `set_scaling(value)` – scale network speed.
- `add_initial_value(node, value)` – set a node's initial state.
- `add_mutation(cell_line, node, value)` – force a mutation for a cell line.
- `add_parameter(name, value)` – additional simulator parameter.
- `add_to_xml(parent)` – export settings if enabled.
- `is_enabled()` – check whether PhysiBoSS is active.
- `get_settings()` – retrieve current PhysiBoSS options.

### ConfigLoader
- `get_cycle_model(name)`
- `get_death_model(name)`
- `get_volume_defaults()`
- `get_mechanics_defaults()`
- `get_motility_defaults()`
- `get_secretion_defaults()`
- `get_cell_interactions_defaults()`
- `get_cell_transformations_defaults()`
- `get_cell_integrity_defaults()`
- `get_custom_data_defaults(data_type='sample')`
- `get_initial_parameter_distributions_defaults()`
- `get_intracellular_defaults(intracellular_type='maboss')`
- `get_cell_type_template(template_name)`
- `get_substrate_defaults(name='substrate')`
- `get_default_phenotype(template='default')`
## Package Weaknesses and Possible Improvements
While the package offers a comprehensive API, several aspects could be enhanced:

1. **Limited automated testing** – `test_modular.py` acts mostly as a demo.
   Adding unit tests for each module and integrating continuous integration would
   improve reliability.
2. **Sparse documentation for advanced features** – some complex methods
   lack detailed examples. Extended tutorials and docstrings would ease adoption.
3. **Validation gaps** – configuration validation currently checks only a few
   conditions. More thorough checks (e.g. verifying cross‑module consistency) can
   prevent runtime errors.
4. **No explicit versioned schema** – the XML generation assumes a single
   schema. Providing version compatibility layers or schema definitions would help
   long‑term maintenance.
5. **Dependency on large JSON defaults** – modifying default parameters requires
   editing JSON files manually. A helper API for managing these defaults could
   simplify customization.

Addressing these items would make the project more robust and easier to extend.
