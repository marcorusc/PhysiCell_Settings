#!/usr/bin/env python3
"""
Basic smoke tests to ensure key modules import and basic objects can be constructed.
These are quick and meant for CI pre-publish validation.
"""

import importlib

def test_import_package_root():
    pkg = importlib.import_module("physicell_config")
    assert hasattr(pkg, "PhysiCellConfig")


def test_import_modules_and_construct_config():
    pkg = importlib.import_module("physicell_config")
    config_cls = pkg.PhysiCellConfig
    config = config_cls()
    # touch main modules
    _ = config.domain
    _ = config.substrates
    _ = config.cell_types
    _ = config.cell_rules
    _ = config.physiboss
    _ = config.options
    _ = config.initial_conditions
    _ = config.save_options


def test_direct_submodules_import():
    # ensure public submodules import
    mods = [
        "physicell_config.modules.domain",
        "physicell_config.modules.substrates",
        "physicell_config.modules.cell_types",
        "physicell_config.modules.cell_rules",
        "physicell_config.modules.cell_rules_csv",
        "physicell_config.modules.physiboss",
        "physicell_config.modules.options",
        "physicell_config.modules.initial_conditions",
        "physicell_config.modules.save_options",
        "physicell_config.xml_loader",
    ]
    for m in mods:
        mod = importlib.import_module(m)
        assert mod is not None
