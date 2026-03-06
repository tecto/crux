"""Handler functions for Crux MCP server tools.

Each handle_* function contains pure logic — no MCP decorators.
The MCP server module wraps these with @mcp.tool().
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.crux_paths import get_project_paths, get_user_paths, CruxPaths
from scripts.lib.crux_session import (
    load_session,
    save_session,
    update_session,
    write_handoff as _write_handoff,
    read_handoff as _read_handoff,
)
from scripts.lib.crux_switch import switch_tool
from scripts.lib.crux_pipeline_config import (
    PipelineConfig,
    load_pipeline_config,
    save_pipeline_config,
    gates_for_mode,
)
from scripts.lib.crux_tdd_gate import (
    start_tdd_gate,
    record_red_phase,
    record_green_phase,
    check_tdd_gate_status,
)
from scripts.lib.crux_security_audit import (
    SecurityFinding,
    start_audit,
    record_findings,
    check_convergence,
    get_blocking_findings,
    resolve_finding,
    audit_summary,
)
from scripts.lib.crux_design_validation import (
    check_contrast_ratio,
    validate_touch_targets,
    start_validation,
    record_validation_findings,
    validation_summary,
    ValidationFinding,
)


# ---------------------------------------------------------------------------
# lookup_knowledge
# ---------------------------------------------------------------------------

def handle_lookup_knowledge(
    query: str,
    project_dir: str,
    home: str,
    mode: str | None = None,
) -> dict:
    """Search knowledge entries across project and user scopes."""
    crux = CruxPaths(project_dir=project_dir, home=home)
    search_dirs = crux.knowledge_search_dirs(mode)

    results: list[dict] = []
    query_lower = query.lower()

    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for md_file in Path(d).glob("*.md"):
            content = md_file.read_text()
            name = md_file.stem
            if query_lower in content.lower() or query_lower in name.lower():
                excerpt = content[:300].strip()
                results.append({
                    "name": name,
                    "excerpt": excerpt,
                    "source": _classify_source(str(md_file), project_dir, home),
                    "path": str(md_file),
                })

    # Deduplicate by name (first occurrence wins — most specific scope)
    seen: set[str] = set()
    unique: list[dict] = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)

    return {
        "total_found": len(unique),
        "results": unique,
    }


def _classify_source(path: str, project_dir: str, home: str) -> str:
    """Classify a knowledge file as 'project' or 'user'."""
    project_crux = os.path.join(project_dir, ".crux")
    if path.startswith(project_crux):
        return "project"
    return "user"


# ---------------------------------------------------------------------------
# get_session_state / update_session
# ---------------------------------------------------------------------------

def handle_get_session_state(project_dir: str) -> dict:
    """Return current session state as a dict."""
    project_paths = get_project_paths(project_dir)
    state = load_session(str(project_paths.root))
    return state.to_dict()


def handle_update_session(
    project_dir: str,
    active_mode: str | None = None,
    active_tool: str | None = None,
    working_on: str | None = None,
    add_decision: str | None = None,
    add_file: str | None = None,
    add_pending: str | None = None,
) -> dict:
    """Update session state and return the new state."""
    project_paths = get_project_paths(project_dir)
    state = update_session(
        project_crux_dir=str(project_paths.root),
        active_mode=active_mode,
        active_tool=active_tool,
        working_on=working_on,
        add_decision=add_decision,
        add_file=add_file,
        add_pending=add_pending,
    )
    return state.to_dict()


# ---------------------------------------------------------------------------
# Handoff
# ---------------------------------------------------------------------------

def handle_write_handoff(content: str, project_dir: str) -> dict:
    """Write handoff context for the next mode/tool."""
    project_paths = get_project_paths(project_dir)
    _write_handoff(content, project_crux_dir=str(project_paths.root))
    return {"written": True}


def handle_read_handoff(project_dir: str) -> dict:
    """Read handoff context."""
    project_paths = get_project_paths(project_dir)
    content = _read_handoff(project_crux_dir=str(project_paths.root))
    return {
        "exists": content is not None,
        "content": content,
    }


# ---------------------------------------------------------------------------
# get_digest
# ---------------------------------------------------------------------------

def handle_get_digest(home: str, date: str | None = None) -> dict:
    """Retrieve a daily digest by date, or the latest one."""
    user_paths = get_user_paths(home)
    digest_dir = user_paths.analytics_digests

    if not os.path.isdir(digest_dir):
        return {"found": False, "content": None}

    if date:
        digest_file = os.path.join(digest_dir, f"{date}.md")
        if os.path.exists(digest_file):
            return {"found": True, "content": Path(digest_file).read_text()}
        return {"found": False, "content": None}

    # Find latest digest
    files = sorted(Path(digest_dir).glob("*.md"))
    if not files:
        return {"found": False, "content": None}

    latest = files[-1]
    return {"found": True, "content": latest.read_text()}


# ---------------------------------------------------------------------------
# get_mode_prompt / list_modes
# ---------------------------------------------------------------------------

def handle_get_mode_prompt(mode: str, home: str) -> dict:
    """Get the prompt for a specific mode."""
    user_paths = get_user_paths(home)
    mode_file = os.path.join(user_paths.modes, f"{mode}.md")

    if not os.path.exists(mode_file):
        return {"found": False, "mode": mode, "prompt": None}

    return {
        "found": True,
        "mode": mode,
        "prompt": Path(mode_file).read_text(),
    }


def handle_list_modes(home: str) -> dict:
    """List all available modes with excerpts."""
    user_paths = get_user_paths(home)
    modes_dir = user_paths.modes

    if not os.path.isdir(modes_dir):
        return {"modes": []}

    modes: list[dict] = []
    for md_file in sorted(Path(modes_dir).glob("*.md")):
        content = md_file.read_text().strip()
        modes.append({
            "name": md_file.stem,
            "excerpt": content[:200],
        })

    return {"modes": modes}


# ---------------------------------------------------------------------------
# validate_script
# ---------------------------------------------------------------------------

_REQUIRED_HEADER_FIELDS = {"Name", "Risk", "Created", "Status", "Description"}


def handle_validate_script(content: str) -> dict:
    """Validate a script against Crux conventions."""
    errors: list[str] = []

    # Shebang
    if not content.startswith("#!/"):
        errors.append("Missing shebang line (e.g., #!/bin/bash)")

    # Header block
    if "################################" not in content:
        errors.append("Missing header block")
    else:
        for field_name in _REQUIRED_HEADER_FIELDS:
            pattern = rf"#\s*{field_name}:"
            if not re.search(pattern, content):
                errors.append(f"Missing header field: {field_name}")

    # set -euo pipefail
    if "set -euo pipefail" not in content:
        errors.append("Missing 'set -euo pipefail'")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# promote_knowledge
# ---------------------------------------------------------------------------

def handle_promote_knowledge(
    entry_name: str,
    project_dir: str,
    home: str,
) -> dict:
    """Promote a knowledge entry from project scope to user scope."""
    project_paths = get_project_paths(project_dir)
    user_paths = get_user_paths(home)

    # Search in project knowledge
    source = os.path.join(project_paths.knowledge, f"{entry_name}.md")
    if not os.path.exists(source):
        return {"promoted": False, "error": f"Entry '{entry_name}' not found in project knowledge"}

    dest = os.path.join(user_paths.knowledge, f"{entry_name}.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(source, dest)

    return {"promoted": True, "from": source, "to": dest}


# ---------------------------------------------------------------------------
# get_project_context
# ---------------------------------------------------------------------------

def handle_get_project_context(project_dir: str) -> dict:
    """Read PROJECT.md from the project context directory."""
    project_paths = get_project_paths(project_dir)
    project_md = project_paths.project_md

    if not os.path.exists(project_md):
        return {"found": False, "content": None}

    return {"found": True, "content": Path(project_md).read_text()}


# ---------------------------------------------------------------------------
# switch_tool
# ---------------------------------------------------------------------------

def handle_switch_tool(
    target_tool: str,
    project_dir: str,
    home: str,
) -> dict:
    """Switch to a different AI coding tool."""
    result = switch_tool(
        target_tool=target_tool,
        project_dir=project_dir,
        home=home,
    )
    resp: dict = {
        "success": result.success,
        "from_tool": result.from_tool,
        "to_tool": result.to_tool,
    }
    if result.error:
        resp["error"] = result.error
    if result.items_synced:
        resp["items_synced"] = result.items_synced
    return resp


# ---------------------------------------------------------------------------
# log_correction
# ---------------------------------------------------------------------------

def handle_log_correction(
    original: str,
    corrected: str,
    category: str,
    mode: str,
    project_dir: str,
) -> dict:
    """Log a correction to the project corrections JSONL file."""
    project_paths = get_project_paths(project_dir)
    corrections_dir = project_paths.corrections
    os.makedirs(corrections_dir, exist_ok=True)

    corrections_file = project_paths.corrections_file
    entry = {
        "original": original,
        "corrected": corrected,
        "category": category,
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(corrections_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {"logged": True}


# ---------------------------------------------------------------------------
# Pipeline config
# ---------------------------------------------------------------------------

def handle_get_pipeline_config(project_dir: str) -> dict:
    """Load and return the pipeline configuration."""
    config_path = os.path.join(project_dir, ".crux", "pipeline.json")
    cfg = load_pipeline_config(config_path)
    return cfg.to_dict()


def handle_get_active_gates(mode: str, risk_level: str, project_dir: str) -> dict:
    """Get the active gates for a mode at a given risk level."""
    config_path = os.path.join(project_dir, ".crux", "pipeline.json")
    cfg = load_pipeline_config(config_path)
    gates = gates_for_mode(mode, risk_level, cfg)
    return {"mode": mode, "risk_level": risk_level, "active_gates": gates}


# ---------------------------------------------------------------------------
# TDD gate
# ---------------------------------------------------------------------------

def handle_start_tdd_gate(
    mode: str,
    feature: str,
    components: list[str],
    edge_cases: list[str],
    project_dir: str,
) -> dict:
    """Start the TDD enforcement gate for a feature."""
    config_path = os.path.join(project_dir, ".crux", "pipeline.json")
    cfg = load_pipeline_config(config_path)
    gate_file = os.path.join(project_dir, ".crux", "gates", "tdd.json")
    os.makedirs(os.path.dirname(gate_file), exist_ok=True)

    state = start_tdd_gate(
        mode=mode,
        enforcement_level=cfg.tdd.level,
        feature=feature,
        components=components,
        edge_cases=edge_cases,
        gate_file=gate_file,
    )
    return state.to_dict()


def handle_check_tdd_status(project_dir: str) -> dict:
    """Check the current status of the TDD gate."""
    gate_file = os.path.join(project_dir, ".crux", "gates", "tdd.json")
    return check_tdd_gate_status(gate_file)


# ---------------------------------------------------------------------------
# Security audit
# ---------------------------------------------------------------------------

def handle_start_security_audit(project_dir: str) -> dict:
    """Start a security audit loop."""
    config_path = os.path.join(project_dir, ".crux", "pipeline.json")
    cfg = load_pipeline_config(config_path)
    audit_file = os.path.join(project_dir, ".crux", "gates", "security.json")
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)

    state = start_audit(
        max_iterations=cfg.security_audit.max_iterations,
        categories=cfg.security_audit.categories,
        audit_file=audit_file,
    )
    return state.to_dict()


def handle_security_audit_summary(project_dir: str) -> dict:
    """Get the security audit summary."""
    audit_file = os.path.join(project_dir, ".crux", "gates", "security.json")
    return audit_summary(audit_file)


# ---------------------------------------------------------------------------
# Design validation
# ---------------------------------------------------------------------------

def handle_start_design_validation(project_dir: str) -> dict:
    """Start the design validation gate."""
    config_path = os.path.join(project_dir, ".crux", "pipeline.json")
    cfg = load_pipeline_config(config_path)
    val_file = os.path.join(project_dir, ".crux", "gates", "design.json")
    os.makedirs(os.path.dirname(val_file), exist_ok=True)

    state = start_validation(
        wcag_level=cfg.design_validation.wcag_level,
        check_brand=cfg.design_validation.check_brand_consistency,
        check_handoff=cfg.design_validation.check_handoff_completeness,
        validation_file=val_file,
    )
    return state.to_dict()


def handle_design_validation_summary(project_dir: str) -> dict:
    """Get the design validation summary."""
    val_file = os.path.join(project_dir, ".crux", "gates", "design.json")
    return validation_summary(val_file)


def handle_check_contrast(foreground: str, background: str) -> dict:
    """Check contrast ratio between two colors."""
    result = check_contrast_ratio(foreground, background)
    return result.to_dict()


# ---------------------------------------------------------------------------
# log_interaction — full-text conversation logging for MCP clients
# ---------------------------------------------------------------------------

def handle_log_interaction(
    role: str,
    content: str,
    project_dir: str,
    metadata: dict | None = None,
) -> dict:
    """Log a conversation message to the conversations JSONL file.

    Used by OpenCode (and other MCP clients) to log full-text messages
    for analysis and continuous improvement.
    """
    if not content.strip():
        return {"logged": False, "error": "Empty content"}
    if role not in ("user", "assistant"):
        return {"logged": False, "error": f"Invalid role: '{role}'. Must be 'user' or 'assistant'"}

    project_paths = get_project_paths(project_dir)
    state = load_session(str(project_paths.root))

    log_dir = os.path.join(str(project_paths.root), "analytics", "conversations")
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today}.jsonl")

    entry: dict = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "role": role,
        "content": content,
        "mode": state.active_mode,
        "tool": state.active_tool,
    }
    if metadata:
        entry["metadata"] = metadata

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return {"logged": True}


# ---------------------------------------------------------------------------
# restore_context — rebuild full session context after restart
# ---------------------------------------------------------------------------

def handle_restore_context(project_dir: str, home: str) -> dict:
    """Rebuild full session context for injection after a restart.

    Returns a formatted context string containing:
    - Active mode and its prompt
    - Working on description
    - Key decisions
    - Pending tasks
    - Files touched
    - Handoff context
    - Context summary
    """
    project_paths = get_project_paths(project_dir)
    user_paths = get_user_paths(home)
    state = load_session(str(project_paths.root))
    handoff = _read_handoff(str(project_paths.root))

    parts: list[str] = []

    # Mode prompt
    mode_file = os.path.join(user_paths.modes, f"{state.active_mode}.md")
    if os.path.exists(mode_file):
        prompt = Path(mode_file).read_text().strip()
        parts.append(f"## Active Mode: {state.active_mode}\n{prompt}")
    else:
        parts.append(f"## Active Mode: {state.active_mode}")

    # Session state
    parts.append(f"\n## Session State")
    parts.append(f"- Mode: {state.active_mode}")
    parts.append(f"- Tool: {state.active_tool or 'not set'}")
    if state.working_on:
        parts.append(f"- Working on: {state.working_on}")

    # Context summary
    if state.context_summary:
        parts.append(f"\n## Context Summary\n{state.context_summary}")

    # Key decisions
    if state.key_decisions:
        parts.append(f"\n## Key Decisions ({len(state.key_decisions)} total)")
        for d in state.key_decisions:
            parts.append(f"- {d}")

    # Pending tasks
    if state.pending:
        parts.append(f"\n## Pending Tasks")
        for task in state.pending:
            parts.append(f"- {task}")

    # Files touched
    if state.files_touched:
        parts.append(f"\n## Files Touched ({len(state.files_touched)} files)")
        for f in state.files_touched:
            parts.append(f"- {f}")

    # Handoff
    if handoff:
        parts.append(f"\n## Handoff Context\n{handoff}")

    return {"context": "\n".join(parts)}
