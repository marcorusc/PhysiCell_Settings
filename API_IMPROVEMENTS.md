# PhysiCell Config — API Improvement Plan

## Context

The `physicell_config` package generates PhysiCell and PhysiBoSS XML/CSV settings

files programmatically. After building regression tests against three curated

reference XML files, **all tests pass**, confirming the package works correctly.

However, the generator scripts (`examples/generate_basic.py`,

`examples/generate_rules.py`, `examples/generate_foxp3.py`) were forced to use

**direct internal dictionary manipulation** in many places because the

`CellTypeModule` public API lacks methods for common operations. This makes

generator code fragile and non-self-documenting.

This document describes **6 issues** to address, ordered by priority. Each

section contains:

-**What** is wrong (the problem)

-**Where** the issue lives (exact file, line numbers, method names)

-**Why** it matters (user impact)

-**Current workaround** (exact code from the generators)

-**How to fix** (precise implementation instructions)

-**Validation** (how to verify the fix works)

> **CRITICAL**: After implementing each change, run the full test suite with

> `python3 -m pytest tests/ -v`. All 7 tests must continue to pass. The tests

> use semantic XML comparison so formatting changes are fine, but structural

> or value changes will be caught.

---

## Issue 1: `_add_cycle_xml` fallback prevents using `phase_durations`

### Problem

In `physicell_config/modules/cell_types.py`, line 438:

```python

transition_rates = cycle.get('transition_rates', model_config.get('transition_rates', []))

```

When a user calls `set_cycle_model('flow_cytometry_separated')`, the cycle dict

gets populated with `transition_rates` from the model config. If the user then

wants to use `phase_durations` instead (which is equally valid in PhysiCell),

they must explicitly set `transition_rates = []`. Simply deleting the key with

`del cycle['transition_rates']` does **not** work because the fallback

`model_config.get('transition_rates', [])` re-fetches the rates from the model

defaults.

Additionally, the code comment on line 458 says:

```python

# Legacy support for old phase_durations format (deprecated but kept for compatibility)

```

This is **incorrect** — PhysiCell actively supports both `phase_durations` and

`phase_transition_rates`. The comment is misleading.

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Method**: `_add_cycle_xml()`, lines 420–466

-**Line 438**: The fallback logic

-**Line 458**: The misleading "Legacy/deprecated" comment

### Current workaround (from `examples/generate_basic.py`, lines 52–60)

```python

# Override to use phase_durations to match example

config.cell_types.cell_types['default']['phenotype']['cycle']['phase_durations'] = [

    {'index': 0, 'duration': 300.0, 'fixed_duration': False},

    {'index': 1, 'duration': 480.0, 'fixed_duration': True},

    {'index': 2, 'duration': 240.0, 'fixed_duration': True},

    {'index': 3, 'duration': 60.0, 'fixed_duration': True}

]

# Set transition_rates to empty so phase_durations are used (model_config fallback)

config.cell_types.cell_types['default']['phenotype']['cycle']['transition_rates'] = []

```

The user must (a) directly manipulate the internal dict to set `phase_durations`,

and (b) explicitly set `transition_rates = []` to suppress the fallback — both

are unintuitive.

### How to fix

#### Step 1: Fix the fallback logic in `_add_cycle_xml` (line 438)

Change line 438 from:

```python

transition_rates = cycle.get('transition_rates', model_config.get('transition_rates', []))

```

to:

```python

if'transition_rates'in cycle:

    transition_rates = cycle['transition_rates']

else:

    transition_rates = model_config.get('transition_rates', [])

```

This way, if the user explicitly sets `transition_rates` to an empty list **or**

deletes the key entirely, the behavior is correct:

- Key absent → fall back to model config (existing behavior for unmodified types)
- Key present but empty → no transition rates, proceed to check phase_durations
- Key present with data → use transition rates

#### Step 2: Fix the misleading comment on line 458

Change:

```python

# Legacy support for old phase_durations format (deprecated but kept for compatibility)

```

to:

```python

# Phase durations format (alternative to transition rates, both supported by PhysiCell)

```

#### Step 3: Add a public method `set_cycle_phase_durations`

