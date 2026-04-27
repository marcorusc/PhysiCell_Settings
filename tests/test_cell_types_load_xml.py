"""
Regression tests for CellTypeModule.load_from_xml / _parse_phenotype.

Earlier versions of the loader parsed cycle / death / volume / mechanics /
motility / secretion / intracellular but silently dropped cell_interactions,
cell_transformations, cell_integrity, and initial_parameter_distributions.
A subsequent save_xml would then regenerate those sections from template
defaults, masking any configuration the user had loaded.

These tests exercise a round-trip (populate -> save_xml -> fresh load_xml)
for each of those four sections and assert the reloaded data matches the
pre-export state.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from physicell_config import PhysiCellConfig


def _diff(before, after, path=""):
    """Walk two nested structures; yield string descriptions of any mismatch."""
    issues = []
    if isinstance(before, dict):
        for k, v in before.items():
            if k not in after:
                issues.append(f"{path}.{k} missing after reload")
            else:
                issues.extend(_diff(v, after[k], f"{path}.{k}"))
    elif isinstance(before, list):
        if not isinstance(after, list) or len(after) != len(before):
            issues.append(
                f"{path} length differs: {len(before)} -> "
                f"{len(after) if isinstance(after, list) else type(after).__name__}"
            )
        else:
            for i, (b, a) in enumerate(zip(before, after)):
                issues.extend(_diff(b, a, f"{path}[{i}]"))
    else:
        if before != after:
            issues.append(f"{path}: {before!r} -> {after!r}")
    return issues


@pytest.fixture
def roundtrip_config(tmp_path: Path):
    cfg = PhysiCellConfig()
    cfg.cell_types.add_cell_type("tumor")
    cfg.cell_types.add_cell_type("macrophage")

    # cell_interactions: scalar + dict-valued fields
    cfg.cell_types.set_attack_rate("macrophage", "tumor", 0.05)
    cfg.cell_types.set_phagocytosis_rates(
        "macrophage", apoptotic=0.01, necrotic=0.02, other_dead=0.005
    )
    mac_ci = cfg.cell_types.cell_types["macrophage"]["phenotype"]["cell_interactions"]
    mac_ci["live_phagocytosis_rates"] = {"tumor": 0.03}
    mac_ci["attack_damage_rate"] = 0.08
    mac_ci["attack_duration"] = 15.0
    cfg.cell_types.cell_types["tumor"]["phenotype"]["cell_interactions"][
        "fusion_rates"
    ] = {"tumor": 0.001}

    # cell_transformations
    cfg.cell_types.set_transformation_rate("tumor", "macrophage", 0.002)

    # cell_integrity
    integrity = cfg.cell_types.cell_types["tumor"]["phenotype"]["cell_integrity"]
    integrity["damage_rate"] = 0.1
    integrity["damage_repair_rate"] = 0.05

    # initial_parameter_distributions (cell_def-level, not phenotype-level)
    cfg.cell_types.cell_types["tumor"]["initial_parameter_distributions"] = {
        "enabled": True,
        "distributions": [
            {
                "enabled": True,
                "type": "Log10Normal",
                "check_base": True,
                "behavior": "cycle entry",
                "mu": -1.5,
                "sigma": 0.3,
                "upper_bound": 0.1,
            },
            {
                "enabled": False,
                "type": "LogUniform",
                "check_base": False,
                "behavior": "necrosis rate",
                "min": 0.001,
                "max": 0.01,
            },
        ],
    }

    xml_path = tmp_path / "roundtrip.xml"
    cfg.save_xml(str(xml_path))

    reloaded = PhysiCellConfig()
    reloaded.load_xml(str(xml_path))

    return cfg, reloaded


def test_cell_interactions_roundtrip(roundtrip_config):
    cfg, reloaded = roundtrip_config
    for name in ("tumor", "macrophage"):
        before = copy.deepcopy(
            cfg.cell_types.cell_types[name]["phenotype"]["cell_interactions"]
        )
        after = reloaded.cell_types.cell_types[name]["phenotype"]["cell_interactions"]
        assert not _diff(before, after), _diff(before, after)


def test_cell_transformations_roundtrip(roundtrip_config):
    cfg, reloaded = roundtrip_config
    before = copy.deepcopy(
        cfg.cell_types.cell_types["tumor"]["phenotype"]["cell_transformations"]
    )
    after = reloaded.cell_types.cell_types["tumor"]["phenotype"][
        "cell_transformations"
    ]
    assert not _diff(before, after), _diff(before, after)
    assert after["transformation_rates"]["macrophage"] == pytest.approx(0.002)


def test_cell_integrity_roundtrip(roundtrip_config):
    cfg, reloaded = roundtrip_config
    before = copy.deepcopy(
        cfg.cell_types.cell_types["tumor"]["phenotype"]["cell_integrity"]
    )
    after = reloaded.cell_types.cell_types["tumor"]["phenotype"]["cell_integrity"]
    assert not _diff(before, after), _diff(before, after)


def test_initial_parameter_distributions_roundtrip(roundtrip_config):
    cfg, reloaded = roundtrip_config
    before = copy.deepcopy(
        cfg.cell_types.cell_types["tumor"]["initial_parameter_distributions"]
    )
    after = reloaded.cell_types.cell_types["tumor"]["initial_parameter_distributions"]
    assert not _diff(before, after), _diff(before, after)
    # Both distribution types survive with their type-specific keys intact
    types = [d["type"] for d in after["distributions"]]
    assert "Log10Normal" in types and "LogUniform" in types


def test_missing_sections_leave_defaults_intact(tmp_path: Path):
    """Cell defs without the four sections should not regress defaults."""
    cfg = PhysiCellConfig()
    cfg.cell_types.add_cell_type("plain")

    xml_path = tmp_path / "plain.xml"
    cfg.save_xml(str(xml_path))

    reloaded = PhysiCellConfig()
    reloaded.load_xml(str(xml_path))

    assert "plain" in reloaded.cell_types.cell_types
    phenotype = reloaded.cell_types.cell_types["plain"]["phenotype"]
    # Sections still exist as dicts with defaults (not lost, not corrupted)
    assert isinstance(phenotype["cell_interactions"], dict)
    assert isinstance(phenotype["cell_transformations"], dict)
    assert isinstance(phenotype["cell_integrity"], dict)
    assert isinstance(
        reloaded.cell_types.cell_types["plain"]["initial_parameter_distributions"],
        dict,
    )
