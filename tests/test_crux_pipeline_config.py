"""Tests for crux_pipeline_config.py — pipeline configuration system."""

import json
import os

import pytest

from scripts.lib.crux_pipeline_config import (
    PipelineConfig,
    TddConfig,
    SecurityAuditConfig,
    SecondOpinionConfig,
    HumanApprovalConfig,
    DryRunConfig,
    DesignValidationConfig,
    KnowledgeBaseConfig,
    load_pipeline_config,
    save_pipeline_config,
    default_config,
    gates_for_risk_level,
    gates_for_mode,
    VALID_TDD_LEVELS,
    VALID_RISK_LEVELS,
    VALID_SEVERITY_LEVELS,
    VALID_SANDBOX_TYPES,
    VALID_WCAG_LEVELS,
    VALID_SECURITY_CATEGORIES,
)


# ---------------------------------------------------------------------------
# TddConfig
# ---------------------------------------------------------------------------

class TestTddConfig:
    def test_defaults(self):
        cfg = TddConfig()
        assert cfg.enabled is True
        assert cfg.level == "standard"
        assert cfg.apply_to_modes == ["build-py", "build-ex"]
        assert cfg.coverage_minimum == 80
        assert cfg.coverage_minimum_strict == 95
        assert cfg.max_correction_iterations == 10
        assert cfg.bdd_enabled is True

    def test_to_dict(self):
        cfg = TddConfig()
        d = cfg.to_dict()
        assert d["enabled"] is True
        assert d["level"] == "standard"
        assert d["apply_to_modes"] == ["build-py", "build-ex"]

    def test_from_dict(self):
        d = {"enabled": False, "level": "strict", "coverage_minimum": 95}
        cfg = TddConfig.from_dict(d)
        assert cfg.enabled is False
        assert cfg.level == "strict"
        assert cfg.coverage_minimum == 95
        # defaults for missing keys
        assert cfg.bdd_enabled is True

    def test_from_dict_empty(self):
        cfg = TddConfig.from_dict({})
        assert cfg.enabled is True
        assert cfg.level == "standard"

    def test_valid_levels(self):
        assert set(VALID_TDD_LEVELS) == {"strict", "standard", "relaxed", "off"}

    def test_off_level(self):
        cfg = TddConfig(level="off", enabled=False)
        assert cfg.level == "off"
        assert cfg.enabled is False


# ---------------------------------------------------------------------------
# SecurityAuditConfig
# ---------------------------------------------------------------------------

class TestSecurityAuditConfig:
    def test_defaults(self):
        cfg = SecurityAuditConfig()
        assert cfg.enabled is True
        assert cfg.max_iterations == 3
        assert cfg.stop_on_convergence is True
        assert cfg.fail_on_severity == ["critical", "high"]
        assert cfg.warn_on_severity == ["medium"]
        assert cfg.log_on_severity == ["low", "info"]
        assert len(cfg.categories) == 7

    def test_to_dict_roundtrip(self):
        cfg = SecurityAuditConfig()
        d = cfg.to_dict()
        cfg2 = SecurityAuditConfig.from_dict(d)
        assert cfg2.max_iterations == cfg.max_iterations
        assert cfg2.categories == cfg.categories

    def test_from_dict_partial(self):
        d = {"max_iterations": 5}
        cfg = SecurityAuditConfig.from_dict(d)
        assert cfg.max_iterations == 5
        assert cfg.enabled is True

    def test_all_categories(self):
        assert VALID_SECURITY_CATEGORIES == [
            "input_validation",
            "authentication",
            "data_exposure",
            "cryptography",
            "dependencies",
            "infrastructure",
            "business_logic",
        ]


# ---------------------------------------------------------------------------
# SecondOpinionConfig
# ---------------------------------------------------------------------------

class TestSecondOpinionConfig:
    def test_defaults(self):
        cfg = SecondOpinionConfig()
        assert cfg.enabled is True
        assert cfg.model == "auto"
        assert cfg.check_test_coverage is True
        assert cfg.check_security_findings is True

    def test_to_dict(self):
        cfg = SecondOpinionConfig(model="32b")
        assert cfg.to_dict()["model"] == "32b"

    def test_from_dict(self):
        cfg = SecondOpinionConfig.from_dict({"model": "custom-model"})
        assert cfg.model == "custom-model"


# ---------------------------------------------------------------------------
# HumanApprovalConfig
# ---------------------------------------------------------------------------

class TestHumanApprovalConfig:
    def test_defaults(self):
        cfg = HumanApprovalConfig()
        assert cfg.enabled is True
        assert cfg.required_for_severity == ["critical", "high", "medium"]

    def test_from_dict(self):
        cfg = HumanApprovalConfig.from_dict({"required_for_severity": ["critical"]})
        assert cfg.required_for_severity == ["critical"]


# ---------------------------------------------------------------------------
# DryRunConfig
# ---------------------------------------------------------------------------