Add to `CellTypeModule`, after the existing `set_cycle_transition_rate` method

(around line 172):

```python

defset_cycle_phase_durations(self, cell_type: str,

                              durations: list[dict]) -> None:

"""Set cycle phase durations for a cell type.


    This clears any transition rates so the XML output uses

    ``<phase_durations>`` instead of ``<phase_transition_rates>``.

    Both formats are valid in PhysiCell.


    Parameters

    ----------

    cell_type:

        Name of the cell type to modify.

    durations:

        List of dicts, each with keys ``index`` (int),

        ``duration`` (float), and ``fixed_duration`` (bool).


    Example

    -------

>>> config.cell_types.set_cycle_phase_durations('default', [

...     {'index': 0, 'duration': 300.0, 'fixed_duration': False},

...     {'index': 1, 'duration': 480.0, 'fixed_duration': True},

...     {'index': 2, 'duration': 240.0, 'fixed_duration': True},

...     {'index': 3, 'duration': 60.0, 'fixed_duration': True},

... ])

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


for d in durations:

self._validate_non_negative_number(d['duration'], f"phase {d['index']} duration")


    cycle =self.cell_types[cell_type]['phenotype']['cycle']

    cycle['phase_durations'] = durations

# Clear transition_rates so _add_cycle_xml uses phase_durations

    cycle['transition_rates'] = []

```

#### Step 4: Update `examples/generate_basic.py` to use the new method

Replace lines 52–60:

```python

# Override to use phase_durations to match example

config.cell_types.cell_types['default']['phenotype']['cycle']['phase_durations'] = [

    {'index': 0, 'duration': 300.0, 'fixed_duration': False},

    {'index': 1, 'duration': 480.0, 'fixed_duration': True},

    {'index': 2, 'duration': 240.0, 'fixed_duration': True},

    {'index': 3, 'duration': 60.0, 'fixed_duration': True}

]

# Set transition_rates to empty so phase_durations are used (model_config fallback)

config.cell_types.cell_types['default']['phenotype']['cycle']['transition_rates'] = []

```

With:

```python

config.cell_types.set_cycle_phase_durations('default', [

    {'index': 0, 'duration': 300.0, 'fixed_duration': False},

    {'index': 1, 'duration': 480.0, 'fixed_duration': True},

    {'index': 2, 'duration': 240.0, 'fixed_duration': True},

    {'index': 3, 'duration': 60.0, 'fixed_duration': True},

])

```

### Validation

Run `python3 -m pytest tests/ -v`. The basic config test must still pass.

---

## Issue 2: No public API for death model parameters

### Problem

The `CellTypeModule` only has `set_death_rate(cell_type, death_type, rate)` which

sets the overall death rate. There is **no public method** to:

1. Set individual death model parameters (e.g., `unlysed_fluid_change_rate`,

`cytoplasmic_biomass_change_rate`, etc.)

2. Choose between `phase_durations` and `phase_transition_rates` for death models
3. Set the phase duration/rate values themselves

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Method**: `set_death_rate()`, lines 174–187 (only sets the rate, nothing else)

-**Serialization**: `_add_death_xml()`, lines 481–561 (reads from internal dict)

### Current workarounds

**Setting death parameters** (from `examples/generate_foxp3.py`, lines 99–108):

```python

# These are direct dict manipulations — no public API exists

death = ct[name]['phenotype']['death']

death['apoptosis']['default_rate'] =0.0

death['apoptosis']['parameters'] =dict(_APOPTOSIS_PARAMS)

death['necrosis']['default_rate'] =0.0

death['necrosis']['parameters'] =dict(_APOPTOSIS_PARAMS)

```

**Replacing entire death model with transition rates** (from `examples/generate_rules.py`, line 157):

```python

# Must replace the entire death dict to switch from phase_durations to phase_transition_rates

ct[name]['phenotype']['death'] = _live_cell_death_transition_rates()

```

Where `_live_cell_death_transition_rates()` is a helper function (lines 14–50)

that builds the full dict structure manually:

```python

def_live_cell_death_transition_rates():

return {

'apoptosis': {

'code': '100', 'name': 'apoptosis', 'default_rate': 0.0,

'phase_transition_rates': [

                {'start_index': 0, 'end_index': 1, 'rate': 0.001938, 'fixed_duration': False}

            ],

'parameters': { ... },

        },

'necrosis': {

'code': '101', 'name': 'necrosis', 'default_rate': 0.0,

'phase_transition_rates': [

                {'start_index': 0, 'end_index': 1, 'rate': 9000000000.0, 'fixed_duration': False},

                {'start_index': 1, 'end_index': 2, 'rate': 1.15741e-05, 'fixed_duration': True},

            ],

'parameters': { ... },

        },

    }

```

**Setting apoptosis phase duration** (from `examples/generate_foxp3.py`, lines 119–121):

```python

# Treg: apoptosis duration = 0 (not 516)

ct['Treg']['phenotype']['death']['apoptosis']['phase_durations'] = [

    {'index': 0, 'duration': 0.0, 'fixed_duration': True}

]

```

### How to fix

#### Add `set_death_parameters` method

Add to `CellTypeModule`, after `set_death_rate()` (around line 188):

```python

defset_death_parameters(self, cell_type: str, death_type: str, **params) -> None:

"""Set death model sub-parameters for a cell type.


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    death_type:

        ``'apoptosis'`` or ``'necrosis'``.

    **params:

        Keyword arguments corresponding to death model parameter names.

        Valid keys: ``unlysed_fluid_change_rate``,

        ``lysed_fluid_change_rate``, ``cytoplasmic_biomass_change_rate``,

        ``nuclear_biomass_change_rate``, ``calcification_rate``,

        ``relative_rupture_volume``.


    Example

    -------

>>> config.cell_types.set_death_parameters('default', 'necrosis',

...     unlysed_fluid_change_rate=0.05,

...     cytoplasmic_biomass_change_rate=0.0166667,

... )

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

if death_type notin ['apoptosis', 'necrosis']:

raiseValueError(f"Invalid death type '{death_type}'. Use 'apoptosis' or 'necrosis'")


    valid_keys = {

'unlysed_fluid_change_rate', 'lysed_fluid_change_rate',

'cytoplasmic_biomass_change_rate', 'nuclear_biomass_change_rate',

'calcification_rate', 'relative_rupture_volume',

    }

for key in params:

if key notin valid_keys:

raiseValueError(f"Invalid death parameter '{key}'. Valid: {valid_keys}")


    death_data =self.cell_types[cell_type]['phenotype']['death'][death_type]

if'parameters'notin death_data:

        death_data['parameters'] = {}

    death_data['parameters'].update(params)

```

#### Add `set_death_phase_durations` method

```python

defset_death_phase_durations(self, cell_type: str, death_type: str,

                              durations: list[dict]) -> None:

"""Set death model phase durations (removes any phase_transition_rates).


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    death_type:

        ``'apoptosis'`` or ``'necrosis'``.

    durations:

        List of dicts with ``index``, ``duration``, ``fixed_duration``.


    Example

    -------

>>> config.cell_types.set_death_phase_durations('Treg', 'apoptosis', [

...     {'index': 0, 'duration': 0.0, 'fixed_duration': True},

... ])

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

if death_type notin ['apoptosis', 'necrosis']:

raiseValueError(f"Invalid death type '{death_type}'")


    death_data =self.cell_types[cell_type]['phenotype']['death'][death_type]

    death_data['phase_durations'] = durations

# Remove transition rates to ensure durations are used

    death_data.pop('phase_transition_rates', None)

```

#### Add `set_death_phase_transition_rates` method

```python

defset_death_phase_transition_rates(self, cell_type: str, death_type: str,

                                     rates: list[dict]) -> None:

"""Set death model phase transition rates (removes any phase_durations).


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    death_type:

        ``'apoptosis'`` or ``'necrosis'``.

    rates:

        List of dicts with ``start_index``, ``end_index``, ``rate``,

        ``fixed_duration``.


    Example

    -------

>>> config.cell_types.set_death_phase_transition_rates(

...     'M0 macrophage', 'necrosis', [

...         {'start_index': 0, 'end_index': 1, 'rate': 9e9, 'fixed_duration': False},

...         {'start_index': 1, 'end_index': 2, 'rate': 1.15741e-05, 'fixed_duration': True},

...     ])

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

if death_type notin ['apoptosis', 'necrosis']:

raiseValueError(f"Invalid death type '{death_type}'")


    death_data =self.cell_types[cell_type]['phenotype']['death'][death_type]

    death_data['phase_transition_rates'] = rates

# Remove durations to ensure transition rates are used

    death_data.pop('phase_durations', None)

```

