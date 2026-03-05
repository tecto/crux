"""Seamless switching between AI coding tools.

Reads session state from .crux/, syncs configs for the target tool,
and updates the active tool marker.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.lib.crux_paths import get_project_paths
from scripts.lib.crux_session import load_session
from scripts.lib.crux_sync import sync_tool, SyncResult, SUPPORTED_TOOLS


@dataclass
class SwitchResult:
    success: bool
    from_tool: str
    to_tool: str
    items_synced: list[str] = field(default_factory=list)
    error: str | None = None


def switch_tool(
    target_tool: str,
    project_dir: str,
    home: str,
) -> SwitchResult:
    """Switch from the current tool to target_tool.

    1. Read current session state (which tool was active)
    2. Sync configs for the target tool
    3. Update session to mark the new active tool
    """
    if target_tool not in SUPPORTED_TOOLS:
        return SwitchResult(
            success=False,
            from_tool="",
            to_tool=target_tool,
            error=f"Unsupported tool: '{target_tool}'. Supported: {', '.join(SUPPORTED_TOOLS)}",
        )

    project_paths = get_project_paths(project_dir)
    current = load_session(str(project_paths.root))
    from_tool = current.active_tool or ""

    # sync_tool handles the adapter generation AND updates session.active_tool
    sync_result = sync_tool(target_tool, project_dir=project_dir, home=home)

    if not sync_result.success:
        return SwitchResult(
            success=False,
            from_tool=from_tool,
            to_tool=target_tool,
            error=sync_result.error,
        )

    return SwitchResult(
        success=True,
        from_tool=from_tool,
        to_tool=target_tool,
        items_synced=sync_result.items_synced,
    )
