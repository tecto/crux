"""Crux runtime status and health reporting.

Provides insight into the live state of Crux:
- Session state (mode, tool, working context)
- Hook status (active, events registered)
- Interaction logging (today's count, tool breakdown)
- Correction capture (total, by category)
- Knowledge entries (count, names)
- MCP server registration
- Pending tasks

Used by `crux status` CLI command.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.crux_paths import get_project_paths, get_user_paths
from scripts.lib.crux_session import load_session


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_json_safe(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# get_status — collect all runtime data
# ---------------------------------------------------------------------------

def get_status(project_dir: str, home: str) -> dict:
    """Collect full Crux runtime status."""
    project_paths = get_project_paths(project_dir)
    user_paths = get_user_paths(home)
    crux_dir = str(project_paths.root)

    status: dict = {}

    # Session
    session = load_session(crux_dir)
    status["session"] = {
        "active_mode": session.active_mode,
        "active_tool": session.active_tool,
        "working_on": session.working_on,
        "updated_at": session.updated_at,
        "decisions": len(session.key_decisions),
    }

    # Knowledge
    kb_dir = project_paths.knowledge
    kb_entries: list[str] = []
    if os.path.isdir(kb_dir):
        kb_entries = [p.stem for p in Path(kb_dir).glob("*.md")]
    status["knowledge"] = {
        "project_entries": len(kb_entries),
        "entry_names": sorted(kb_entries),
    }

    # Modes
    modes_dir = user_paths.modes
    mode_names: list[str] = []
    if os.path.isdir(modes_dir):
        mode_names = [p.stem for p in Path(modes_dir).glob("*.md") if p.stem != "_template"]
    status["modes"] = {
        "total": len(mode_names),
        "available": sorted(mode_names),
    }

    # Hooks
    hooks_data = _check_hooks(project_dir)
    status["hooks"] = hooks_data

    # Interactions
    status["interactions"] = _count_today_interactions(project_dir)

    # Corrections
    status["corrections"] = _count_corrections(project_dir)

    # MCP
    status["mcp"] = _check_mcp(project_dir)

    # Pending
    status["pending"] = {
        "count": len(session.pending),
        "items": list(session.pending),
    }

    # Files
    status["files"] = {
        "tracked": len(session.files_touched),
    }

    return status


def _check_hooks(project_dir: str) -> dict:
    """Check if Claude Code hooks are configured."""
    settings_path = os.path.join(project_dir, ".claude", "settings.local.json")
    settings = _load_json_safe(settings_path)

    hooks = settings.get("hooks", {})
    events = [k for k, v in hooks.items() if v]

    return {
        "active": len(events) > 0,
        "events_registered": len(events),
        "events": events,
    }


def _count_today_interactions(project_dir: str) -> dict:
    """Count today's interactions from the log."""
    project_paths = get_project_paths(project_dir)
    log_dir = os.path.join(str(project_paths.root), "analytics", "interactions")
    log_file = os.path.join(log_dir, f"{_today()}.jsonl")

    if not os.path.exists(log_file):
        return {"today": 0, "tool_breakdown": {}}

    tools: Counter = Counter()
    count = 0
    with open(log_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                tools[entry.get("tool_name", "unknown")] += 1
                count += 1
            except json.JSONDecodeError:
                continue

    return {
        "today": count,
        "tool_breakdown": dict(tools.most_common()),
    }


def _count_corrections(project_dir: str) -> dict:
    """Count all corrections."""
    project_paths = get_project_paths(project_dir)
    corr_file = project_paths.corrections_file

    if not os.path.exists(corr_file):
        return {"total": 0, "by_category": {}}

    categories: Counter = Counter()
    total = 0
    with open(corr_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                categories[entry.get("category", "unknown")] += 1
                total += 1
            except json.JSONDecodeError:
                continue

    return {
        "total": total,
        "by_category": dict(categories.most_common()),
    }


def _check_mcp(project_dir: str) -> dict:
    """Check MCP server registration."""
    mcp_path = os.path.join(project_dir, ".claude", "mcp.json")
    mcp_config = _load_json_safe(mcp_path)

    registered = "crux" in mcp_config.get("mcpServers", {})

    result: dict = {"registered": registered}
    if registered:
        # Import to count tools
        try:
            from scripts.lib.crux_mcp_server import mcp as mcp_server
            result["tool_count"] = len(mcp_server._tool_manager._tools)
        except Exception:
            result["tool_count"] = 0
    return result


# ---------------------------------------------------------------------------
# format_status — human-readable output
# ---------------------------------------------------------------------------

def format_status(status: dict) -> str:
    """Format status dict into human-readable output."""
    lines: list[str] = []

    # Session
    s = status["session"]
    lines.append("SESSION")
    lines.append(f"  Mode: {s['active_mode']}")
    lines.append(f"  Tool: {s['active_tool']}")
    if s["working_on"]:
        lines.append(f"  Working on: {s['working_on']}")
    lines.append(f"  Decisions: {s['decisions']}")
    lines.append(f"  Updated: {s['updated_at']}")
    lines.append("")

    # Hooks
    h = status["hooks"]
    hook_label = "ACTIVE" if h["active"] else "INACTIVE"
    lines.append(f"HOOKS: {hook_label}")
    if h["active"]:
        lines.append(f"  Events: {', '.join(h['events'])}")
    lines.append("")

    # Interactions
    i = status["interactions"]
    lines.append(f"INTERACTIONS: {i['today']} today")
    if i["tool_breakdown"]:
        for tool, count in sorted(i["tool_breakdown"].items(), key=lambda x: -x[1]):
            lines.append(f"  {tool}: {count}")
    lines.append("")

    # Corrections
    c = status["corrections"]
    lines.append(f"CORRECTIONS: {c['total']} total")
    if c["by_category"]:
        for cat, count in c["by_category"].items():
            lines.append(f"  {cat}: {count}")
    lines.append("")

    # Knowledge
    k = status["knowledge"]
    lines.append(f"KNOWLEDGE: {k['project_entries']} entries")
    if k["entry_names"]:
        for name in k["entry_names"]:
            lines.append(f"  {name}")
    lines.append("")

    # MCP
    m = status["mcp"]
    mcp_label = f"REGISTERED ({m.get('tool_count', 0)} tools)" if m["registered"] else "NOT REGISTERED"
    lines.append(f"MCP: {mcp_label}")
    lines.append("")

    # Modes
    md = status["modes"]
    lines.append(f"MODES: {md['total']} available")
    lines.append("")

    # Files
    lines.append(f"FILES TRACKED: {status['files']['tracked']}")
    lines.append("")

    # Pending
    p = status["pending"]
    if p["count"] > 0:
        lines.append(f"PENDING: {p['count']} items")
        for item in p["items"]:
            lines.append(f"  - {item}")
    else:
        lines.append("PENDING: none")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# check_health — pass/fail checks
# ---------------------------------------------------------------------------

def check_health(project_dir: str, home: str) -> list[dict]:
    """Run health checks and return pass/fail results."""
    status = get_status(project_dir=project_dir, home=home)
    checks: list[dict] = []

    # Session exists
    checks.append({
        "name": "Session state",
        "passed": bool(status["session"]["active_mode"]),
        "message": f"Mode: {status['session']['active_mode']}, Tool: {status['session']['active_tool']}",
    })

    # Hooks active
    h = status["hooks"]
    checks.append({
        "name": "Hooks active",
        "passed": h["active"],
        "message": f"{h['events_registered']} events registered" if h["active"] else "No hooks configured",
    })

    # Interactions logging
    i = status["interactions"]
    checks.append({
        "name": "Interaction logging",
        "passed": i["today"] > 0,
        "message": f"{i['today']} interactions today" if i["today"] > 0 else "No interactions logged today",
    })

    # Corrections
    c = status["corrections"]
    checks.append({
        "name": "Correction capture",
        "passed": True,  # always passes — 0 corrections is fine
        "message": f"{c['total']} corrections captured" if c["total"] > 0 else "No corrections yet (normal for new sessions)",
    })

    # Knowledge
    k = status["knowledge"]
    checks.append({
        "name": "Knowledge base",
        "passed": k["project_entries"] > 0,
        "message": f"{k['project_entries']} entries" if k["project_entries"] > 0 else "No knowledge entries",
    })

    # MCP
    m = status["mcp"]
    checks.append({
        "name": "MCP server",
        "passed": m["registered"],
        "message": f"Registered with {m.get('tool_count', 0)} tools" if m["registered"] else "Not registered",
    })

    # Modes
    md = status["modes"]
    checks.append({
        "name": "Modes available",
        "passed": md["total"] > 0,
        "message": f"{md['total']} modes" if md["total"] > 0 else "No modes found",
    })

    return checks
