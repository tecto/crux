"""Generate tool-specific configs from .crux/ — the adapter layer.

Each tool (OpenCode, Claude Code, Cursor, etc.) has its own config format.
This module reads from .crux/ (source of truth) and generates the right
configs for each tool.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from scripts.lib.crux_paths import get_project_paths, get_user_paths
from scripts.lib.crux_session import load_session, read_handoff, update_session

SUPPORTED_TOOLS = ("opencode", "claude-code")

# Mode metadata for Claude Code agent frontmatter
_MODE_META = {
    "build-py": {"description": "Python development specialist", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "build-ex": {"description": "Elixir/Phoenix/Ash specialist", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "plan": {"description": "Software architecture planning", "tools": "Read, Grep, Glob", "permissionMode": "plan"},
    "infra-architect": {"description": "Infrastructure and deployment planning", "tools": "Read, Grep, Glob", "permissionMode": "plan"},
    "review": {"description": "Code review specialist", "tools": "Read, Grep, Glob", "permissionMode": "plan"},
    "debug": {"description": "Root cause analysis and debugging", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "explain": {"description": "Teaching and mentoring", "tools": "Read, Grep, Glob", "permissionMode": "plan"},
    "analyst": {"description": "Data analysis specialist", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "writer": {"description": "Professional technical writing", "tools": "Read, Write, Grep, Glob"},
    "psych": {"description": "ACT/Attachment therapeutic support", "tools": "Read, Grep, Glob", "permissionMode": "plan"},
    "legal": {"description": "Legal research and analysis", "tools": "Read, Write, Grep, Glob"},
    "strategist": {"description": "First principles strategic analysis", "tools": "Read, Grep, Glob"},
    "ai-infra": {"description": "AI/LLM infrastructure management", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "mac": {"description": "macOS system operations", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
    "docker": {"description": "Container and Linux operations", "tools": "Read, Write, Edit, Bash, Grep, Glob"},
}


@dataclass
class SyncResult:
    success: bool
    tool: str
    items_synced: list[str] = field(default_factory=list)
    error: str | None = None


def _safe_symlink(source: str, target: str) -> None:
    """Create a symlink, removing any existing link/file at target."""
    if os.path.islink(target):
        os.remove(target)
    elif os.path.exists(target):
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
    os.symlink(source, target)


def _safe_write(path: str, content: str) -> None:
    """Write content to a file, creating parent directories."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def sync_opencode(project_dir: str, home: str) -> SyncResult:
    """Generate ~/.config/opencode/ configs from .crux/."""
    user_paths = get_user_paths(home)
    config_dir = os.path.join(home, ".config", "opencode")
    os.makedirs(config_dir, exist_ok=True)
    items: list[str] = []

    # Symlink modes
    modes_source = user_paths.modes
    if os.path.isdir(modes_source):
        _safe_symlink(modes_source, os.path.join(config_dir, "modes"))
        items.append("modes")

    # Symlink user-level knowledge
    know_source = user_paths.knowledge
    if os.path.isdir(know_source):
        _safe_symlink(know_source, os.path.join(config_dir, "knowledge"))
        items.append("knowledge")

    return SyncResult(success=True, tool="opencode", items_synced=items)


def sync_claude_code(project_dir: str, home: str) -> SyncResult:
    """Generate .claude/ directory from .crux/ data."""
    user_paths = get_user_paths(home)
    project_paths = get_project_paths(project_dir)
    claude_dir = os.path.join(project_dir, ".claude")
    items: list[str] = []

    # Create agents from mode definitions
    agents_dir = os.path.join(claude_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    modes_dir = user_paths.modes
    if os.path.isdir(modes_dir):
        for mode_file in Path(modes_dir).glob("*.md"):
            mode_name = mode_file.stem
            body = mode_file.read_text().strip()
            meta = _MODE_META.get(mode_name, {"description": f"{mode_name} specialist", "tools": "Read, Grep, Glob"})

            frontmatter = f"---\nname: {mode_name}\ndescription: {meta['description']}\ntools: {meta['tools']}\n"
            if "permissionMode" in meta:
                frontmatter += f"permissionMode: {meta['permissionMode']}\n"
            frontmatter += "---\n\n"

            agent_path = os.path.join(agents_dir, f"{mode_name}.md")
            _safe_write(agent_path, frontmatter + body)
            items.append(f"agent:{mode_name}")

    # Create rules from knowledge entries
    rules_dir = os.path.join(claude_dir, "rules")
    os.makedirs(rules_dir, exist_ok=True)

    for knowledge_dir in [project_paths.knowledge, user_paths.knowledge_shared]:
        if os.path.isdir(knowledge_dir):
            for md_file in Path(knowledge_dir).glob("*.md"):
                rule_path = os.path.join(rules_dir, md_file.name)
                _safe_write(rule_path, md_file.read_text())
                items.append(f"rule:{md_file.stem}")

    # Create crux-context.md with session state and handoff
    session = load_session(str(project_paths.root))
    handoff = read_handoff(str(project_paths.root))

    context_lines = ["# Crux Session Context\n"]
    context_lines.append(f"**Active mode:** {session.active_mode}")
    if session.working_on:
        context_lines.append(f"**Working on:** {session.working_on}")
    if session.key_decisions:
        context_lines.append("\n**Key decisions:**")
        for d in session.key_decisions:
            context_lines.append(f"- {d}")
    if session.files_touched:
        context_lines.append("\n**Files touched:**")
        for f in session.files_touched:
            context_lines.append(f"- {f}")
    if session.pending:
        context_lines.append("\n**Pending:**")
        for p in session.pending:
            context_lines.append(f"- {p}")
    if handoff:
        context_lines.append(f"\n**Handoff context:**\n{handoff}")

    context_path = os.path.join(claude_dir, "crux-context.md")
    _safe_write(context_path, "\n".join(context_lines) + "\n")
    items.append("crux-context")

    return SyncResult(success=True, tool="claude-code", items_synced=items)


def sync_tool(
    tool_name: str,
    project_dir: str,
    home: str,
) -> SyncResult:
    """Dispatch sync to the appropriate adapter and update session state."""
    if tool_name not in SUPPORTED_TOOLS:
        return SyncResult(
            success=False,
            tool=tool_name,
            error=f"Unsupported tool: '{tool_name}'. Supported: {', '.join(SUPPORTED_TOOLS)}",
        )

    project_paths = get_project_paths(project_dir)

    if tool_name == "opencode":
        result = sync_opencode(project_dir=project_dir, home=home)
    elif tool_name == "claude-code":
        result = sync_claude_code(project_dir=project_dir, home=home)
    else:  # pragma: no cover — guarded by earlier SUPPORTED_TOOLS check
        return SyncResult(success=False, tool=tool_name, error=f"Unsupported tool: '{tool_name}'")

    # Update session to reflect the active tool
    if result.success:
        update_session(project_crux_dir=str(project_paths.root), active_tool=tool_name)

    return result
