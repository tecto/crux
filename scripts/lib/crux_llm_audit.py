"""LLM-based script auditing for safety pipeline Gates 4-5."""

from __future__ import annotations

import json

from scripts.lib.crux_ollama import generate

DEFAULT_MODEL_8B = "qwen3:8b"
DEFAULT_MODEL_32B = "qwen3:32b"

AUDIT_SYSTEM_PROMPT = (
    "You are a security auditor reviewing bash scripts for vulnerabilities. "
    "Respond with ONLY valid JSON in this format: "
    '{"passed": true/false, "findings": [{"severity": "high|medium|low", '
    '"title": "...", "description": "..."}], "summary": "..."}'
)


def format_audit_prompt(script_content: str, risk_level: str) -> str:
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
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def audit_script_8b(
    script_content: str,
    risk_level: str,
    endpoint: str | None = None,
    model: str | None = None,
) -> dict:
    """Gate 4: Adversarial audit using a small (8B) model."""
    model = model or DEFAULT_MODEL_8B
    prompt = format_audit_prompt(script_content, risk_level)
    kwargs: dict = {"model": model, "prompt": prompt, "system": AUDIT_SYSTEM_PROMPT}
    if endpoint:
        kwargs["endpoint"] = endpoint

    result = generate(**kwargs)

    if not result["success"]:
        return {
            "gate": "audit_8b",
            "passed": True,
            "skipped": True,
            "reason": "Ollama unavailable — skipping 8B audit",
            "findings": [],
        }

    parsed = _parse_audit_response(result["response"])
    if parsed is None:
        return {
            "gate": "audit_8b",
            "passed": True,
            "skipped": True,
            "reason": "Could not parse LLM response as JSON",
            "findings": [],
        }

    return {
        "gate": "audit_8b",
        "passed": parsed.get("passed", True),
        "skipped": False,
        "findings": parsed.get("findings", []),
        "summary": parsed.get("summary", ""),
        "model": model,
    }


def audit_script_32b(
    script_content: str,
    risk_level: str,
    endpoint: str | None = None,
    model: str | None = None,
) -> dict:
    """Gate 5: Second-opinion audit using a large (32B) model. High-risk only."""
    if risk_level != "high":
        return {
            "gate": "audit_32b",
            "passed": True,
            "skipped": True,
            "reason": "Not high-risk — 32B audit only runs for high-risk scripts",
            "findings": [],
        }

    model = model or DEFAULT_MODEL_32B
    prompt = format_audit_prompt(script_content, risk_level)
    kwargs: dict = {"model": model, "prompt": prompt, "system": AUDIT_SYSTEM_PROMPT}
    if endpoint:
        kwargs["endpoint"] = endpoint

    result = generate(**kwargs)

    if not result["success"]:
        return {
            "gate": "audit_32b",
            "passed": True,
            "skipped": True,
            "reason": "Ollama unavailable — skipping 32B audit",
            "findings": [],
        }

    parsed = _parse_audit_response(result["response"])
    if parsed is None:
        return {
            "gate": "audit_32b",
            "passed": True,
            "skipped": True,
            "reason": "Could not parse LLM response as JSON",
            "findings": [],
        }

    return {
        "gate": "audit_32b",
        "passed": parsed.get("passed", True),
        "skipped": False,
        "findings": parsed.get("findings", []),
        "summary": parsed.get("summary", ""),
        "model": model,
    }