#### Update generators to use new methods

In `examples/generate_foxp3.py`, replace direct dict manipulation like:

```python

death['apoptosis']['parameters'] =dict(_APOPTOSIS_PARAMS)

```

with:

```python

config.cell_types.set_death_parameters(name, 'apoptosis',

unlysed_fluid_change_rate=0.05,

lysed_fluid_change_rate=0.0,

cytoplasmic_biomass_change_rate=1.66667e-02,

nuclear_biomass_change_rate=5.83333e-03,

calcification_rate=0.0,

relative_rupture_volume=2.0,

)

```

In `examples/generate_foxp3.py`, replace:

```python

ct['Treg']['phenotype']['death']['apoptosis']['phase_durations'] = [

    {'index': 0, 'duration': 0.0, 'fixed_duration': True}

]

```

with:

```python

config.cell_types.set_death_phase_durations('Treg', 'apoptosis', [

    {'index': 0, 'duration': 0.0, 'fixed_duration': True},

])

```

In `examples/generate_rules.py`, replace the `_live_cell_death_transition_rates()`

helper + direct dict assignment with the new methods:

```python

config.cell_types.set_death_rate(name, 'apoptosis', 0.0)

config.cell_types.set_death_phase_transition_rates(name, 'apoptosis', [

    {'start_index': 0, 'end_index': 1, 'rate': 0.001938, 'fixed_duration': False},

])

config.cell_types.set_death_parameters(name, 'apoptosis', ...)


config.cell_types.set_death_rate(name, 'necrosis', 0.0)

config.cell_types.set_death_phase_transition_rates(name, 'necrosis', [

    {'start_index': 0, 'end_index': 1, 'rate': 9e9, 'fixed_duration': False},

    {'start_index': 1, 'end_index': 2, 'rate': 1.15741e-05, 'fixed_duration': True},

])

config.cell_types.set_death_parameters(name, 'necrosis', ...)

```

The `_live_cell_death_transition_rates()` helper function (lines 14–50 of

`generate_rules.py`) can then be removed.

### Validation

Run `python3 -m pytest tests/ -v`. All 7 tests must still pass.

---

## Issue 3: No public API for cell adhesion affinities

### Problem

There is no public method to set per-cell-type adhesion affinities. Users must

directly manipulate the internal mechanics dict. This was required in both

`generate_rules.py` and `generate_foxp3.py`.

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Serialization**: `_add_mechanics_xml()`, lines 605–610 (reads `cell_adhesion_affinities` from dict)

-**No setter method exists**

### Current workarounds

From `examples/generate_rules.py`, lines 166–171:

```python

all_cell_names =list(ct.keys())

for name in all_cell_names:

    ct[name]['phenotype']['mechanics']['cell_adhesion_affinities'] = {

        n: 1.0for n in all_cell_names

    }

```

From `examples/generate_foxp3.py`, lines (similar pattern):

```python

for name in cell_names:

    ct[name]['phenotype']['mechanics']['cell_adhesion_affinities'] = {

        n: 1.0for n in cell_names

    }

```

### How to fix

Add to `CellTypeModule`, after `set_motility()` (around line 231):

```python

defset_cell_adhesion_affinities(self, cell_type: str,

                                 affinities: dict[str, float]) -> None:

"""Set per-cell-type adhesion affinities.


    Parameters

    ----------

    cell_type:

        Name of the cell type to modify.

    affinities:

        Dictionary mapping target cell type names to affinity values.

        Replaces any existing affinities (including the placeholder

        ``"default"`` key).


    Example

    -------

>>> config.cell_types.set_cell_adhesion_affinities('M0 macrophage', {

...     'malignant epithelial cell': 1.0,

...     'M0 macrophage': 1.0,

...     'effector T cell': 0.5,

... })

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


for target, value in affinities.items():

self._validate_non_negative_number(value, f"adhesion affinity for {target}")


self.cell_types[cell_type]['phenotype']['mechanics']['cell_adhesion_affinities'] = affinities.copy()

```

