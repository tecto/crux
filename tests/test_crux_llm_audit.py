"""Tests for crux_llm_audit.py — LLM-based script auditing for Gates 4-5."""

import json
from unittest.mock import patch, MagicMock

import pytest

from scripts.lib.crux_llm_audit import (
    audit_script_8b,
    audit_script_32b,
    format_audit_prompt,
)


SAMPLE_SCRIPT = """#!/bin/bash
set -euo pipefail
# Risk: medium
# Description: Deploy app
DRY_RUN="${DRY_RUN:-0}"
main() { echo "deploying"; }
main "$@"
"""

CLEAN_RESPONSE = json.dumps({
    "passed": True,
    "findings": [],
    "summary": "No security issues found.",
})

FINDINGS_RESPONSE = json.dumps({
    "passed": False,
    "findings": [
        {"severity": "high", "title": "Command injection", "description": "Unquoted variable expansion"},
    ],
    "summary": "1 issue found.",
})


# ---------------------------------------------------------------------------
# format_audit_prompt
# ---------------------------------------------------------------------------

class TestFormatAuditPrompt:
    def test_includes_script_content(self):
        prompt = format_audit_prompt("echo hello", "low")
        assert "echo hello" in prompt

    def test_includes_risk_level(self):
        prompt = format_audit_prompt("echo hello", "high")
        assert "high" in prompt.lower()

    def test_requests_json_response(self):
        prompt = format_audit_prompt("echo hello", "medium")
        assert "json" in prompt.lower()


# ---------------------------------------------------------------------------
# audit_script_8b
# ---------------------------------------------------------------------------

class TestAuditScript8b:
    def test_clean_audit_passes(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            result = audit_script_8b(SAMPLE_SCRIPT, "medium")
            assert result["passed"] is True
            assert result["skipped"] is False
            assert len(result["findings"]) == 0

    def test_audit_with_findings_fails(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": FINDINGS_RESPONSE}
            result = audit_script_8b(SAMPLE_SCRIPT, "medium")
            assert result["passed"] is False
            assert len(result["findings"]) == 1
            assert result["findings"][0]["severity"] == "high"

    def test_ollama_unavailable_skips_gracefully(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": False, "error": "Connection refused"}
            result = audit_script_8b(SAMPLE_SCRIPT, "medium")
            assert result["passed"] is True
            assert result["skipped"] is True
            assert "unavailable" in result["reason"].lower()

    def test_malformed_llm_response_skips(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": "not json at all"}
            result = audit_script_8b(SAMPLE_SCRIPT, "medium")
            assert result["passed"] is True
            assert result["skipped"] is True
            assert "parse" in result["reason"].lower()

    def test_uses_8b_model(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_8b(SAMPLE_SCRIPT, "medium")
            call_kwargs = mock_gen.call_args[1] if mock_gen.call_args[1] else {}
            call_args = mock_gen.call_args[0] if mock_gen.call_args[0] else ()
            # Model should contain 8b indicator
            all_args = str(call_args) + str(call_kwargs)
            assert "8b" in all_args.lower() or "small" in all_args.lower()

    def test_low_risk_still_audited(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            result = audit_script_8b(SAMPLE_SCRIPT, "low")
            assert result["skipped"] is False
            assert mock_gen.called

    def test_custom_endpoint(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_8b(SAMPLE_SCRIPT, "medium", endpoint="http://gpu:11434")
            _, kwargs = mock_gen.call_args
            assert kwargs.get("endpoint") == "http://gpu:11434"

    def test_custom_model(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_8b(SAMPLE_SCRIPT, "medium", model="custom:7b")
            _, kwargs = mock_gen.call_args
            assert kwargs.get("model") == "custom:7b"

    def test_markdown_wrapped_json_response(self):
        wrapped = f"```json\n{CLEAN_RESPONSE}\n```"
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": wrapped}
            result = audit_script_8b(SAMPLE_SCRIPT, "medium")
            assert result["passed"] is True
            assert result["skipped"] is False


# ---------------------------------------------------------------------------
# audit_script_32b
# ---------------------------------------------------------------------------

class TestAuditScript32b:
    def test_high_risk_runs_audit(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            result = audit_script_32b(SAMPLE_SCRIPT, "high")
            assert result["passed"] is True
            assert result["skipped"] is False
            assert mock_gen.called

    def test_non_high_risk_skips(self):
        result = audit_script_32b(SAMPLE_SCRIPT, "medium")
        assert result["passed"] is True
        assert result["skipped"] is True
        assert "high-risk" in result["reason"].lower() or "not high" in result["reason"].lower()

    def test_low_risk_skips(self):
        result = audit_script_32b(SAMPLE_SCRIPT, "low")
        assert result["skipped"] is True

    def test_audit_with_findings_fails(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": FINDINGS_RESPONSE}
            result = audit_script_32b(SAMPLE_SCRIPT, "high")
            assert result["passed"] is False
            assert len(result["findings"]) == 1

    def test_ollama_unavailable_skips_gracefully(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": False, "error": "Connection refused"}
            result = audit_script_32b(SAMPLE_SCRIPT, "high")
            assert result["passed"] is True
            assert result["skipped"] is True

    def test_uses_32b_model(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_32b(SAMPLE_SCRIPT, "high")
            all_args = str(mock_gen.call_args)
            assert "32b" in all_args.lower() or "large" in all_args.lower()

    def test_custom_model(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_32b(SAMPLE_SCRIPT, "high", model="custom:32b")
            _, kwargs = mock_gen.call_args
            assert kwargs.get("model") == "custom:32b"

    def test_malformed_response_skips(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": "garbage"}
            result = audit_script_32b(SAMPLE_SCRIPT, "high")
            assert result["passed"] is True
            assert result["skipped"] is True

    def test_custom_endpoint(self):
        with patch("scripts.lib.crux_llm_audit.generate") as mock_gen:
            mock_gen.return_value = {"success": True, "response": CLEAN_RESPONSE}
            audit_script_32b(SAMPLE_SCRIPT, "high", endpoint="http://gpu:11434")
            _, kwargs = mock_gen.call_args
            assert kwargs.get("endpoint") == "http://gpu:11434"
