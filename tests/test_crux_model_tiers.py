"""Tests for model tier system."""

import os
from unittest.mock import patch

import pytest

from scripts.lib.crux_model_tiers import (
    MODE_TIERS,
    TASK_ROUTING,
    TIER_ORDER,
    TIERS,
    get_available_tiers,
    get_mode_model,
    get_task_model,
    get_tier_for_model,
    resolve_tier,
    tier_down,
    tier_up,
)


# --- Tier definitions ---


def test_all_tiers_exist():
    assert set(TIERS.keys()) == {"frontier", "standard", "fast", "local", "micro"}


def test_tier_order():
    assert TIER_ORDER == ["micro", "fast", "local", "standard", "frontier"]


def test_all_tiers_have_models():
    for tier, models in TIERS.items():
        assert len(models) > 0, f"Tier {tier} has no models"


# --- Tier resolution ---


def test_resolve_tier_with_ollama():
    model = resolve_tier("micro", ["ollama"])
    assert model is not None
    assert "ollama" in model


def test_resolve_tier_with_anthropic():
    model = resolve_tier("frontier", ["anthropic"])
    assert model is not None
    assert "anthropic" in model


def test_resolve_tier_no_providers():
    model = resolve_tier("frontier", [])
    assert model is None


def test_resolve_tier_unknown_tier():
    assert resolve_tier("nonexistent", ["ollama"]) is None


def test_resolve_tier_auto_detect():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=True):
        model = resolve_tier("frontier")
        assert model is not None


def test_resolve_tier_auto_detect_no_keys():
    with patch.dict(os.environ, {}, clear=True):
        # Only ollama available (assumed always available)
        model = resolve_tier("micro")
        assert model is not None
        assert "ollama" in model


def test_resolve_tier_prefers_first_model():
    model = resolve_tier("fast", ["anthropic", "ollama"])
    # First model in fast tier with anthropic available should be anthropic
    assert "anthropic" in model


def test_resolve_tier_openai():
    model = resolve_tier("frontier", ["openai"])
    assert model is not None
    assert "openai" in model


# --- Task routing ---


def test_all_task_types_have_tiers():
    expected_tasks = [
        "plan_audit", "code_audit", "security_audit", "doc_audit",
        "fix_generation", "independence", "title", "compaction",
        "write", "e2e_test",
    ]
    for task in expected_tasks:
        assert task in TASK_ROUTING, f"Task {task} not in TASK_ROUTING"


def test_get_task_model_plan_audit():
    model = get_task_model("plan_audit", ["ollama"])
    assert model is not None


def test_get_task_model_security_audit():
    model = get_task_model("security_audit", ["anthropic"])
    assert model is not None
    assert "anthropic" in model


def test_get_task_model_title():
    model = get_task_model("title", ["ollama"])
    assert model is not None
    assert "8b" in model or "4b" in model  # Micro tier


def test_get_task_model_unknown():
    assert get_task_model("nonexistent", ["ollama"]) is None


def test_get_task_model_no_provider():
    model = get_task_model("security_audit", [])
    assert model is None


# --- Mode→model mapping ---


def test_mode_tiers_all_modes():
    from scripts.lib.crux_sync import OPENCODE_AGENT_META
    for mode in OPENCODE_AGENT_META:
        assert mode in MODE_TIERS, f"Mode {mode} not in MODE_TIERS"


def test_get_mode_model_build_py():
    model = get_mode_model("build-py", "primary", ["ollama"])
    assert model is not None
    assert "ollama" in model


def test_get_mode_model_plan_audit():
    model = get_mode_model("plan", "audit", ["anthropic"])
    assert model is not None


def test_get_mode_model_unknown_mode():
    assert get_mode_model("nonexistent", "primary", ["ollama"]) is None


def test_get_mode_model_unknown_role():
    # writer has no "audit" role
    assert get_mode_model("writer", "audit", ["ollama"]) is None


def test_get_mode_model_security_audit():
    model = get_mode_model("security", "audit", ["anthropic"])
    assert model is not None
    # Security audit should use frontier tier
    assert "anthropic" in model


# --- Tier navigation ---


def test_tier_up_micro():
    assert tier_up("micro") == "fast"


def test_tier_up_fast():
    assert tier_up("fast") == "local"


def test_tier_up_standard():
    assert tier_up("standard") == "frontier"


def test_tier_up_frontier():
    assert tier_up("frontier") is None


def test_tier_up_unknown():
    assert tier_up("nonexistent") is None


def test_tier_down_frontier():
    assert tier_down("frontier") == "standard"


def test_tier_down_micro():
    assert tier_down("micro") is None


def test_tier_down_unknown():
    assert tier_down("nonexistent") is None


# --- Model→tier lookup ---


def test_get_tier_for_model_known():
    tier = get_tier_for_model("anthropic/claude-opus-4-5")
    assert tier == "frontier"


def test_get_tier_for_model_micro():
    tier = get_tier_for_model("ollama/qwen3:8b")
    assert tier is not None


def test_get_tier_for_model_unknown():
    assert get_tier_for_model("unknown/model") is None


# --- Available tiers ---