class TestDryRunConfig:
    def test_defaults(self):
        cfg = DryRunConfig()
        assert cfg.enabled is True
        assert cfg.sandbox_type == "container"
        assert cfg.timeout_seconds == 300

    def test_from_dict(self):
        cfg = DryRunConfig.from_dict({"sandbox_type": "vm", "timeout_seconds": 600})
        assert cfg.sandbox_type == "vm"
        assert cfg.timeout_seconds == 600

    def test_valid_sandbox_types(self):
        assert set(VALID_SANDBOX_TYPES) == {"isolated", "container", "vm"}


# ---------------------------------------------------------------------------
# DesignValidationConfig
# ---------------------------------------------------------------------------

class TestDesignValidationConfig:
    def test_defaults(self):
        cfg = DesignValidationConfig()
        assert cfg.enabled is True
        assert cfg.wcag_level == "AA"
        assert cfg.check_brand_consistency is True
        assert cfg.check_handoff_completeness is True

    def test_from_dict(self):
        cfg = DesignValidationConfig.from_dict({"wcag_level": "AAA"})
        assert cfg.wcag_level == "AAA"

    def test_valid_wcag_levels(self):
        assert set(VALID_WCAG_LEVELS) == {"A", "AA", "AAA"}


# ---------------------------------------------------------------------------
# KnowledgeBaseConfig
# ---------------------------------------------------------------------------

class TestKnowledgeBaseConfig:
    def test_defaults(self):
        cfg = KnowledgeBaseConfig()
        assert cfg.enabled is True
        assert cfg.auto_promote_patterns is True
        assert cfg.cross_project_learning is True
        assert set(cfg.categories) == {
            "test_patterns", "security_findings",
            "design_patterns", "code_patterns",
        }

    def test_from_dict(self):
        cfg = KnowledgeBaseConfig.from_dict({"cross_project_learning": False})
        assert cfg.cross_project_learning is False
        assert cfg.enabled is True


# ---------------------------------------------------------------------------
# PipelineConfig (top-level)
# ---------------------------------------------------------------------------

class TestPipelineConfig:
    def test_defaults(self):
        cfg = PipelineConfig()
        assert cfg.version == "2.0"
        assert cfg.environment == "production"
        assert isinstance(cfg.tdd, TddConfig)
        assert isinstance(cfg.security_audit, SecurityAuditConfig)
        assert isinstance(cfg.second_opinion, SecondOpinionConfig)
        assert isinstance(cfg.human_approval, HumanApprovalConfig)
        assert isinstance(cfg.dry_run, DryRunConfig)
        assert isinstance(cfg.design_validation, DesignValidationConfig)
        assert isinstance(cfg.knowledge_base, KnowledgeBaseConfig)

    def test_to_dict_has_all_sections(self):
        cfg = PipelineConfig()
        d = cfg.to_dict()
        assert "metadata" in d
        assert "pipeline" in d
        assert "knowledge_base" in d
        assert d["metadata"]["version"] == "2.0"
        pipeline = d["pipeline"]
        assert "tdd_enforcement" in pipeline
        assert "security_audit" in pipeline
        assert "second_opinion" in pipeline
        assert "human_approval" in pipeline
        assert "dry_run" in pipeline
        assert "design_validation" in pipeline

    def test_from_dict_full(self):
        d = {
            "metadata": {"version": "2.0", "environment": "dev"},
            "pipeline": {
                "tdd_enforcement": {"level": "strict"},
                "security_audit": {"max_iterations": 5},
            },
            "knowledge_base": {"cross_project_learning": False},
        }
        cfg = PipelineConfig.from_dict(d)
        assert cfg.environment == "dev"
        assert cfg.tdd.level == "strict"
        assert cfg.security_audit.max_iterations == 5
        assert cfg.knowledge_base.cross_project_learning is False

    def test_from_dict_empty(self):
        cfg = PipelineConfig.from_dict({})
        assert cfg.version == "2.0"
        assert cfg.tdd.enabled is True

    def test_from_dict_missing_pipeline(self):
        cfg = PipelineConfig.from_dict({"metadata": {"version": "3.0"}})
        assert cfg.version == "3.0"
        assert cfg.tdd.enabled is True

    def test_roundtrip(self):
        cfg = PipelineConfig()
        d = cfg.to_dict()
        cfg2 = PipelineConfig.from_dict(d)
        assert cfg2.to_dict() == d


# ---------------------------------------------------------------------------
# default_config
# ---------------------------------------------------------------------------

class TestDefaultConfig:
    def test_returns_pipeline_config(self):
        cfg = default_config()
        assert isinstance(cfg, PipelineConfig)
        assert cfg.tdd.level == "standard"

    def test_is_independent_copy(self):
        cfg1 = default_config()
        cfg2 = default_config()
        cfg1.tdd.level = "strict"
        assert cfg2.tdd.level == "standard"


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

