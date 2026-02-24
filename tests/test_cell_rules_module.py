#!/usr/bin/env python3
"""
Unit tests for the unified CellRulesModule.

Covers: signals/behaviors registry, context awareness, add_rule / remove_rule,
validate_rules, generate_csv, load_rules_from_csv, rulesets, and print helpers.
"""

import pytest
from physicell_config import PhysiCellConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config():
    """Bare config with no cell types or substrates."""
    return PhysiCellConfig()


@pytest.fixture
def config_with_context():
    """Config pre-populated with substrates and cell types."""
    cfg = PhysiCellConfig()
    cfg.substrates.add_substrate("oxygen")
    cfg.substrates.add_substrate("glucose")
    cfg.cell_types.add_cell_type("tumor")
    cfg.cell_types.add_cell_type("immune_cell")
    cfg.cell_rules.update_context_from_config(cfg)
    return cfg


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

class TestRegistryLoading:
    def test_registry_loaded_on_init(self, config):
        assert config.cell_rules._signals_behaviors is not None

    def test_signals_available(self, config):
        assert len(config.cell_rules.get_available_signals()) > 0

    def test_behaviors_available(self, config):
        assert len(config.cell_rules.get_available_behaviors()) > 0


# ---------------------------------------------------------------------------
# get_available_signals / get_available_behaviors
# ---------------------------------------------------------------------------

class TestGetAvailable:
    def test_signals_no_filter_returns_all(self, config):
        signals = config.cell_rules.get_available_signals()
        assert isinstance(signals, dict) and len(signals) > 0

    def test_signals_filter_contact(self, config):
        signals = config.cell_rules.get_available_signals(filter_by_type="contact")
        assert signals and all(v["type"] == "contact" for v in signals.values())

    def test_signals_filter_substrate(self, config):
        signals = config.cell_rules.get_available_signals(filter_by_type="substrate")
        assert all(v["type"] == "substrate" for v in signals.values())

    def test_signals_unknown_filter_empty(self, config):
        assert config.cell_rules.get_available_signals(filter_by_type="__no_such_type__") == {}

    def test_behaviors_no_filter_returns_all(self, config):
        behaviors = config.cell_rules.get_available_behaviors()
        assert isinstance(behaviors, dict) and len(behaviors) > 0

    def test_behaviors_filter_death(self, config):
        behaviors = config.cell_rules.get_available_behaviors(filter_by_type="death")
        assert behaviors and all(v["type"] == "death" for v in behaviors.values())

    def test_behaviors_filter_motility(self, config):
        behaviors = config.cell_rules.get_available_behaviors(filter_by_type="motility")
        assert all(v["type"] == "motility" for v in behaviors.values())

    def test_behaviors_unknown_filter_empty(self, config):
        assert config.cell_rules.get_available_behaviors(filter_by_type="__no_such_type__") == {}


# ---------------------------------------------------------------------------
# get_signal_by_name / get_behavior_by_name
# ---------------------------------------------------------------------------

class TestLookupByName:
    def test_signal_found(self, config):
        result = config.cell_rules.get_signal_by_name("contact with live cell")
        assert result is not None
        assert result["name"] == "contact with live cell"
        assert "id" in result

    def test_signal_not_found(self, config):
        assert config.cell_rules.get_signal_by_name("nonexistent_signal_xyz") is None

    def test_behavior_found(self, config):
        result = config.cell_rules.get_behavior_by_name("apoptosis")
        assert result is not None
        assert result["name"] == "apoptosis"
        assert "id" in result

    def test_behavior_not_found(self, config):
        assert config.cell_rules.get_behavior_by_name("nonexistent_behavior_xyz") is None



# ---------------------------------------------------------------------------
# Context management
# ---------------------------------------------------------------------------