def test_get_available_tiers():
    result = get_available_tiers(["ollama"])
    assert isinstance(result, dict)
    assert "micro" in result
    assert "frontier" in result
    # Micro should have ollama model, frontier shouldn't
    assert result["micro"] is not None
    assert result["frontier"] is None


def test_get_available_tiers_all_providers():
    result = get_available_tiers(["ollama", "anthropic", "openai"])
    assert all(v is not None for v in result.values())


# --- Provider detection ---


def test_provider_available_ollama():
    from scripts.lib.crux_model_tiers import _provider_available
    assert _provider_available("ollama") is True


def test_provider_available_anthropic_with_key():
    from scripts.lib.crux_model_tiers import _provider_available
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
        assert _provider_available("anthropic") is True


def test_provider_available_anthropic_without_key():
    from scripts.lib.crux_model_tiers import _provider_available
    with patch.dict(os.environ, {}, clear=True):
        assert _provider_available("anthropic") is False


def test_provider_available_anthropic_crux_key():
    from scripts.lib.crux_model_tiers import _provider_available
    with patch.dict(os.environ, {"CRUX_ANTHROPIC_API_KEY": "sk-test"}, clear=True):
        assert _provider_available("anthropic") is True


def test_provider_available_openai():
    from scripts.lib.crux_model_tiers import _provider_available
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        assert _provider_available("openai") is True


def test_provider_available_openai_crux_key():
    from scripts.lib.crux_model_tiers import _provider_available
    with patch.dict(os.environ, {"CRUX_OPENAI_API_KEY": "sk-test"}, clear=True):
        assert _provider_available("openai") is True


def test_provider_available_unknown():
    from scripts.lib.crux_model_tiers import _provider_available
    assert _provider_available("unknown_provider") is False


# --- Parse model ---


def test_parse_model_with_provider():
    from scripts.lib.crux_model_tiers import _parse_model
    assert _parse_model("anthropic/claude-opus-4-5") == ("anthropic", "claude-opus-4-5")


def test_parse_model_without_provider():
    from scripts.lib.crux_model_tiers import _parse_model
    assert _parse_model("qwen3:8b") == ("ollama", "qwen3:8b")


# --- Escalation ---


def test_escalate_validation_failure():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3:8b", "validation_failure", attempt=0, available_providers=["ollama", "anthropic"])
    assert result.escalated is True
    assert result.new_tier is not None


def test_escalate_validation_failure_max_reached():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3:8b", "validation_failure", attempt=2, available_providers=["ollama"])
    assert result.escalated is False
    assert "Max escalations" in result.reason


def test_escalate_quality_failure():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("openai/gpt-5-mini", "quality_failure", attempt=0, available_providers=["anthropic", "openai"])
    assert result.escalated is True
    assert result.new_tier is not None


def test_escalate_quality_failure_max_reached():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("openai/gpt-5-mini", "quality_failure", attempt=1, available_providers=["openai"])
    assert result.escalated is False


def test_escalate_provider_error():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3-coder:30b", "provider_error", attempt=0, available_providers=["ollama", "anthropic"])
    assert result.escalated is True
    assert "anthropic" in result.new_model


def test_escalate_provider_error_no_alternative():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3-coder:30b", "provider_error", attempt=0, available_providers=["ollama"])
    assert result.escalated is False
    assert "No alternative" in result.reason


def test_escalate_provider_error_max_retries():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3-coder:30b", "provider_error", attempt=2, available_providers=["ollama", "anthropic"])
    assert result.escalated is False


def test_escalate_timeout():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3:8b", "timeout", attempt=0, available_providers=["ollama", "anthropic"])
    assert result.escalated is True


def test_escalate_timeout_max_retries():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3:8b", "timeout", attempt=1, available_providers=["ollama"])
    assert result.escalated is False


def test_escalate_unknown_failure():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("ollama/qwen3:8b", "unknown_type", attempt=0)
    assert result.escalated is False
    assert "Unknown failure" in result.reason


def test_escalate_already_at_frontier():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("anthropic/claude-opus-4-5", "validation_failure", attempt=0, available_providers=["anthropic"])
    assert result.escalated is False
    assert "highest tier" in result.reason


def test_escalate_unknown_model():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("unknown/model", "validation_failure", attempt=0)
    assert result.escalated is False
    assert "Cannot determine tier" in result.reason


def test_escalate_no_model_at_next_tier():
    from scripts.lib.crux_model_tiers import escalate
    # micro → fast, but only unknown providers available
    result = escalate("ollama/qwen3:8b", "validation_failure", attempt=0, available_providers=[])
    assert result.escalated is False
    assert "No model available" in result.reason


def test_escalate_provider_error_unknown_model():
    from scripts.lib.crux_model_tiers import escalate
    result = escalate("unknown/model", "provider_error", attempt=0)
    assert result.escalated is False


def test_escalate_provider_error_auto_detect():
    from scripts.lib.crux_model_tiers import escalate
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=True):
        result = escalate("ollama/qwen3-coder:30b", "provider_error", attempt=0)
        assert result.escalated is True


def test_escalation_result_fields():
    from scripts.lib.crux_model_tiers import EscalationResult
    r = EscalationResult(escalated=True, new_model="m", new_tier="t", reason="r")
    assert r.escalated is True
    assert r.new_model == "m"
    assert r.new_tier == "t"
    assert r.reason == "r"