Also add a convenience method to set all cell types to have affinities for all

other cell types (the common use case):

```python

defupdate_all_cell_types_for_adhesion_affinities(self,

                                                   default_affinity: float=1.0) -> None:

"""Populate adhesion affinities so every cell type has an entry for every other.


    Existing non-default entries are preserved. The placeholder ``"default"``

    key is removed and replaced with explicit per-cell-type entries.


    Parameters

    ----------

    default_affinity:

        Default affinity value for missing entries.

    """

    all_names =list(self.cell_types.keys())

for cell_type_name in all_names:

        existing =self.cell_types[cell_type_name]['phenotype']['mechanics'].get(

'cell_adhesion_affinities', {})

# Remove placeholder

        existing.pop('default', None)

        new_affinities = {}

for name in all_names:

            new_affinities[name] = existing.get(name, default_affinity)

self.cell_types[cell_type_name]['phenotype']['mechanics']['cell_adhesion_affinities'] = new_affinities

```

#### Update generators

In `examples/generate_rules.py`, replace lines 166–172:

```python

all_cell_names =list(ct.keys())

for name in all_cell_names:

    ct[name]['phenotype']['mechanics']['cell_adhesion_affinities'] = {

        n: 1.0for n in all_cell_names

    }

    ct[name]['phenotype']['mechanics']['relative_maximum_adhesion_distance'] =1.5

```

with:

```python

config.cell_types.update_all_cell_types_for_adhesion_affinities(default_affinity=1.0)

```

(Keep the `relative_maximum_adhesion_distance` setting via `set_mechanics_parameters` — see Issue 5.)

### Validation

Run `python3 -m pytest tests/ -v`. All 7 tests must still pass.

---

## Issue 4: No public API for cell interactions and transformations

### Problem

Setting `apoptotic_phagocytosis_rate`, `necrotic_phagocytosis_rate`,

`other_dead_phagocytosis_rate`, specific `attack_rates`, `attack_damage_rate`,

`attack_duration`, and `transformation_rates` all require direct dict

manipulation. The existing `update_all_cell_types_for_interactions()` only

populates zero-valued entries — it cannot set specific non-zero rates.

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Method**: `update_all_cell_types_for_interactions()`, lines 316–365 (only fills zeros)

-**Serialization**: `_add_cell_interactions_xml()`, lines 730–778

-**Serialization**: `_add_cell_transformations_xml()`, lines 780–789

-**No setter methods exist**

### Current workarounds

From `examples/generate_rules.py`, lines 257–279:

```python

# Direct dict manipulation — no public API

for name in ['M0 macrophage', 'M1 macrophage', 'M2 macrophage']:

    ct[name]['phenotype']['cell_interactions'] = {

'apoptotic_phagocytosis_rate': 0.01,

'necrotic_phagocytosis_rate': 0.01,

'other_dead_phagocytosis_rate': 0.01,

'attack_damage_rate': 1.0,

'attack_duration': 0.1,

    }


ct['effector T cell']['phenotype']['cell_interactions'] = {

'apoptotic_phagocytosis_rate': 0,

'necrotic_phagocytosis_rate': 0,

'other_dead_phagocytosis_rate': 0,

'attack_damage_rate': 1.0,

'attack_duration': 0.1,

'attack_rates': {'malignant epithelial cell': 0.01},

}


ct['M1 macrophage']['phenotype']['cell_transformations'] = {

'transformation_rates': {'M2 macrophage': 0.001},

}

```

### How to fix

Add these methods to `CellTypeModule`:

```python

defset_phagocytosis_rates(self, cell_type: str,

                           apoptotic: float=None,

                           necrotic: float=None,

                           other_dead: float=None) -> None:

"""Set dead-cell phagocytosis rates.


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    apoptotic:

        Rate for phagocytosing apoptotic cells.

    necrotic:

        Rate for phagocytosing necrotic cells.

    other_dead:

        Rate for phagocytosing other dead cells.


    Example

    -------

>>> config.cell_types.set_phagocytosis_rates('M0 macrophage',

...     apoptotic=0.01, necrotic=0.01, other_dead=0.01)

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


    interactions =self.cell_types[cell_type]['phenotype']['cell_interactions']

if apoptotic isnotNone:

self._validate_non_negative_number(apoptotic, "apoptotic phagocytosis rate")

        interactions['apoptotic_phagocytosis_rate'] = apoptotic

if necrotic isnotNone:

self._validate_non_negative_number(necrotic, "necrotic phagocytosis rate")

        interactions['necrotic_phagocytosis_rate'] = necrotic

if other_dead isnotNone:

self._validate_non_negative_number(other_dead, "other dead phagocytosis rate")

        interactions['other_dead_phagocytosis_rate'] = other_dead



defset_attack_rate(self, cell_type: str, target_cell_type: str,

                    rate: float) -> None:

"""Set the attack rate for one cell type attacking another.


    Parameters

    ----------

    cell_type:

        The attacking cell type.

    target_cell_type:

        The cell type being attacked.

    rate:

        Attack rate in 1/min.


    Example

    -------

>>> config.cell_types.set_attack_rate('effector T cell',

...     'malignant epithelial cell', 0.01)

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

self._validate_non_negative_number(rate, "attack rate")


    interactions =self.cell_types[cell_type]['phenotype']['cell_interactions']

if'attack_rates'notin interactions:

        interactions['attack_rates'] = {}

    interactions['attack_rates'][target_cell_type] = rate



defset_attack_parameters(self, cell_type: str,

                          damage_rate: float=None,

                          duration: float=None) -> None:

"""Set attack damage rate and duration.


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    damage_rate:

        Attack damage rate in 1/min.

    duration:

        Attack duration in min.


    Example

    -------

>>> config.cell_types.set_attack_parameters('effector T cell',

...     damage_rate=1.0, duration=0.1)

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


    interactions =self.cell_types[cell_type]['phenotype']['cell_interactions']

if damage_rate isnotNone:

self._validate_non_negative_number(damage_rate, "attack damage rate")

        interactions['attack_damage_rate'] = damage_rate

if duration isnotNone:

self._validate_non_negative_number(duration, "attack duration")

        interactions['attack_duration'] = duration



defset_transformation_rate(self, cell_type: str, target_cell_type: str,

                            rate: float) -> None:

"""Set the transformation rate from one cell type to another.


    Parameters

    ----------

    cell_type:

        The cell type that transforms.

    target_cell_type:

        The cell type it transforms into.

    rate:

        Transformation rate in 1/min.


    Example

    -------

>>> config.cell_types.set_transformation_rate('M1 macrophage',

...     'M2 macrophage', 0.001)

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

self._validate_non_negative_number(rate, "transformation rate")


    transformations =self.cell_types[cell_type]['phenotype']['cell_transformations']

if'transformation_rates'notin transformations:

        transformations['transformation_rates'] = {}

    transformations['transformation_rates'][target_cell_type] = rate

```

#### Update generators

In `examples/generate_rules.py`, replace lines 257–279 with:

```python

for name in ['M0 macrophage', 'M1 macrophage', 'M2 macrophage']:

    config.cell_types.set_phagocytosis_rates(name, apoptotic=0.01, necrotic=0.01, other_dead=0.01)


config.cell_types.set_attack_rate('effector T cell', 'malignant epithelial cell', 0.01)


config.cell_types.set_transformation_rate('M1 macrophage', 'M2 macrophage', 0.001)

```

### Validation

Run `python3 -m pytest tests/ -v`. All 7 tests must still pass.

---

## Issue 5: No public API for mechanics parameters beyond adhesion/repulsion

### Problem

While `cell_cell_adhesion_strength` and `cell_cell_repulsion_strength` are set

via direct dict access, there is no public method for setting any mechanics

parameters. Users directly manipulate the dict for:

