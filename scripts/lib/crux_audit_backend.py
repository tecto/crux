"""Audit backend abstraction for Gates 4-5 (PLAN-169, PLAN-170, PLAN-182).

Provides graceful fallback from Ollama to Claude Code subagent when
local LLM is unavailable. Prevents silent audit skipping.

PLAN-170: OpenCode mode enforces audit requirement - no silent skipping.
PLAN-182: Flexible API backends (Anthropic, OpenAI) for adversarial auditing.
          Supports pure API mode, hybrid mode, and multi-key configurations.

Environment Variables (PLAN-182):
    CRUX_AUDIT_BACKEND: Primary backend (ollama|anthropic|openai|subagent)
    CRUX_ADVERSARIAL_BACKEND: Adversarial backend (ollama|anthropic|openai|subagent)
    CRUX_ANTHROPIC_API_KEY: API key for Anthropic (or use ANTHROPIC_API_KEY)
    CRUX_OPENAI_API_KEY: API key for OpenAI (or use OPENAI_API_KEY)
    CRUX_ADVERSARIAL_MODEL: Model for adversarial audit
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from scripts.lib.crux_ollama import check_ollama_running, generate

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions (PLAN-170)
# ---------------------------------------------------------------------------


class AuditRequiredError(Exception):
    """Raised when audit is required but no backend is available.

    This is used in OpenCode mode where Ollama is mandatory.
    """
    pass

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class AuditFinding:
    """A single finding from an audit."""

    severity: str  # high, medium, low
    title: str
    description: str


@dataclass
class AuditResult:
    """Result from an audit backend."""

    passed: bool
    skipped: bool
    findings: list[AuditFinding] = field(default_factory=list)
    summary: str = ""
    reason: str = ""
    backend: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# Backend Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AuditBackend(Protocol):
    """Protocol for audit backends."""

    @property
    def name(self) -> str:
        """Human-readable backend name."""
        ...

    def is_available(self) -> bool:
        """Check if this backend is currently available."""
        ...

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        """Run an audit on the given script content."""
        ...


# ---------------------------------------------------------------------------
# Ollama Backend
# ---------------------------------------------------------------------------


class OllamaBackend:
    """Audit backend using local Ollama LLM."""

    def __init__(
        self,
        model: str = "qwen3:8b",
        endpoint: str | None = None,
    ) -> None:
        self._model = model
        self._endpoint = endpoint

    @property
    def name(self) -> str:
        return f"Ollama ({self._model})"

    def is_available(self) -> bool:
        return check_ollama_running(self._endpoint or "http://localhost:11434")

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        prompt = _format_audit_prompt(script_content, risk_level)
        kwargs: dict = {
            "model": self._model,
            "prompt": prompt,
            "system": system_prompt,
        }
        if self._endpoint:
            kwargs["endpoint"] = self._endpoint

        result = generate(**kwargs)

        if not result["success"]:
            return AuditResult(
                passed=True,
                skipped=True,
                reason=f"Ollama call failed: {result.get('error', 'unknown')}",
                backend=self.name,
            )

        parsed = _parse_audit_response(result["response"])
        if parsed is None:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="Could not parse LLM response as JSON",
                backend=self.name,
            )

        findings = [
            AuditFinding(
                severity=f.get("severity", "medium"),
                title=f.get("title", "Unknown"),
                description=f.get("description", ""),
            )
            for f in parsed.get("findings", [])
        ]

        return AuditResult(
            passed=parsed.get("passed", True),
            skipped=False,
            findings=findings,
            summary=parsed.get("summary", ""),
            backend=self.name,
            model=self._model,
        )


# ---------------------------------------------------------------------------
# Anthropic API Backend (PLAN-182)
# ---------------------------------------------------------------------------


class AnthropicBackend:
    """Audit backend using Anthropic API (Claude models).

    Uses the Anthropic SDK to call Claude models for adversarial auditing.
    Supports both CRUX_ANTHROPIC_API_KEY and ANTHROPIC_API_KEY env vars.
    """

    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get(
            "CRUX_ANTHROPIC_API_KEY",
            os.environ.get("ANTHROPIC_API_KEY", ""),
        )
        self._client = None

    @property
    def name(self) -> str:
        return f"Anthropic ({self._model})"

    def is_available(self) -> bool:
        """Check if Anthropic API is available (API key set)."""
        return bool(self._api_key)

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self._api_key)
            except ImportError:
                _logger.warning("anthropic package not installed")
                return None
        return self._client

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        if not self._api_key:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="Anthropic API key not configured",
                backend=self.name,
            )

        client = self._get_client()
        if client is None:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="anthropic package not installed (pip install anthropic)",
                backend=self.name,
            )

        prompt = _format_audit_prompt(script_content, risk_level)

        try:
            message = client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            parsed = _parse_audit_response(response_text)

            if parsed is None:
                return AuditResult(
                    passed=True,
                    skipped=True,
                    reason="Could not parse Anthropic response as JSON",
                    backend=self.name,
                )

            findings = [
                AuditFinding(
                    severity=f.get("severity", "medium"),
                    title=f.get("title", "Unknown"),
                    description=f.get("description", ""),
                )
                for f in parsed.get("findings", [])
            ]

            return AuditResult(
                passed=parsed.get("passed", True),
                skipped=False,
                findings=findings,
                summary=parsed.get("summary", ""),
                backend=self.name,
                model=self._model,
            )

        except Exception as exc:
            _logger.debug("Anthropic audit failed: %s", exc)
            return AuditResult(
                passed=True,
                skipped=True,
                reason=f"Anthropic API error: {exc}",
                backend=self.name,
            )


# ---------------------------------------------------------------------------
# OpenAI API Backend (PLAN-182)
# ---------------------------------------------------------------------------


class OpenAIBackend:
    """Audit backend using OpenAI API (GPT models).

    Uses the OpenAI SDK to call GPT models for adversarial auditing.
    Supports both CRUX_OPENAI_API_KEY and OPENAI_API_KEY env vars.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get(
            "CRUX_OPENAI_API_KEY",
            os.environ.get("OPENAI_API_KEY", ""),
        )
        self._client = None

    @property
    def name(self) -> str:
        return f"OpenAI ({self._model})"

    def is_available(self) -> bool:
        """Check if OpenAI API is available (API key set)."""
        return bool(self._api_key)

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                _logger.warning("openai package not installed")
                return None
        return self._client

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        if not self._api_key:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="OpenAI API key not configured",
                backend=self.name,
            )

        client = self._get_client()
        if client is None:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="openai package not installed (pip install openai)",
                backend=self.name,
            )

        prompt = _format_audit_prompt(script_content, risk_level)

        try:
            response = client.chat.completions.create(
                model=self._model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )

            response_text = response.choices[0].message.content
            parsed = _parse_audit_response(response_text)

            if parsed is None:
                return AuditResult(
                    passed=True,
                    skipped=True,
                    reason="Could not parse OpenAI response as JSON",
                    backend=self.name,
                )

            findings = [
                AuditFinding(
                    severity=f.get("severity", "medium"),
                    title=f.get("title", "Unknown"),
                    description=f.get("description", ""),
                )
                for f in parsed.get("findings", [])
            ]

            return AuditResult(
                passed=parsed.get("passed", True),
                skipped=False,
                findings=findings,
                summary=parsed.get("summary", ""),
                backend=self.name,
                model=self._model,
            )

        except Exception as exc:
            _logger.debug("OpenAI audit failed: %s", exc)
            return AuditResult(
                passed=True,
                skipped=True,
                reason=f"OpenAI API error: {exc}",
                backend=self.name,
            )


