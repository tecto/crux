"""Tests for audit backend abstraction (PLAN-169, PLAN-170, PLAN-182)."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.lib.crux_audit_backend import (
    AuditBackend,
    AuditFinding,
    AuditRequiredError,
    AuditResult,
    AnthropicBackend,
    ClaudeSubagentBackend,
    DisabledBackend,
    OllamaBackend,
    OpenAIBackend,
    _format_audit_prompt,
    _parse_audit_response,
    _create_backend,
    detect_context_mode,
    detect_opencode_context,
    get_adversarial_backend,
    get_audit_backend,
    get_backend_status,
    get_configured_backend,
)
import scripts.lib.crux_audit_backend as audit_backend_mod


@pytest.fixture(autouse=True)
def reset_backend_cache():
    """Reset the backend cache before each test to ensure isolation."""
    audit_backend_mod._cached_backend = None
    audit_backend_mod._cached_backend_check_time = 0
    yield
    audit_backend_mod._cached_backend = None
    audit_backend_mod._cached_backend_check_time = 0


# ---------------------------------------------------------------------------
# AuditResult tests
# ---------------------------------------------------------------------------


class TestAuditResult:
    def test_passed_result(self):
        result = AuditResult(passed=True, skipped=False, backend="test")
        assert result.passed is True
        assert result.skipped is False
        assert result.findings == []

    def test_failed_result_with_findings(self):
        finding = AuditFinding(
            severity="high",
            title="Command injection",
            description="Unsafe variable expansion",
        )
        result = AuditResult(
            passed=False,
            skipped=False,
            findings=[finding],
            backend="test",
        )
        assert result.passed is False
        assert len(result.findings) == 1
        assert result.findings[0].severity == "high"

    def test_skipped_result(self):
        result = AuditResult(
            passed=True,
            skipped=True,
            reason="Ollama unavailable",
            backend="test",
        )
        assert result.skipped is True
        assert "Ollama" in result.reason


# ---------------------------------------------------------------------------
# OllamaBackend tests
# ---------------------------------------------------------------------------


class TestOllamaBackend:
    def test_name_includes_model(self):
        backend = OllamaBackend(model="qwen3:8b")
        assert "qwen3:8b" in backend.name
        assert "Ollama" in backend.name

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_is_available_when_running(self, mock_check):
        mock_check.return_value = True
        backend = OllamaBackend()
        assert backend.is_available() is True

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_is_available_when_down(self, mock_check):
        mock_check.return_value = False
        backend = OllamaBackend()
        assert backend.is_available() is False

    @patch("scripts.lib.crux_audit_backend.generate")
    def test_audit_success(self, mock_generate):
        mock_generate.return_value = {
            "success": True,
            "response": json.dumps({
                "passed": True,
                "findings": [],
                "summary": "No issues found",
            }),
        }
        backend = OllamaBackend()
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.passed is True
        assert result.skipped is False
        assert result.summary == "No issues found"

    @patch("scripts.lib.crux_audit_backend.generate")
    def test_audit_with_findings(self, mock_generate):
        mock_generate.return_value = {
            "success": True,
            "response": json.dumps({
                "passed": False,
                "findings": [
                    {
                        "severity": "high",
                        "title": "Command injection",
                        "description": "Unsafe use of $VAR",
                    }
                ],
                "summary": "Security issues found",
            }),
        }
        backend = OllamaBackend()
        result = backend.audit("rm -rf $VAR", "high", "system prompt")

        assert result.passed is False
        assert len(result.findings) == 1
        assert result.findings[0].severity == "high"

    @patch("scripts.lib.crux_audit_backend.generate")
    def test_audit_ollama_failure(self, mock_generate):
        mock_generate.return_value = {"success": False, "error": "Connection refused"}
        backend = OllamaBackend()
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.passed is True  # Skipped means pass
        assert result.skipped is True
        assert "failed" in result.reason.lower()

    @patch("scripts.lib.crux_audit_backend.generate")
    def test_audit_invalid_json_response(self, mock_generate):
        mock_generate.return_value = {
            "success": True,
            "response": "This is not JSON",
        }
        backend = OllamaBackend()
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "parse" in result.reason.lower()


# ---------------------------------------------------------------------------
# ClaudeSubagentBackend tests
# ---------------------------------------------------------------------------


class TestClaudeSubagentBackend:
    def test_name(self):
        backend = ClaudeSubagentBackend()
        assert "Claude" in backend.name
        assert "subagent" in backend.name

    @patch("subprocess.run")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_is_available_with_claude(self, mock_find, mock_run):
        mock_find.return_value = "/usr/local/bin/claude"
        backend = ClaudeSubagentBackend()
        backend._claude_path = "/usr/local/bin/claude"
        assert backend.is_available() is True

    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_is_available_without_claude(self, mock_find):
        mock_find.return_value = None
        backend = ClaudeSubagentBackend()
        backend._claude_path = None
        assert backend.is_available() is False

    def test_audit_without_claude_binary(self):
        backend = ClaudeSubagentBackend()
        backend._claude_path = None
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "not found" in result.reason.lower()


# ---------------------------------------------------------------------------
# AnthropicBackend tests (PLAN-182)
# ---------------------------------------------------------------------------


class TestAnthropicBackend:
    def test_name_includes_model(self):
        backend = AnthropicBackend(model="claude-3-haiku-20240307")
        assert "claude-3-haiku" in backend.name
        assert "Anthropic" in backend.name

    def test_is_available_with_api_key(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            assert backend.is_available() is True

    def test_is_available_with_crux_api_key(self):
        with patch.dict("os.environ", {"CRUX_ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
            backend = AnthropicBackend()
            assert backend.is_available() is True

    def test_is_unavailable_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            backend = AnthropicBackend()
            assert backend.is_available() is False

    def test_audit_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            backend = AnthropicBackend()
            result = backend.audit("echo hello", "low", "system prompt")
            assert result.skipped is True
            assert "API key" in result.reason

    def test_audit_without_package(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            with patch.object(backend, "_get_client", return_value=None):
                result = backend.audit("echo hello", "low", "system prompt")
                assert result.skipped is True
                assert "not installed" in result.reason

    def test_audit_success(self):
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps({
            "passed": True,
            "findings": [],
            "summary": "No issues found",
        }))]
        mock_client.messages.create.return_value = mock_message

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.passed is True
            assert result.skipped is False
            assert "Anthropic" in result.backend

    def test_audit_with_findings(self):
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps({
            "passed": False,
            "findings": [{"severity": "high", "title": "Issue", "description": "Bad"}],
            "summary": "Found issues",
        }))]
        mock_client.messages.create.return_value = mock_message

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            backend._client = mock_client
            result = backend.audit("rm -rf /", "high", "system prompt")

            assert result.passed is False
            assert len(result.findings) == 1
            assert result.findings[0].severity == "high"

    def test_implements_protocol(self):
        backend = AnthropicBackend()
        assert isinstance(backend, AuditBackend)


# ---------------------------------------------------------------------------
# OpenAIBackend tests (PLAN-182)
# ---------------------------------------------------------------------------


class TestOpenAIBackend:
    def test_name_includes_model(self):
        backend = OpenAIBackend(model="gpt-4o-mini")
        assert "gpt-4o-mini" in backend.name
        assert "OpenAI" in backend.name

    def test_is_available_with_api_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            assert backend.is_available() is True

    def test_is_available_with_crux_api_key(self):
        with patch.dict("os.environ", {"CRUX_OPENAI_API_KEY": "sk-test"}, clear=True):
            backend = OpenAIBackend()
            assert backend.is_available() is True

    def test_is_unavailable_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            backend = OpenAIBackend()
            assert backend.is_available() is False

    def test_audit_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            backend = OpenAIBackend()
            result = backend.audit("echo hello", "low", "system prompt")
            assert result.skipped is True
            assert "API key" in result.reason

    def test_audit_without_package(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            with patch.object(backend, "_get_client", return_value=None):
                result = backend.audit("echo hello", "low", "system prompt")
                assert result.skipped is True
                assert "not installed" in result.reason

    def test_audit_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "passed": True,
            "findings": [],
            "summary": "No issues found",
        })))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.passed is True
            assert result.skipped is False
            assert "OpenAI" in result.backend

    def test_audit_with_findings(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "passed": False,
            "findings": [{"severity": "medium", "title": "Warning", "description": "Check this"}],
            "summary": "Review needed",
        })))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            backend._client = mock_client
            result = backend.audit("curl $URL", "medium", "system prompt")

            assert result.passed is False
            assert len(result.findings) == 1

    def test_implements_protocol(self):
        backend = OpenAIBackend()
        assert isinstance(backend, AuditBackend)


# ---------------------------------------------------------------------------
# DisabledBackend tests
# ---------------------------------------------------------------------------


class TestDisabledBackend:
    def test_name_indicates_disabled(self):
        backend = DisabledBackend()
        assert "DISABLED" in backend.name

    def test_is_always_available(self):
        backend = DisabledBackend()
        assert backend.is_available() is True

    def test_audit_always_skips(self):
        backend = DisabledBackend()
        result = backend.audit("rm -rf /", "high", "system prompt")

        assert result.passed is True
        assert result.skipped is True
        assert "No audit backend" in result.reason


# ---------------------------------------------------------------------------
# Backend selection tests
# ---------------------------------------------------------------------------


class TestGetAuditBackend:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_prefers_ollama_when_available(self, mock_check):
        mock_check.return_value = True
        # Clear cache
        import scripts.lib.crux_audit_backend as mod
        mod._cached_backend = None
        mod._cached_backend_check_time = 0

        backend = get_audit_backend(force_refresh=True)
        assert isinstance(backend, OllamaBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_falls_back_to_claude(self, mock_find, mock_check):
        mock_check.return_value = False
        mock_find.return_value = "/usr/local/bin/claude"

        # Clear API keys so Claude subagent is the fallback
        with patch.dict("os.environ", {}, clear=True):
            backend = get_audit_backend(force_refresh=True)
            assert isinstance(backend, ClaudeSubagentBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_falls_back_to_disabled(self, mock_find, mock_check):
        mock_check.return_value = False
        mock_find.return_value = None

        # Clear API keys so DisabledBackend is the fallback
        with patch.dict("os.environ", {}, clear=True):
            backend = get_audit_backend(force_refresh=True)
            assert isinstance(backend, DisabledBackend)


class TestGetBackendStatus:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_returns_status_dict(self, mock_find, mock_check):
        mock_check.return_value = True
        mock_find.return_value = "/usr/local/bin/claude"

        import scripts.lib.crux_audit_backend as mod
        mod._cached_backend = None
        mod._cached_backend_check_time = 0

        status = get_backend_status()

        assert "active_backend" in status
        assert "ollama_available" in status
        assert "claude_available" in status
        assert "backends" in status


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestFormatAuditPrompt:
    def test_includes_risk_level(self):
        prompt = _format_audit_prompt("echo hello", "high")
        assert "high-risk" in prompt

    def test_includes_script_content(self):
        prompt = _format_audit_prompt("rm -rf /tmp", "low")
        assert "rm -rf /tmp" in prompt

    def test_includes_code_block(self):
        prompt = _format_audit_prompt("echo test", "medium")
        assert "```bash" in prompt


class TestParseAuditResponse:
    def test_parses_valid_json(self):
        response = json.dumps({"passed": True, "findings": []})
        result = _parse_audit_response(response)
        assert result["passed"] is True

    def test_parses_json_in_code_block(self):
        response = "```json\n{\"passed\": false, \"findings\": []}\n```"
        result = _parse_audit_response(response)
        assert result["passed"] is False

    def test_returns_none_for_invalid_json(self):
        result = _parse_audit_response("not json")
        assert result is None

    def test_returns_none_for_empty_string(self):
        result = _parse_audit_response("")
        assert result is None


# ---------------------------------------------------------------------------
# Protocol compliance tests
# ---------------------------------------------------------------------------


class TestBackendProtocol:
    def test_ollama_implements_protocol(self):
        backend = OllamaBackend()
        assert isinstance(backend, AuditBackend)

    def test_claude_implements_protocol(self):
        backend = ClaudeSubagentBackend()
        assert isinstance(backend, AuditBackend)

    def test_disabled_implements_protocol(self):
        backend = DisabledBackend()
        assert isinstance(backend, AuditBackend)


# ---------------------------------------------------------------------------
# OpenCode enforcement tests (PLAN-170)
# ---------------------------------------------------------------------------


class TestOpenCodeDetection:
    def test_detect_opencode_from_env(self):
        with patch.dict("os.environ", {"CRUX_TOOL": "opencode"}):
            assert detect_opencode_context() is True

    def test_detect_claude_code_from_env(self):
        with patch.dict("os.environ", {"CRUX_TOOL": "claude-code"}):
            assert detect_opencode_context() is False

    def test_detect_claude_code_entry_point(self):
        with patch.dict("os.environ", {"CLAUDE_CODE_ENTRY_POINT": "1"}, clear=False):
            # Clear CRUX_TOOL to test fallback
            env = {"CLAUDE_CODE_ENTRY_POINT": "1"}
            with patch.dict("os.environ", env, clear=True):
                assert detect_opencode_context() is False

    def test_context_mode_unknown_default(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                mode = detect_context_mode()
                assert mode == "unknown"


class TestOpenCodeEnforcement:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_opencode_context")
    def test_opencode_raises_when_no_backend_available(self, mock_detect, mock_check):
        mock_detect.return_value = True
        mock_check.return_value = False

        # Clear all API keys too
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuditRequiredError) as exc_info:
                get_audit_backend(force_refresh=True, context="auto")

            # PLAN-182: error message now mentions multiple options
            assert "audit backend" in str(exc_info.value).lower()

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_opencode_explicit_context_raises_when_no_backend(self, mock_check):
        mock_check.return_value = False

        # Clear all API keys
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuditRequiredError):
                get_audit_backend(force_refresh=True, context="opencode")

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_opencode_with_ollama_works(self, mock_check):
        mock_check.return_value = True

        import scripts.lib.crux_audit_backend as mod
        mod._cached_backend = None
        mod._cached_backend_check_time = 0

        backend = get_audit_backend(force_refresh=True, context="opencode")
        assert isinstance(backend, OllamaBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_claude_code_still_falls_back(self, mock_find, mock_check):
        mock_check.return_value = False
        mock_find.return_value = "/usr/local/bin/claude"

        # Clear API keys so Claude subagent is the fallback
        with patch.dict("os.environ", {}, clear=True):
            # Claude Code mode should still fall back
            backend = get_audit_backend(force_refresh=True, context="claude-code")
            assert isinstance(backend, ClaudeSubagentBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_enforce_opencode_can_be_disabled(self, mock_find, mock_check):
        mock_check.return_value = False
        mock_find.return_value = None  # No Claude either

        # Clear API keys so DisabledBackend is the fallback
        with patch.dict("os.environ", {}, clear=True):
            # With enforce_opencode=False, should not raise even in opencode context
            backend = get_audit_backend(
                force_refresh=True,
                context="opencode",
                enforce_opencode=False,
            )
            # Falls through to DisabledBackend since both Ollama and Claude unavailable
            assert isinstance(backend, DisabledBackend)


class TestBackendStatusWithMode:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_context_mode")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_status_shows_opencode_blocked(self, mock_find, mock_mode, mock_check):
        mock_check.return_value = False
        mock_mode.return_value = "opencode"
        mock_find.return_value = None

        # Clear API keys so no backend is available
        with patch.dict("os.environ", {}, clear=True):
            status = get_backend_status()

            assert status["context_mode"] == "opencode"
            assert status["audit_required"] is True
            assert status["audit_blocked"] is True
            assert "BLOCKED" in status["active_backend"]

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_context_mode")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    def test_status_shows_claude_code_fallback(self, mock_find, mock_mode, mock_check):
        mock_check.return_value = False
        mock_mode.return_value = "claude-code"
        mock_find.return_value = "/usr/local/bin/claude"

        with patch.dict("os.environ", {}, clear=True):
            status = get_backend_status()

            assert status["context_mode"] == "claude-code"
            assert status["audit_required"] is False
            assert status["audit_blocked"] is False


# ---------------------------------------------------------------------------
# PLAN-182: Flexible API backend tests
# ---------------------------------------------------------------------------


class TestCreateBackend:
    def test_creates_ollama_backend(self):
        backend = _create_backend("ollama", "qwen3:8b")
        assert isinstance(backend, OllamaBackend)
        assert "qwen3:8b" in backend.name

    def test_creates_anthropic_backend(self):
        backend = _create_backend("anthropic", "claude-3-opus-20240229")
        assert isinstance(backend, AnthropicBackend)
        assert "claude-3-opus" in backend.name

    def test_creates_openai_backend(self):
        backend = _create_backend("openai", "gpt-4")
        assert isinstance(backend, OpenAIBackend)
        assert "gpt-4" in backend.name

    def test_creates_subagent_backend(self):
        backend = _create_backend("subagent")
        assert isinstance(backend, ClaudeSubagentBackend)

    def test_returns_none_for_unknown_type(self):
        backend = _create_backend("invalid")
        assert backend is None

    def test_case_insensitive(self):
        backend = _create_backend("OLLAMA")
        assert isinstance(backend, OllamaBackend)


class TestGetConfiguredBackend:
    def test_returns_none_when_not_configured(self):
        with patch.dict("os.environ", {}, clear=True):
            primary, adversarial = get_configured_backend()
            assert primary is None
            assert adversarial is None

    def test_returns_primary_backend(self):
        with patch.dict("os.environ", {"CRUX_AUDIT_BACKEND": "anthropic"}, clear=True):
            primary, adversarial = get_configured_backend()
            assert primary == "anthropic"
            assert adversarial is None

    def test_returns_adversarial_backend(self):
        with patch.dict("os.environ", {"CRUX_ADVERSARIAL_BACKEND": "openai"}, clear=True):
            primary, adversarial = get_configured_backend()
            assert primary is None
            assert adversarial == "openai"

    def test_returns_both_backends(self):
        with patch.dict("os.environ", {
            "CRUX_AUDIT_BACKEND": "ollama",
            "CRUX_ADVERSARIAL_BACKEND": "anthropic",
        }, clear=True):
            primary, adversarial = get_configured_backend()
            assert primary == "ollama"
            assert adversarial == "anthropic"


class TestOpenCodeWithAPIBackends:
    """PLAN-182: OpenCode mode should accept API backends."""

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_opencode_works_with_anthropic(self, mock_check):
        mock_check.return_value = False  # Ollama not available

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
            backend = get_audit_backend(force_refresh=True, context="opencode")
            assert isinstance(backend, AnthropicBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_opencode_works_with_openai(self, mock_check):
        mock_check.return_value = False  # Ollama not available

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=True):
            backend = get_audit_backend(force_refresh=True, context="opencode")
            assert isinstance(backend, OpenAIBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_opencode_prefers_ollama(self, mock_check):
        mock_check.return_value = True  # Ollama available

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = get_audit_backend(force_refresh=True, context="opencode")
            assert isinstance(backend, OllamaBackend)


class TestAdversarialBackend:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_adversarial_uses_configured_backend(self, mock_check):
        mock_check.return_value = True  # Ollama available

        with patch.dict("os.environ", {
            "CRUX_ADVERSARIAL_BACKEND": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
        }):
            backend = get_adversarial_backend(force_refresh=True, context="claude-code")
            assert isinstance(backend, AnthropicBackend)

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_adversarial_uses_model_config(self, mock_check):
        mock_check.return_value = False

        with patch.dict("os.environ", {
            "CRUX_ADVERSARIAL_BACKEND": "anthropic",
            "CRUX_ADVERSARIAL_MODEL": "claude-3-opus-20240229",
            "ANTHROPIC_API_KEY": "sk-ant-test",
        }):
            backend = get_adversarial_backend(force_refresh=True, context="claude-code")
            assert "claude-3-opus" in backend.name

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_adversarial_falls_back_to_primary(self, mock_check):
        mock_check.return_value = True  # Ollama available

        # No adversarial configured, should use same as primary
        with patch.dict("os.environ", {}, clear=True):
            backend = get_adversarial_backend(force_refresh=True, context="claude-code")
            assert isinstance(backend, OllamaBackend)


class TestBackendStatusPlan182:
    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_context_mode")
    def test_status_includes_api_backends(self, mock_mode, mock_check):
        mock_check.return_value = False
        mock_mode.return_value = "claude-code"

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            status = get_backend_status()

            assert "anthropic_available" in status
            assert "openai_available" in status
            assert status["anthropic_available"] is True
            assert "backends" in status
            assert "anthropic" in status["backends"]

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_context_mode")
    def test_status_includes_configured_backends(self, mock_mode, mock_check):
        mock_check.return_value = True
        mock_mode.return_value = "opencode"

        with patch.dict("os.environ", {
            "CRUX_AUDIT_BACKEND": "ollama",
            "CRUX_ADVERSARIAL_BACKEND": "anthropic",
        }):
            status = get_backend_status()

            assert "configured" in status
            assert status["configured"]["primary"] == "ollama"
            assert status["configured"]["adversarial"] == "anthropic"


# ---------------------------------------------------------------------------
# Coverage gap tests
# ---------------------------------------------------------------------------


class TestOllamaBackendEndpoint:
    """Cover line 136: OllamaBackend.audit passes endpoint kwarg."""

    @patch("scripts.lib.crux_audit_backend.generate")
    def test_audit_passes_endpoint(self, mock_generate):
        mock_generate.return_value = {
            "success": True,
            "response": json.dumps({"passed": True, "findings": [], "summary": "ok"}),
        }
        backend = OllamaBackend(model="qwen3:8b", endpoint="http://custom:11434")
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.passed is True
        assert result.skipped is False
        # Verify endpoint was passed to generate
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args
        assert call_kwargs.kwargs.get("endpoint") == "http://custom:11434" or \
               (len(call_kwargs.args) == 0 and "endpoint" in call_kwargs[1])


class TestAnthropicGetClient:
    """Cover lines 211-216: AnthropicBackend._get_client paths."""

    def test_get_client_import_error(self):
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("no anthropic")
            return original_import(name, *args, **kwargs)

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            with patch("builtins.__import__", side_effect=mock_import):
                client = backend._get_client()
                assert client is None

    def test_get_client_success(self):
        """Cover line 213: successful client creation."""
        mock_anthropic_cls = MagicMock()
        mock_module = MagicMock()
        mock_module.Anthropic = mock_anthropic_cls

        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                return mock_module
            return original_import(name, *args, **kwargs)

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            with patch("builtins.__import__", side_effect=mock_import):
                client = backend._get_client()
                assert client is not None


class TestAnthropicAuditUnparseable:
    """Cover line 256: Anthropic audit returns unparseable JSON."""

    def test_audit_unparseable_response(self):
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not valid json at all")]
        mock_client.messages.create.return_value = mock_message

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.skipped is True
            assert "parse" in result.reason.lower()


class TestAnthropicAuditException:
    """Cover lines 281-283: Anthropic audit API exception."""

    def test_audit_api_exception(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API timeout")

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            backend = AnthropicBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.skipped is True
            assert "API error" in result.reason


class TestOpenAIGetClient:
    """Cover lines 326-331: OpenAIBackend._get_client paths."""

    def test_get_client_import_error(self):
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("no openai")
            return original_import(name, *args, **kwargs)

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            with patch("builtins.__import__", side_effect=mock_import):
                client = backend._get_client()
                assert client is None

    def test_get_client_success(self):
        """Cover line 328: successful client creation."""
        mock_openai_cls = MagicMock()
        mock_module = MagicMock()
        mock_module.OpenAI = mock_openai_cls

        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                return mock_module
            return original_import(name, *args, **kwargs)

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            with patch("builtins.__import__", side_effect=mock_import):
                client = backend._get_client()
                assert client is not None


class TestOpenAIAuditUnparseable:
    """Cover line 373: OpenAI audit returns unparseable JSON."""

    def test_audit_unparseable_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not json"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.skipped is True
            assert "parse" in result.reason.lower()


class TestOpenAIAuditException:
    """Cover lines 398-400: OpenAI audit API exception."""

    def test_audit_api_exception(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API timeout")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            backend = OpenAIBackend()
            backend._client = mock_client
            result = backend.audit("echo hello", "low", "system prompt")

            assert result.skipped is True
            assert "API error" in result.reason


class TestClaudeSubagentFindBinary:
    """Cover lines 447-448: _find_claude_binary file exists path."""

    @patch("os.access", return_value=True)
    @patch("os.path.isfile", return_value=True)
    @patch("subprocess.run")
    def test_find_binary_from_file_path(self, mock_run, mock_isfile, mock_access):
        # The first candidate (~/.claude/local/claude) should match
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        result = backend._find_claude_binary()
        assert result is not None

    @patch("os.access", return_value=False)
    @patch("os.path.isfile", return_value=False)
    @patch("subprocess.run")
    def test_find_binary_from_path_which(self, mock_run, mock_isfile, mock_access):
        # All file paths fail, "which claude" succeeds
        mock_run.return_value = MagicMock(returncode=0, stdout="/usr/bin/claude\n")
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        result = backend._find_claude_binary()
        assert result == "/usr/bin/claude"

    @patch("os.access", return_value=False)
    @patch("os.path.isfile", return_value=False)
    @patch("subprocess.run")
    def test_find_binary_which_fails(self, mock_run, mock_isfile, mock_access):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        result = backend._find_claude_binary()
        assert result is None


class TestClaudeSubagentAudit:
    """Cover lines 475-544: ClaudeSubagentBackend.audit subprocess paths."""

    @patch("subprocess.run")
    def test_audit_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"passed": True, "findings": [], "summary": "ok"}),
            stderr="",
        )
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.passed is True
        assert result.skipped is False
        assert result.summary == "ok"

    @patch("subprocess.run")
    def test_audit_with_findings(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "passed": False,
                "findings": [{"severity": "high", "title": "Bad", "description": "Very bad"}],
                "summary": "issues",
            }),
            stderr="",
        )
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("rm -rf /", "high", "system prompt")

        assert result.passed is False
        assert len(result.findings) == 1

    @patch("subprocess.run")
    def test_audit_cli_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
        )
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "failed" in result.reason.lower()

    @patch("subprocess.run")
    def test_audit_unparseable_response(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not json at all",
            stderr="",
        )
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "parse" in result.reason.lower()

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=120))
    def test_audit_timeout(self, mock_run):
        import subprocess
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "timed out" in result.reason.lower()

    @patch("subprocess.run", side_effect=OSError("Permission denied"))
    def test_audit_os_error(self, mock_run):
        backend = ClaudeSubagentBackend.__new__(ClaudeSubagentBackend)
        backend._claude_path = "/usr/local/bin/claude"
        result = backend.audit("echo hello", "low", "system prompt")

        assert result.skipped is True
        assert "error" in result.reason.lower()


class TestDetectOpenCodeStateFile:
    """Cover lines 612-619, 623: detect_opencode_context state file and OPENCODE_SESSION."""

    def test_opencode_from_state_file(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="opencode\n"):
                    assert detect_opencode_context() is True

    def test_claude_code_from_state_file(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="claude-code\n"):
                    assert detect_opencode_context() is False

    def test_both_from_state_file(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="both\n"):
                    assert detect_opencode_context() is False

    def test_state_file_read_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", side_effect=OSError("denied")):
                    # Should fall through gracefully
                    assert detect_opencode_context() is False

    def test_opencode_session_env(self):
        with patch.dict("os.environ", {"OPENCODE_SESSION": "1"}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                assert detect_opencode_context() is True


class TestDetectContextModeStateFile:
    """Cover lines 640, 644, 648-653: detect_context_mode state file paths."""

    def test_context_mode_claude_code_from_env(self):
        with patch.dict("os.environ", {"CLAUDE_CODE_ENTRY_POINT": "1"}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                mode = detect_context_mode()
                assert mode == "claude-code"

    def test_context_mode_from_state_file_claude_code(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="claude-code\n"):
                    mode = detect_context_mode()
                    assert mode == "claude-code"

    def test_context_mode_from_state_file_both(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="both\n"):
                    mode = detect_context_mode()
                    assert mode == "both"

    def test_context_mode_from_state_file_opencode(self):
        with patch.dict("os.environ", {"CRUX_TOOL": "opencode"}, clear=True):
            mode = detect_context_mode()
            assert mode == "opencode"

    def test_context_mode_state_file_read_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", side_effect=OSError("denied")):
                    mode = detect_context_mode()
                    assert mode == "unknown"

    def test_context_mode_state_file_unknown_tool(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value="vim\n"):
                    mode = detect_context_mode()
                    assert mode == "unknown"


class TestCreateBackendFinalReturn:
    """Cover line 701: _create_backend final return None."""

    def test_create_backend_with_default_models(self):
        # Test each backend type without explicit model to cover default paths
        b1 = _create_backend("ollama")
        assert isinstance(b1, OllamaBackend)
        b2 = _create_backend("anthropic")
        assert isinstance(b2, AnthropicBackend)
        b3 = _create_backend("openai")
        assert isinstance(b3, OpenAIBackend)

    def test_create_backend_known_class_but_unhandled_type(self):
        """Cover line 701: backend_type in _BACKEND_CLASSES but not in if/elif chain."""
        # Temporarily add a fake backend type to the class map
        with patch.dict(audit_backend_mod._BACKEND_CLASSES, {"custom": MagicMock}):
            result = _create_backend("custom")
            assert result is None


class TestConfiguredBackendOpenCodeEnforcement:
    """Cover lines 778-779: configured backend unavailable raises in opencode."""

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_configured_unavailable_raises_opencode(self, mock_check):
        mock_check.return_value = False
        with patch.dict("os.environ", {
            "CRUX_AUDIT_BACKEND": "ollama",
        }, clear=True):
            with pytest.raises(AuditRequiredError) as exc_info:
                get_audit_backend(force_refresh=True, context="opencode")
            assert "not available" in str(exc_info.value).lower()


class TestCachedBackendReturn:
    """Cover line 800: cached backend return path."""

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    def test_cached_backend_returned(self, mock_check):
        import time
        mock_check.return_value = True

        # First call populates cache
        backend1 = get_audit_backend(force_refresh=True)
        assert isinstance(backend1, OllamaBackend)

        # Second call should return cached (no force_refresh)
        mock_check.return_value = False  # Would fail if not cached
        audit_backend_mod._cached_backend_check_time = time.time()  # recent
        backend2 = get_audit_backend(force_refresh=False)
        assert isinstance(backend2, OllamaBackend)
        assert backend2 is backend1


class TestGetBackendStatusAuditRequiredError:
    """Cover lines 929-931: get_backend_status catches AuditRequiredError."""

    @patch("scripts.lib.crux_audit_backend.check_ollama_running")
    @patch("scripts.lib.crux_audit_backend.detect_context_mode")
    @patch.object(ClaudeSubagentBackend, "_find_claude_binary")
    @patch("scripts.lib.crux_audit_backend.get_audit_backend")
    def test_status_catches_audit_required_error(self, mock_get, mock_find, mock_mode, mock_check):
        mock_check.return_value = False
        mock_mode.return_value = "claude-code"
        mock_find.return_value = None
        mock_get.side_effect = AuditRequiredError("No backend")

        with patch.dict("os.environ", {}, clear=True):
            status = get_backend_status()
            assert status["audit_blocked"] is True
            assert "BLOCKED" in status["active_backend"]