-`cell_cell_adhesion_strength`

-`relative_maximum_adhesion_distance`

-`attachment_elastic_constant`

-`attachment_rate`

-`detachment_rate`

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Serialization**: `_add_mechanics_xml()`, lines 589–640

-**No setter method exists** (only `set_volume_parameters` exists for volume)

### Current workarounds

From `examples/generate_foxp3.py`:

```python

ct[name]['phenotype']['mechanics'].update({

'cell_cell_adhesion_strength': 0.4,

'cell_cell_repulsion_strength': 10.0,

'relative_maximum_adhesion_distance': 1.25,

'attachment_elastic_constant': 0.0,

'attachment_rate': 0.0,

'detachment_rate': 0.0,

})

```

From `examples/generate_rules.py`:

```python

ct[name]['phenotype']['mechanics']['cell_cell_adhesion_strength'] =0.0

```

### How to fix

Add to `CellTypeModule`:

```python

defset_mechanics_parameters(self, cell_type: str, **params) -> None:

"""Set mechanics parameters for a cell type.


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    **params:

        Keyword arguments. Valid keys:

        ``cell_cell_adhesion_strength``,

        ``cell_cell_repulsion_strength``,

        ``relative_maximum_adhesion_distance``,

        ``attachment_elastic_constant``,

        ``attachment_rate``,

        ``detachment_rate``,

        ``maximum_number_of_attachments``.


    Example

    -------

>>> config.cell_types.set_mechanics_parameters('M0 macrophage',

...     cell_cell_adhesion_strength=0.0,

...     relative_maximum_adhesion_distance=1.5,

... )

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


    valid_keys = {

'cell_cell_adhesion_strength',

'cell_cell_repulsion_strength',

'relative_maximum_adhesion_distance',

'attachment_elastic_constant',

'attachment_rate',

'detachment_rate',

'maximum_number_of_attachments',

    }

for key in params:

if key notin valid_keys:

raiseValueError(f"Invalid mechanics parameter '{key}'. Valid: {valid_keys}")


self.cell_types[cell_type]['phenotype']['mechanics'].update(params)

```

#### Update generators

In `examples/generate_foxp3.py`, replace:

```python

ct[name]['phenotype']['mechanics'].update({

'cell_cell_adhesion_strength': 0.4,

...

})

```

with:

```python

config.cell_types.set_mechanics_parameters(name,

cell_cell_adhesion_strength=0.4,

cell_cell_repulsion_strength=10.0,

relative_maximum_adhesion_distance=1.25,

attachment_elastic_constant=0.0,

attachment_rate=0.0,

detachment_rate=0.0,

)

```

### Validation

Run `python3 -m pytest tests/ -v`. All 7 tests must still pass.

---

## Issue 6: No public API for custom data

### Problem

Custom data for cell types must be set via direct dict manipulation. There is no

public method to add or modify custom data entries.

### Where

-**File**: `physicell_config/modules/cell_types.py`

-**Serialization**: `_add_custom_data_xml()`, lines 833–846

-**No setter method exists**

### Current workarounds

From `examples/generate_rules.py`, lines 158–162:

```python

ct[name]['custom_data'] = {

'sample': {'value': 0.0, 'units': 'dimensionless',

'description': '', 'conserved': False}

}

```

From `examples/generate_foxp3.py`:

```python

ct[name]['custom_data'] = {

'somedata': {'value': 1.0, 'conserved': False,

'units': 'dimensionless', 'description': ''}

}

```

### How to fix

Add to `CellTypeModule`:

```python

defset_custom_data(self, cell_type: str, key: str, value,

                    units: str='dimensionless',

                    description: str='',

                    conserved: bool=False) -> None:

"""Add or update a custom data entry for a cell type.


    Parameters

    ----------

    cell_type:

        Name of the cell type.

    key:

        Name of the custom data variable.

    value:

        Value of the variable (numeric or string).

    units:

        Unit string (default ``'dimensionless'``).

    description:

        Optional description.

    conserved:

        Whether the quantity is conserved.


    Example

    -------

>>> config.cell_types.set_custom_data('M0 macrophage', 'sample',

...     value=0.0, units='dimensionless')

    """

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")


self.cell_types[cell_type]['custom_data'][key] = {

'value': value,

'units': units,

'description': description,

'conserved': conserved,

    }

```

