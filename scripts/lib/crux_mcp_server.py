"""Crux MCP Server — universal integration layer for AI coding tools.

Exposes Crux capabilities (knowledge, sessions, modes, corrections, etc.)
via the Model Context Protocol. Any MCP-compatible tool (Claude Code, OpenCode,
Cursor, etc.) can connect to this server.

Run: python -m scripts.lib.crux_mcp_server
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from scripts.lib.crux_mcp_handlers import (
    handle_lookup_knowledge,
    handle_get_session_state,
    handle_update_session,
    handle_write_handoff,
    handle_read_handoff,
    handle_get_digest,
    handle_get_mode_prompt,
    handle_validate_script,
    handle_promote_knowledge,
    handle_get_project_context,
    handle_switch_tool,
    handle_list_modes,
    handle_log_correction,
)

mcp = FastMCP("crux", instructions="Crux AI operating system — knowledge, sessions, modes, and tool switching.")


def _home() -> str:
    return os.environ.get("CRUX_HOME", os.environ.get("HOME", ""))


def _project() -> str:
    return os.environ.get("CRUX_PROJECT", os.getcwd())


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def lookup_knowledge(query: str, mode: str | None = None) -> dict:
    """Search knowledge entries across project and user scopes.

    Args:
        query: Search term to match against knowledge entry names and content.
        mode: Optional mode name to include mode-scoped knowledge.
    """
    return handle_lookup_knowledge(query=query, mode=mode, project_dir=_project(), home=_home())


@mcp.tool()
def get_session_state() -> dict:
    """Get the current Crux session state (active mode, tool, working context)."""
    return handle_get_session_state(project_dir=_project())


@mcp.tool()
def update_session(
    active_mode: str | None = None,
    active_tool: str | None = None,
    working_on: str | None = None,
    add_decision: str | None = None,
    add_file: str | None = None,
    add_pending: str | None = None,
) -> dict:
    """Update the current session state.

    Args:
        active_mode: Switch to a different mode.
        active_tool: Update the active tool name.
        working_on: Describe what you're currently working on.
        add_decision: Add a key decision to the session log.
        add_file: Add a file to the list of touched files.
        add_pending: Add a pending task.
    """
    return handle_update_session(
        project_dir=_project(),
        active_mode=active_mode,
        active_tool=active_tool,
        working_on=working_on,
        add_decision=add_decision,
        add_file=add_file,
        add_pending=add_pending,
    )


@mcp.tool()
def write_handoff(content: str) -> dict:
    """Write handoff context for the next mode or tool switch.

    Args:
        content: The handoff context to persist.
    """
    return handle_write_handoff(content=content, project_dir=_project())


@mcp.tool()
def read_handoff() -> dict:
    """Read handoff context left by a previous mode or tool."""
    return handle_read_handoff(project_dir=_project())


@mcp.tool()
def get_digest(date: str | None = None) -> dict:
    """Retrieve a daily digest.

    Args:
        date: Date in YYYY-MM-DD format. Omit for the latest digest.
    """
    return handle_get_digest(home=_home(), date=date)


@mcp.tool()
def get_mode_prompt(mode: str) -> dict:
    """Get the full prompt text for a specific mode.

    Args:
        mode: The mode name (e.g., 'build-py', 'debug', 'plan').
    """
    return handle_get_mode_prompt(mode=mode, home=_home())


@mcp.tool()
def list_modes() -> dict:
    """List all available Crux modes with descriptions."""
    return handle_list_modes(home=_home())


@mcp.tool()
def validate_script(content: str) -> dict:
    """Validate a script against Crux safety conventions.

    Args:
        content: The full script content to validate.
    """
    return handle_validate_script(content=content)


@mcp.tool()
def promote_knowledge(entry_name: str) -> dict:
    """Promote a knowledge entry from project scope to user scope.

    Args:
        entry_name: The knowledge entry name (without .md extension).
    """
    return handle_promote_knowledge(entry_name=entry_name, project_dir=_project(), home=_home())


@mcp.tool()
def get_project_context() -> dict:
    """Read the PROJECT.md context file for the current project."""
    return handle_get_project_context(project_dir=_project())


@mcp.tool()
def switch_tool_to(target_tool: str) -> dict:
    """Switch to a different AI coding tool, syncing all configs.

    Args:
        target_tool: The tool to switch to (e.g., 'opencode', 'claude-code').
    """
    return handle_switch_tool(target_tool=target_tool, project_dir=_project(), home=_home())


@mcp.tool()
def log_correction(
    original: str,
    corrected: str,
    category: str,
    mode: str,
) -> dict:
    """Log a correction for continuous learning.

    Args:
        original: What the AI originally did/said.
        corrected: What the correct action/response should have been.
        category: Correction category (e.g., 'code-pattern', 'style', 'logic').
        mode: The mode that was active when the correction occurred.
    """
    return handle_log_correction(
        original=original,
        corrected=corrected,
        category=category,
        mode=mode,
        project_dir=_project(),
    )


async def run():  # pragma: no cover — starts blocking stdio server
    """Run the MCP server on stdio transport."""
    await mcp.run_stdio_async()


if __name__ == "__main__":  # pragma: no cover
    import asyncio
    asyncio.run(run())
