"""Regression tests ensuring generated example configs match curated XML files."""

from __future__ import annotations

import difflib
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_SPECS = [
    (
        "examples/generate_basic.py",
        "create_basic_config",
        "examples/PhysiCell_settings.xml",
    ),
    (
        "examples/generate_rules.py",
        "create_rules_config",
        "examples/PhysiCell_settings_rules.xml",
    ),
    (
        "examples/generate_foxp3.py",
        "create_foxp3_config",
        "examples/PhysiCell_settings_FOXP3_2_mutant.xml",
    ),
]


def _load_factory(script_rel_path: str, factory_name: str):
    """Dynamically load a factory function from an example script."""
    script_path = REPO_ROOT / script_rel_path
    module_name = f"generated_tests_{script_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load spec for {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, factory_name):
        raise AttributeError(f"{script_path} does not define {factory_name}")
    return getattr(module, factory_name)


def _read_expected(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _format_diff(expected: str, actual: str, expected_label: str, actual_label: str) -> str:
    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile=expected_label,
        tofile=actual_label,
        lineterm="",
    )
    return "\n".join(list(diff)[:200])


@pytest.mark.parametrize("script_path,factory_name,expected_xml", EXAMPLE_SPECS)
def test_example_configs_match_curated_files(script_path: str, factory_name: str, expected_xml: str):
    """Ensure each supported example exactly reproduces its curated XML file."""
    factory = _load_factory(script_path, factory_name)
    config = factory()
    generated_xml = config.generate_xml()
    expected_contents = _read_expected(expected_xml)
    if generated_xml != expected_contents:
        diff = _format_diff(expected_contents, generated_xml, expected_xml, f"{script_path}:{factory_name}")
        pytest.fail(
            f"Generated XML from {factory_name} in {script_path} does not match {expected_xml}.\nDiff:\n{diff}"
        )