#### Update generators

In `examples/generate_rules.py`, replace:

```python

ct[name]['custom_data'] = {

'sample': {'value': 0.0, 'units': 'dimensionless',

'description': '', 'conserved': False}

}

```

with:

```python

config.cell_types.set_custom_data(name, 'sample', value=0.0)

```

Note: when switching from template `live_cell` (which has default custom data

key `somedata`) to using key `sample`, the old key needs to be removed first.

The `set_custom_data` method only adds/updates — it doesn't remove old keys.

For a complete replacement, the generator should do:

```python

# Clear template default and set the correct key

ct[name]['custom_data'].clear()

config.cell_types.set_custom_data(name, 'sample', value=0.0)

```

Or alternatively, add a `clear_custom_data` convenience:

```python

defclear_custom_data(self, cell_type: str) -> None:

"""Remove all custom data entries for a cell type."""

if cell_type notinself.cell_types:

raiseValueError(f"Cell type '{cell_type}' not found")

self.cell_types[cell_type]['custom_data'].clear()

```

### Validation

Run `python3 -m pytest tests/ -v`. All 7 tests must still pass.

---

## Summary of all new methods to add to `CellTypeModule`

| #  | Method name                                       | Issue | Purpose                                          |

|----|---------------------------------------------------|-------|--------------------------------------------------|

| 1  | `set_cycle_phase_durations()`                     | 1     | Set cycle durations (alternative to rates)        |

| 2  | `set_death_parameters()`                          | 2     | Set death sub-parameters                          |

| 3  | `set_death_phase_durations()`                     | 2     | Set death phase durations                         |

| 4  | `set_death_phase_transition_rates()`              | 2     | Set death phase transition rates                  |

| 5  | `set_cell_adhesion_affinities()`                  | 3     | Set per-cell-type adhesion affinities             |

| 6  | `update_all_cell_types_for_adhesion_affinities()` | 3     | Populate affinities for all cell types            |

| 7  | `set_phagocytosis_rates()`                        | 4     | Set dead-cell phagocytosis rates                  |

| 8  | `set_attack_rate()`                               | 4     | Set attack rate against a target cell type        |

| 9  | `set_attack_parameters()`                         | 4     | Set attack damage rate and duration               |

| 10 | `set_transformation_rate()`                       | 4     | Set transformation rate to a target cell type     |

| 11 | `set_mechanics_parameters()`                      | 5     | Set mechanics params (adhesion, attachment, etc.) |

| 12 | `set_custom_data()`                               | 6     | Add/update custom data entry                      |

| 13 | `clear_custom_data()`                             | 6     | Remove all custom data entries                    |

## Additional changes

| File                                        | Change                                              |

|---------------------------------------------|-----------------------------------------------------|

| `physicell_config/modules/cell_types.py:438`| Fix `_add_cycle_xml` fallback logic                 |

| `physicell_config/modules/cell_types.py:458`| Fix misleading "legacy/deprecated" comment          |

| `examples/generate_basic.py`                | Use new API methods instead of dict manipulation    |

| `examples/generate_rules.py`               | Use new API methods, remove `_live_cell_death_transition_rates()` helper |

| `examples/generate_foxp3.py`               | Use new API methods instead of dict manipulation    |

## Implementation order

1.**Issue 1** first — it fixes a bug and is the simplest change.

2.**Issues 2–6** can be done in any order — they are independent API additions.

3.**Update generators** after all methods are implemented.

4.**Run tests** after each issue to catch regressions early.

## Final validation

After all changes:

```bash

python3-mpytesttests/-v

```

All 7 tests must pass:

-`test_example_configs_match_curated_files[basic]`

-`test_example_configs_match_curated_files[rules]`

-`test_example_configs_match_curated_files[foxp3]`

-`test_cell_rules_csv_matches_expected`

-`test_import_package_root`

-`test_import_modules_and_construct_config`

-`test_direct_submodules_import`