class TestContextManagement:
    def test_context_has_required_keys(self, config):
        ctx = config.cell_rules.get_context()
        assert "cell_types" in ctx
        assert "substrates" in ctx
        assert "custom_variables" in ctx

    def test_context_syncs_cell_types(self, config_with_context):
        ctx = config_with_context.cell_rules.get_context()
        assert "tumor" in ctx["cell_types"]
        assert "immune_cell" in ctx["cell_types"]

    def test_context_syncs_substrates(self, config_with_context):
        ctx = config_with_context.cell_rules.get_context()
        assert "oxygen" in ctx["substrates"]
        assert "glucose" in ctx["substrates"]

    def test_context_update_incremental(self, config):
        config.substrates.add_substrate("oxygen")
        config.cell_rules.update_context_from_config(config)
        assert "oxygen" in config.cell_rules.get_context()["substrates"]
        config.substrates.add_substrate("glucose")
        config.cell_rules.update_context_from_config(config)
        assert "glucose" in config.cell_rules.get_context()["substrates"]


# ---------------------------------------------------------------------------
# add_rule
# ---------------------------------------------------------------------------

class TestAddRule:
    def test_add_valid_rule(self, config_with_context):
        config_with_context.cell_rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        assert len(config_with_context.cell_rules.get_rules()) == 1

    def test_rule_fields_stored_correctly(self, config_with_context):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "increases", "cycle entry", 0.003, 21.5, 4, 0)
        rule = rules.get_rules()[0]
        assert rule["cell_type"] == "tumor"
        assert rule["signal"] == "oxygen"
        assert rule["direction"] == "increases"
        assert rule["behavior"] == "cycle entry"
        assert rule["saturation_value"] == 0.003
        assert rule["half_max"] == 21.5
        assert rule["hill_power"] == 4
        assert rule["apply_to_dead"] == 0

    def test_invalid_direction_raises(self, config):
        with pytest.raises(ValueError, match="direction"):
            config.cell_rules.add_rule("tumor", "oxygen", "sideways", "apoptosis", 0, 1, 4, 0)

    def test_invalid_apply_to_dead_raises(self, config):
        with pytest.raises(ValueError, match="apply_to_dead"):
            config.cell_rules.add_rule("tumor", "oxygen", "increases", "apoptosis", 0, 1, 4, 5)

    def test_multiple_rules_accumulate(self, config_with_context):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        rules.add_rule("tumor", "pressure", "decreases", "cycle entry", 0, 1, 4, 0)
        assert len(rules.get_rules()) == 2


# ---------------------------------------------------------------------------
# remove_rule
# ---------------------------------------------------------------------------

class TestRemoveRule:
    def test_remove_existing_rule(self, config_with_context):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        rules.add_rule("tumor", "pressure", "decreases", "cycle entry", 0, 1, 4, 0)
        rules.remove_rule(0)
        remaining = rules.get_rules()
        assert len(remaining) == 1
        assert remaining[0]["signal"] == "pressure"

    def test_remove_out_of_range_raises(self, config):
        with pytest.raises(IndexError):
            config.cell_rules.remove_rule(99)

    def test_remove_negative_index_raises(self, config):
        with pytest.raises(IndexError):
            config.cell_rules.remove_rule(-1)


# ---------------------------------------------------------------------------
# validate_rules
# ---------------------------------------------------------------------------

class TestValidateRules:
    def test_no_rules_returns_empty(self, config):
        assert config.cell_rules.validate_rules() == []

    def test_valid_rules_return_empty(self, config_with_context):
        config_with_context.cell_rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        assert config_with_context.cell_rules.validate_rules() == []

    def test_invalid_direction_returns_message(self, config):
        # Bypass add_rule to inject a bad rule directly
        config.cell_rules.rules.append({
            "cell_type": "tumor", "signal": "oxygen", "direction": "sideways",
            "behavior": "necrosis", "saturation_value": 0,
            "half_max": 1, "hill_power": 4, "apply_to_dead": 0,
        })
        messages = config.cell_rules.validate_rules()
        assert len(messages) == 1
        assert "Rule 0" in messages[0]



# ---------------------------------------------------------------------------
# clear_rules
# ---------------------------------------------------------------------------

class TestClearRules:
    def test_clear_rules_empties_list(self, config_with_context):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        rules.add_rule("tumor", "pressure", "decreases", "cycle entry", 0, 1, 4, 0)
        assert len(rules.get_rules()) == 2
        rules.clear_rules()
        assert rules.get_rules() == []

    def test_clear_rules_on_empty_is_safe(self, config):
        config.cell_rules.clear_rules()
        assert config.cell_rules.get_rules() == []