class TestLoadSave:
    def test_save_and_load(self, tmp_path):
        config_file = str(tmp_path / "pipeline.json")
        cfg = PipelineConfig()
        cfg.tdd.level = "strict"
        save_pipeline_config(cfg, config_file)

        loaded = load_pipeline_config(config_file)
        assert loaded.tdd.level == "strict"
        assert loaded.security_audit.max_iterations == 3

    def test_load_missing_file_returns_default(self, tmp_path):
        config_file = str(tmp_path / "nonexistent.json")
        cfg = load_pipeline_config(config_file)
        assert isinstance(cfg, PipelineConfig)
        assert cfg.tdd.level == "standard"

    def test_load_corrupt_file_returns_default(self, tmp_path):
        config_file = str(tmp_path / "bad.json")
        with open(config_file, "w") as f:
            f.write("not json {{{")
        cfg = load_pipeline_config(config_file)
        assert cfg.tdd.level == "standard"

    def test_save_creates_parent_dirs(self, tmp_path):
        config_file = str(tmp_path / "sub" / "dir" / "pipeline.json")
        save_pipeline_config(PipelineConfig(), config_file)
        assert os.path.exists(config_file)

    def test_saved_file_is_valid_json(self, tmp_path):
        config_file = str(tmp_path / "pipeline.json")
        save_pipeline_config(PipelineConfig(), config_file)
        with open(config_file) as f:
            data = json.load(f)
        assert "metadata" in data


# ---------------------------------------------------------------------------
# gates_for_risk_level
# ---------------------------------------------------------------------------

class TestGatesForRiskLevel:
    def test_low_risk(self):
        cfg = default_config()
        gates = gates_for_risk_level("low", cfg)
        assert 1 in gates  # preflight always
        assert 3 not in gates  # no security audit
        assert 5 not in gates  # no human approval

    def test_medium_risk(self):
        cfg = default_config()
        gates = gates_for_risk_level("medium", cfg)
        assert 1 in gates
        assert 3 in gates  # security audit
        assert 5 in gates  # human approval
        assert 4 not in gates  # no second opinion

    def test_high_risk(self):
        cfg = default_config()
        gates = gates_for_risk_level("high", cfg)
        assert 1 in gates
        assert 3 in gates
        assert 4 in gates  # second opinion
        assert 5 in gates
        assert 6 in gates  # dry run

    def test_critical_risk(self):
        cfg = default_config()
        gates = gates_for_risk_level("critical", cfg)
        assert 1 in gates
        assert 3 in gates
        assert 4 in gates
        assert 5 in gates
        assert 6 in gates

    def test_tdd_gate_included_when_enabled(self):
        cfg = default_config()
        gates = gates_for_risk_level("high", cfg)
        assert 2 in gates

    def test_tdd_gate_excluded_when_disabled(self):
        cfg = default_config()
        cfg.tdd.enabled = False
        gates = gates_for_risk_level("high", cfg)
        assert 2 not in gates

    def test_design_gate_included_for_critical(self):
        cfg = default_config()
        gates = gates_for_risk_level("critical", cfg)
        assert 7 in gates

    def test_design_gate_excluded_when_disabled(self):
        cfg = default_config()
        cfg.design_validation.enabled = False
        gates = gates_for_risk_level("critical", cfg)
        assert 7 not in gates

    def test_invalid_risk_level_returns_all(self):
        cfg = default_config()
        gates = gates_for_risk_level("unknown", cfg)
        assert 1 in gates


# ---------------------------------------------------------------------------
# gates_for_mode
# ---------------------------------------------------------------------------

class TestGatesForMode:
    def test_build_mode_includes_tdd(self):
        cfg = default_config()
        gates = gates_for_mode("build-py", "high", cfg)
        assert 2 in gates

    def test_non_build_mode_excludes_tdd(self):
        cfg = default_config()
        gates = gates_for_mode("review", "high", cfg)
        assert 2 not in gates

    def test_design_mode_includes_design_gate(self):
        cfg = default_config()
        gates = gates_for_mode("design-ui", "high", cfg)
        assert 7 in gates

    def test_non_design_mode_excludes_design_gate(self):
        cfg = default_config()
        gates = gates_for_mode("build-py", "high", cfg)
        assert 7 not in gates

    def test_non_design_mode_excludes_design_gate_at_critical(self):
        cfg = default_config()
        gates = gates_for_mode("build-py", "critical", cfg)
        assert 7 not in gates

    def test_design_mode_uses_accessibility_audit(self):
        cfg = default_config()
        gates = gates_for_mode("design-review", "high", cfg)
        # gate 3 still present but context is accessibility not security
        assert 3 in gates

    def test_explain_mode_minimal_gates(self):
        cfg = default_config()
        gates = gates_for_mode("explain", "low", cfg)
        assert 1 in gates
        assert 2 not in gates
        assert 3 not in gates

    def test_custom_apply_to_modes(self):
        cfg = default_config()
        cfg.tdd.apply_to_modes = ["build-py", "build-ex", "test"]
        gates = gates_for_mode("test", "high", cfg)
        assert 2 in gates
