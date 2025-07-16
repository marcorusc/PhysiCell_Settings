"""Collection of configuration modules used by :class:`PhysiCellConfig`.

Each submodule handles a single aspect of the configuration such as domain
geometry, substrates or cell rules.  They are imported lazily to avoid circular
dependencies when constructing the main configuration object.
"""

# Import modules only when needed to avoid circular imports
__all__ = [
    'DomainModule',
    'SubstrateModule', 
    'CellTypeModule',
    'CellRulesModule',
    'PhysiBoSSModule',
    'OptionsModule',
    'InitialConditionsModule',
    'SaveOptionsModule'
]