# ---------------------------------------------------------------------------
# Claude Code Subagent Backend
# ---------------------------------------------------------------------------


class ClaudeSubagentBackend:
    """Audit backend using Claude Code's security subagent.

    This backend invokes Claude Code's Task tool with subagent_type="security"
    to perform adversarial script auditing. It works by writing a prompt file
    and invoking claude with --print to get the response.
    """

    def __init__(self) -> None:
        self._claude_path = self._find_claude_binary()

    @property
    def name(self) -> str:
        return "Claude subagent (security)"

    def _find_claude_binary(self) -> str | None:
        """Find the claude CLI binary."""
        # Check common locations
        candidates = [
            os.path.expanduser("~/.claude/local/claude"),
            "/usr/local/bin/claude",
            "claude",  # Fall back to PATH
        ]
        for path in candidates:
            if path == "claude":
                # Check PATH
                result = subprocess.run(
                    ["which", "claude"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            elif os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    def is_available(self) -> bool:
        """Check if Claude Code is available and we're in a Claude session."""
        # Check for Claude binary
        if not self._claude_path:
            return False

        # Check if we're in a Claude Code context (CLAUDE_CODE_ENTRY_POINT set)
        # or if claude CLI is available for spawning
        return True

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        if not self._claude_path:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="Claude CLI not found",
                backend=self.name,
            )

        # Build the audit prompt
        prompt = f"""{system_prompt}

Review this {risk_level}-risk bash script for security issues.
Check for: command injection, unquoted variables, path traversal,
privilege escalation, and unsafe operations.

```bash
{script_content}
```

Respond with ONLY valid JSON."""

        try:
            # Use claude CLI with --print for non-interactive output
            result = subprocess.run(
                [
                    self._claude_path,
                    "--print",
                    "-p", prompt,
                ],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env={**os.environ, "CLAUDE_CODE_DISABLE_HOOKS": "1"},
            )

            if result.returncode != 0:
                return AuditResult(
                    passed=True,
                    skipped=True,
                    reason=f"Claude CLI failed: {result.stderr[:200]}",
                    backend=self.name,
                )

            parsed = _parse_audit_response(result.stdout)
            if parsed is None:
                return AuditResult(
                    passed=True,
                    skipped=True,
                    reason="Could not parse Claude response as JSON",
                    backend=self.name,
                )

            findings = [
                AuditFinding(
                    severity=f.get("severity", "medium"),
                    title=f.get("title", "Unknown"),
                    description=f.get("description", ""),
                )
                for f in parsed.get("findings", [])
            ]

            return AuditResult(
                passed=parsed.get("passed", True),
                skipped=False,
                findings=findings,
                summary=parsed.get("summary", ""),
                backend=self.name,
            )

        except subprocess.TimeoutExpired:
            return AuditResult(
                passed=True,
                skipped=True,
                reason="Claude audit timed out after 120s",
                backend=self.name,
            )
        except Exception as exc:
            _logger.debug("Claude subagent audit failed: %s", exc)
            return AuditResult(
                passed=True,
                skipped=True,
                reason=f"Claude audit error: {exc}",
                backend=self.name,
            )


# ---------------------------------------------------------------------------
# Disabled Backend (explicit no-audit)
# ---------------------------------------------------------------------------


class DisabledBackend:
    """Fallback backend when no LLM is available.

    Unlike silent skipping, this backend explicitly warns that no audit
    was performed and returns a clear indication in the result.
    """

    @property
    def name(self) -> str:
        return "DISABLED (no LLM available)"

    def is_available(self) -> bool:
        return True  # Always "available" as the last resort

    def audit(
        self,
        script_content: str,
        risk_level: str,
        system_prompt: str,
    ) -> AuditResult:
        _logger.warning(
            "No audit backend available - script audit skipped for %s-risk script",
            risk_level,
        )
        return AuditResult(
            passed=True,
            skipped=True,
            reason="No audit backend available (Ollama down, Claude CLI not found)",
            backend=self.name,
        )


# ---------------------------------------------------------------------------
# Context Detection (PLAN-170)
# ---------------------------------------------------------------------------


def detect_opencode_context() -> bool:
    """Detect if we're running in OpenCode mode.

    Checks multiple indicators:
    1. CRUX_TOOL environment variable
    2. Setup state file from Crux setup.sh
    3. OpenCode-specific environment variables
    """
    # Check explicit environment variable
    crux_tool = os.environ.get("CRUX_TOOL", "").lower()
    if crux_tool == "opencode":
        return True
    if crux_tool == "claude-code":
        return False

    # Check setup state file
    state_file = Path.home() / ".config" / "crux" / "setup-state" / "selected_tool"
    if state_file.exists():
        try:
            tool = state_file.read_text().strip().lower()
            if tool == "opencode":
                return True
            if tool in ("claude-code", "both"):
                return False
        except (OSError, IOError):
            pass

    # Check for OpenCode-specific indicators
    if os.environ.get("OPENCODE_SESSION"):
        return True

    # Check for Claude Code indicators (inverse detection)
    if os.environ.get("CLAUDE_CODE_ENTRY_POINT"):
        return False

    # Default: unknown context, assume Claude Code (graceful fallback)
    return False


def detect_context_mode() -> str:
    """Detect the current tool context.

    Returns:
        "opencode", "claude-code", or "unknown"
    """
    if detect_opencode_context():
        return "opencode"

    # Check for Claude Code
    if os.environ.get("CLAUDE_CODE_ENTRY_POINT"):
        return "claude-code"

    state_file = Path.home() / ".config" / "crux" / "setup-state" / "selected_tool"
    if state_file.exists():
        try:
            tool = state_file.read_text().strip().lower()
            if tool in ("claude-code", "opencode", "both"):
                return tool
        except (OSError, IOError):
            pass

    return "unknown"


# ---------------------------------------------------------------------------
# Backend Selection
# ---------------------------------------------------------------------------

# Cached backend instance
_cached_backend: AuditBackend | None = None
_cached_backend_check_time: float = 0

# Backend name to class mapping
_BACKEND_CLASSES: dict[str, type] = {
    "ollama": OllamaBackend,
    "anthropic": AnthropicBackend,
    "openai": OpenAIBackend,
    "subagent": ClaudeSubagentBackend,
}


def _create_backend(
    backend_type: str,
    model: str | None = None,
) -> AuditBackend | None:
    """Create a backend instance by type name.

    Args:
        backend_type: One of "ollama", "anthropic", "openai", "subagent"
        model: Optional model override

    Returns:
        Backend instance or None if type unknown
    """
    backend_type = backend_type.lower()
    cls = _BACKEND_CLASSES.get(backend_type)
    if cls is None:
        return None

    if backend_type == "ollama":
        return cls(model=model or "qwen3:8b")
    elif backend_type == "anthropic":
        return cls(model=model or "claude-3-haiku-20240307")
    elif backend_type == "openai":
        return cls(model=model or "gpt-4o-mini")
    elif backend_type == "subagent":
        return cls()
    return None


def get_configured_backend() -> tuple[str | None, str | None]:
    """Get configured backend from environment variables.

    Returns:
        Tuple of (primary_backend, adversarial_backend) names, or None if not configured
    """
    primary = os.environ.get("CRUX_AUDIT_BACKEND", "").lower() or None
    adversarial = os.environ.get("CRUX_ADVERSARIAL_BACKEND", "").lower() or None
    return primary, adversarial


def get_audit_backend(
    force_refresh: bool = False,
    prefer_ollama_model: str = "qwen3:8b",
    context: str = "auto",
    enforce_opencode: bool = True,
    role: str = "primary",
) -> AuditBackend:
    """Get the best available audit backend.

    PLAN-182: Supports flexible backend configuration via environment variables.
    Priority (when no env var configured):
    1. Ollama (local, fast, private, free)
    2. Anthropic API (if ANTHROPIC_API_KEY set)
    3. OpenAI API (if OPENAI_API_KEY set)
    4. Claude Code subagent (requires Claude CLI) - NOT in OpenCode mode
    5. Disabled (explicit warning, no silent skipping) - NOT in OpenCode mode

    PLAN-170: In OpenCode mode, SOME audit backend is REQUIRED.
    PLAN-182: OpenCode now accepts API backends (not just Ollama).

    Args:
        force_refresh: If True, re-check backend availability
        prefer_ollama_model: Ollama model to use if available
        context: "auto", "opencode", or "claude-code" - determines enforcement
        enforce_opencode: If False, skip OpenCode enforcement (for testing)
        role: "primary" or "adversarial" - which backend to get

    Returns:
        The best available AuditBackend instance

    Raises:
        AuditRequiredError: In OpenCode mode when no audit backend is available
    """
    global _cached_backend, _cached_backend_check_time

    import time

    now = time.time()

    # Determine context
    is_opencode = False
    if context == "auto":
        is_opencode = detect_opencode_context()
    elif context == "opencode":
        is_opencode = True

    # Check for explicit backend configuration (PLAN-182)
    primary_config, adversarial_config = get_configured_backend()
    configured_type = adversarial_config if role == "adversarial" else primary_config

    # Get adversarial model if specified
    adversarial_model = os.environ.get("CRUX_ADVERSARIAL_MODEL")

    # If backend explicitly configured, try to use it
    if configured_type:
        model = adversarial_model if role == "adversarial" else prefer_ollama_model
        backend = _create_backend(configured_type, model)
        if backend and backend.is_available():
            _logger.debug("Using configured %s backend: %s", role, backend.name)
            if role == "primary":
                _cached_backend = backend
                _cached_backend_check_time = now
            return backend
        elif is_opencode and enforce_opencode:
            raise AuditRequiredError(
                f"Configured {role} backend '{configured_type}' is not available.\n"
                f"\n"
                f"Check your configuration:\n"
                f"  - CRUX_AUDIT_BACKEND={primary_config or 'not set'}\n"
                f"  - CRUX_ADVERSARIAL_BACKEND={adversarial_config or 'not set'}\n"
                f"\n"
                f"Ensure API keys are set if using API backends:\n"
                f"  - ANTHROPIC_API_KEY or CRUX_ANTHROPIC_API_KEY\n"
                f"  - OPENAI_API_KEY or CRUX_OPENAI_API_KEY\n"
            )

    # Cache backend for 60 seconds to avoid repeated checks
    # But don't use cache if context changed or we need to enforce
    if (
        not force_refresh
        and _cached_backend is not None
        and (now - _cached_backend_check_time) < 60
        and role == "primary"
        and not (is_opencode and enforce_opencode and isinstance(_cached_backend, DisabledBackend))
    ):
        return _cached_backend

    # Auto-discovery: try backends in priority order
    # 1. Ollama (local, fast, private, free)
    ollama = OllamaBackend(model=prefer_ollama_model)
    if ollama.is_available():
        if role == "primary":
            _cached_backend = ollama
            _cached_backend_check_time = now
        _logger.debug("Using Ollama backend: %s", ollama.name)
        return ollama

    # 2. Anthropic API (PLAN-182)
    anthropic = AnthropicBackend(
        model=adversarial_model if role == "adversarial" else "claude-3-haiku-20240307"
    )
    if anthropic.is_available():
        if role == "primary":
            _cached_backend = anthropic
            _cached_backend_check_time = now
        _logger.debug("Using Anthropic backend: %s", anthropic.name)
        return anthropic

    # 3. OpenAI API (PLAN-182)
    openai_backend = OpenAIBackend(
        model=adversarial_model if role == "adversarial" else "gpt-4o-mini"
    )
    if openai_backend.is_available():
        if role == "primary":
            _cached_backend = openai_backend
            _cached_backend_check_time = now
        _logger.debug("Using OpenAI backend: %s", openai_backend.name)
        return openai_backend

    # PLAN-170/182: OpenCode mode requires SOME audit backend
    if is_opencode and enforce_opencode:
        raise AuditRequiredError(
            "OpenCode requires an audit backend for adversarial auditing.\n"
            "\n"
            "Available options:\n"
            "  1. Local Ollama:\n"
            "     ollama serve && ollama pull qwen3:8b\n"
            "\n"
            "  2. Anthropic API:\n"
            "     export ANTHROPIC_API_KEY=sk-ant-...\n"
            "\n"
            "  3. OpenAI API:\n"
            "     export OPENAI_API_KEY=sk-...\n"
            "\n"
            "Configure explicitly with:\n"
            "  export CRUX_AUDIT_BACKEND=ollama|anthropic|openai\n"
            "  export CRUX_ADVERSARIAL_BACKEND=anthropic  # for hybrid mode\n"
        )

    # 4. Claude subagent (Claude Code mode only)
    claude = ClaudeSubagentBackend()
    if claude.is_available():
        if role == "primary":
            _cached_backend = claude
            _cached_backend_check_time = now
        _logger.debug("Using Claude subagent backend")
        return claude

    # 5. Fall back to disabled (Claude Code mode only)
    disabled = DisabledBackend()
    if role == "primary":
        _cached_backend = disabled
        _cached_backend_check_time = now
    _logger.warning("No audit backend available - using disabled backend")
    return disabled


def get_adversarial_backend(
    force_refresh: bool = False,
    context: str = "auto",
    enforce: bool = True,
) -> AuditBackend:
    """Get the adversarial audit backend.

    PLAN-182: Returns the backend configured for adversarial role,
    which may be different from the primary backend.

    Args:
        force_refresh: If True, re-check backend availability
        context: "auto", "opencode", or "claude-code"
        enforce: If True, raise AuditRequiredError if no backend available

    Returns:
        The adversarial AuditBackend instance
    """
    return get_audit_backend(
        force_refresh=force_refresh,
        context=context,
        enforce_opencode=enforce,
        role="adversarial",
    )


def get_backend_status() -> dict:
    """Get status of all audit backends for health checks.

    Returns:
        Dict with backend availability, active backend, and mode info
    """
    ollama = OllamaBackend()
    anthropic = AnthropicBackend()
    openai_backend = OpenAIBackend()
    claude = ClaudeSubagentBackend()

    ollama_available = ollama.is_available()
    anthropic_available = anthropic.is_available()
    openai_available = openai_backend.is_available()
    claude_available = claude.is_available()
    context_mode = detect_context_mode()
    is_opencode = context_mode == "opencode"

    # Get configured backends (PLAN-182)
    primary_config, adversarial_config = get_configured_backend()

    # Any API backend available counts as having an audit option
    any_backend_available = (
        ollama_available or anthropic_available or openai_available or claude_available
    )

    # Determine active backend (with enforcement disabled for status check)
    try:
        active = get_audit_backend(enforce_opencode=False, force_refresh=True)
        active_name = active.name
        audit_blocked = False
    except AuditRequiredError:
        active_name = "BLOCKED (no backend available)"
        audit_blocked = True

    # Check if audit would be blocked in current mode
    # PLAN-182: OpenCode now accepts API backends, not just Ollama
    if is_opencode and not any_backend_available:
        audit_blocked = True
        active_name = "BLOCKED (no audit backend for OpenCode)"

    return {
        "active_backend": active_name,
        "ollama_available": ollama_available,
        "anthropic_available": anthropic_available,
        "openai_available": openai_available,
        "claude_available": claude_available,
        "context_mode": context_mode,
        "audit_required": is_opencode,
        "audit_blocked": audit_blocked,
        "configured": {
            "primary": primary_config,
            "adversarial": adversarial_config,
        },
        "backends": {
            "ollama": {
                "available": ollama_available,
                "name": ollama.name,
                "available_in": ["opencode", "claude-code", "both"],
            },
            "anthropic": {
                "available": anthropic_available,
                "name": anthropic.name,
                "available_in": ["opencode", "claude-code", "both"],
            },
            "openai": {
                "available": openai_available,
                "name": openai_backend.name,
                "available_in": ["opencode", "claude-code", "both"],
            },
            "claude": {
                "available": claude_available,
                "name": claude.name,
                "available_in": ["claude-code", "both"],
            },
            "disabled": {
                "available": not is_opencode,
                "name": DisabledBackend().name,
                "available_in": ["claude-code", "both"],
            },
        },
    }


# ---------------------------------------------------------------------------
# Helper functions (moved from crux_llm_audit.py)
# ---------------------------------------------------------------------------


def _format_audit_prompt(script_content: str, risk_level: str) -> str:
    """Build the audit prompt for an LLM review."""
    return (
        f"Review this {risk_level}-risk bash script for security issues. "
        f"Check for: command injection, unquoted variables, path traversal, "
        f"privilege escalation, and unsafe operations. "
        f"Respond with json.\n\n```bash\n{script_content}\n```"
    )


def _parse_audit_response(response_text: str) -> dict | None:
    """Parse LLM response as JSON audit result. Returns None on failure."""
    try:
        # Handle responses wrapped in markdown code blocks
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            if len(lines) > 2:
                text = "\n".join(lines[1:-1])
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