# ---------------------------------------------------------------------------
# Ruleset management
# ---------------------------------------------------------------------------

class TestRulesetManagement:
    def test_add_ruleset_default_args(self, config):
        config.cell_rules.add_ruleset("main")
        rulesets = config.cell_rules.get_rulesets()
        assert "main" in rulesets
        assert rulesets["main"]["folder"] == "./config"
        assert rulesets["main"]["filename"] == "rules.csv"
        assert rulesets["main"]["enabled"] is True

    def test_add_ruleset_custom_args(self, config):
        config.cell_rules.add_ruleset(
            "immune", folder="./output", filename="immune_rules.csv", enabled=False
        )
        ruleset = config.cell_rules.get_rulesets()["immune"]
        assert ruleset["folder"] == "./output"
        assert ruleset["filename"] == "immune_rules.csv"
        assert ruleset["enabled"] is False

    def test_add_ruleset_sets_protocol_version(self, config):
        config.cell_rules.add_ruleset("main")
        rs = config.cell_rules.get_rulesets()["main"]
        assert rs["protocol"] == "CBHG"
        assert rs["version"] == "3.0"
        assert rs["format"] == "csv"

    def test_multiple_rulesets(self, config):
        config.cell_rules.add_ruleset("tumor_rules")
        config.cell_rules.add_ruleset("immune_rules", filename="immune.csv")
        assert len(config.cell_rules.get_rulesets()) == 2

    def test_clear_rulesets(self, config):
        config.cell_rules.add_ruleset("main")
        config.cell_rules.clear_rulesets()
        assert config.cell_rules.get_rulesets() == {}

    def test_get_rulesets_returns_copy(self, config):
        config.cell_rules.add_ruleset("main")
        rs = config.cell_rules.get_rulesets()
        rs["should_not_appear"] = {}
        assert "should_not_appear" not in config.cell_rules.get_rulesets()


# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------

