"""Initialize .crux/ directory structures for project and user scopes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from scripts.lib.crux_paths import get_project_paths, get_user_paths

ALL_MODES = [
    "build-py", "build-ex", "plan", "infra-architect", "review",
    "debug", "explain", "analyst", "writer", "psych",
    "legal", "strategist", "ai-infra", "mac", "docker",
]

DEFAULT_PROJECT_CONFIG = {
    "active_mode": "build-py",
    "active_tool": "",
}

DEFAULT_USER_CONFIG = {
    "default_mode": "build-py",
    "digest_cadence": "daily",
}

GITIGNORE_CONTENT = """\
# Crux: ephemeral data (not tracked)
sessions/
corrections/
scripts/session/
scripts/archive/
bip/state.json
bip/history.jsonl
bip/drafts/
bip/config.json
bip/typefully.key

# Crux: tracked data (explicitly allowed)
!knowledge/
!scripts/lib/
!scripts/templates/
!project.json
!context/
!.gitignore
"""


@dataclass
class InitResult:
    success: bool
    root: str
    dirs_created: list[str] = field(default_factory=list)
    error: str | None = None


def init_project(project_dir: str | None = None) -> InitResult:
    """Create .crux/ directory structure in a project."""
    paths = get_project_paths(project_dir)
    dirs_created: list[str] = []

    dirs = [
        paths.knowledge,
        paths.knowledge_by_mode,
        paths.corrections,
        paths.sessions,
        paths.sessions_history,
        paths.scripts,
        paths.scripts_lib,
        paths.scripts_session,
        paths.scripts_archive,
        paths.scripts_templates,
        paths.context,
        paths.models,
        paths.bip,
        paths.bip_drafts,
    ]

    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            dirs_created.append(d)

    # Write project.json only if it doesn't exist
    if not os.path.exists(paths.config_file):
        with open(paths.config_file, "w") as f:
            json.dump(DEFAULT_PROJECT_CONFIG, f, indent=2)

    # Write .gitignore only if it doesn't exist
    gitignore = os.path.join(paths.root, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write(GITIGNORE_CONTENT)

    return InitResult(success=True, root=paths.root, dirs_created=dirs_created)


def init_user(home: str | None = None) -> InitResult:
    """Create ~/.crux/ directory structure."""
    paths = get_user_paths(home)
    dirs_created: list[str] = []

    dirs = [
        paths.knowledge,
        paths.knowledge_shared,
        paths.knowledge_by_mode,
        paths.modes,
        paths.corrections,
        paths.analytics,
        paths.analytics_digests,
        paths.templates,
        paths.scripts_lib,
        paths.models,
        paths.adapters,
    ]

    # Create per-mode knowledge directories
    for mode in ALL_MODES:
        dirs.append(os.path.join(paths.knowledge_by_mode, mode))

    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            dirs_created.append(d)

    # Write config.json only if it doesn't exist
    if not os.path.exists(paths.config_file):
        with open(paths.config_file, "w") as f:
            json.dump(DEFAULT_USER_CONFIG, f, indent=2)

    return InitResult(success=True, root=paths.root, dirs_created=dirs_created)