class TestCsvIO:
    def test_save_rules_to_csv_creates_file(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        outfile = str(tmp_path / "rules.csv")
        rules.save_rules_to_csv(outfile)
        assert (tmp_path / "rules.csv").exists()

    def test_save_rules_to_csv_content(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0.0, 3.75, 8, 0)
        outfile = str(tmp_path / "rules.csv")
        rules.save_rules_to_csv(outfile)
        content = (tmp_path / "rules.csv").read_text()
        assert "tumor" in content
        assert "oxygen" in content
        assert "decreases" in content
        assert "necrosis" in content

    def test_save_rules_empty_raises(self, config):
        with pytest.raises(ValueError, match="No rules"):
            config.cell_rules.save_rules_to_csv("/tmp/empty_rules.csv")

    def test_generate_csv_returns_filename(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        outfile = str(tmp_path / "gen_rules.csv")
        result = rules.generate_csv(outfile)
        assert result == outfile

    def test_generate_csv_creates_file(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0)
        outfile = str(tmp_path / "gen_rules.csv")
        rules.generate_csv(outfile)
        assert (tmp_path / "gen_rules.csv").exists()

    def test_load_rules_from_csv(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0.0, 3.75, 8, 0)
        outfile = str(tmp_path / "rules.csv")
        rules.save_rules_to_csv(outfile)
        rules.clear_rules()
        assert rules.get_rules() == []
        rules.load_rules_from_csv(outfile)
        loaded = rules.get_rules()
        assert len(loaded) == 1
        assert loaded[0]["cell_type"] == "tumor"
        assert loaded[0]["signal"] == "oxygen"
        assert loaded[0]["direction"] == "decreases"
        assert loaded[0]["behavior"] == "necrosis"

    def test_load_rules_missing_file_raises(self, config):
        with pytest.raises(FileNotFoundError):
            config.cell_rules.load_rules_from_csv("/nonexistent/path/rules.csv")

    def test_roundtrip_multiple_rules(self, config_with_context, tmp_path):
        rules = config_with_context.cell_rules
        rules.add_rule("tumor", "oxygen", "decreases", "necrosis", 0.0, 3.75, 8, 0)
        rules.add_rule("tumor", "pressure", "decreases", "cycle entry", 0.0, 1.0, 4, 0)
        outfile = str(tmp_path / "rules.csv")
        rules.save_rules_to_csv(outfile)
        rules.clear_rules()
        rules.load_rules_from_csv(outfile)
        assert len(rules.get_rules()) == 2


# ---------------------------------------------------------------------------
# Print helpers (smoke tests — just verify they don't raise)
# ---------------------------------------------------------------------------

class TestPrintHelpers:
    def test_print_available_signals_no_crash(self, config, capsys):
        config.cell_rules.print_available_signals()
        captured = capsys.readouterr()
        assert "Available Signals" in captured.out

    def test_print_available_signals_with_filter(self, config, capsys):
        config.cell_rules.print_available_signals(filter_by_type="contact")
        captured = capsys.readouterr()
        assert "contact" in captured.out.lower()

    def test_print_available_behaviors_no_crash(self, config, capsys):
        config.cell_rules.print_available_behaviors()
        captured = capsys.readouterr()
        assert "Available Behaviors" in captured.out

    def test_print_context_no_crash(self, config_with_context, capsys):
        config_with_context.cell_rules.print_context()
        captured = capsys.readouterr()
        assert "Context" in captured.out
        assert "tumor" in captured.out

    def test_print_rules_empty(self, config, capsys):
        config.cell_rules.print_rules()
        captured = capsys.readouterr()
        assert "No rules" in captured.out

    def test_print_rules_with_data(self, config_with_context, capsys):
        config_with_context.cell_rules.add_rule(
            "tumor", "oxygen", "decreases", "necrosis", 0, 3.75, 8, 0
        )
        config_with_context.cell_rules.print_rules()
        captured = capsys.readouterr()
        assert "tumor" in captured.out
        assert "oxygen" in captured.out


# ---------------------------------------------------------------------------
# XML serialization
# ---------------------------------------------------------------------------

import xml.etree.ElementTree as ET


class TestXmlSerialization:
    def test_add_to_xml_creates_cell_rules_element(self, config):
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        assert root.find("cell_rules") is not None

    def test_add_to_xml_creates_rulesets_element(self, config):
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        assert root.find("cell_rules/rulesets") is not None

    def test_add_to_xml_default_disabled_ruleset(self, config):
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        ruleset = root.find("cell_rules/rulesets/ruleset")
        assert ruleset is not None
        assert ruleset.get("enabled") == "false"

    def test_add_to_xml_with_ruleset(self, config):
        config.cell_rules.add_ruleset("main", folder="./config", filename="rules.csv", enabled=True)
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        ruleset = root.find("cell_rules/rulesets/ruleset")
        assert ruleset is not None
        assert ruleset.get("enabled") == "true"
        assert ruleset.find("folder").text == "./config"
        assert ruleset.find("filename").text == "rules.csv"

    def test_add_to_xml_includes_settings(self, config):
        config.cell_rules.include_settings = True
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        assert root.find("cell_rules/settings") is not None

    def test_load_from_xml_restores_ruleset(self, config):
        # Build XML with a ruleset, serialize, then reload
        config.cell_rules.add_ruleset("main", folder="./data", filename="my_rules.csv", enabled=True)
        root = ET.Element("root")
        config.cell_rules.add_to_xml(root)
        cell_rules_elem = root.find("cell_rules")

        # Load into a fresh module
        fresh = PhysiCellConfig()
        fresh.cell_rules.load_from_xml(cell_rules_elem)
        rulesets = fresh.cell_rules.get_rulesets()
        assert len(rulesets) == 1
        rs = next(iter(rulesets.values()))
        assert rs["folder"] == "./data"
        assert rs["filename"] == "my_rules.csv"
        assert rs["enabled"] is True

    def test_load_from_xml_none_is_safe(self, config):
        config.cell_rules.load_from_xml(None)   # must not raise
        assert config.cell_rules.get_rulesets() == {}
