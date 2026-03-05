"""Generate and maintain PROJECT.md from directory state and project metadata."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProjectInfo:
    name: str = ""
    tech_stack: list[str] = field(default_factory=list)
    directory_tree: str = ""
    key_files: list[str] = field(default_factory=list)
    recent_changes: list[str] = field(default_factory=list)


def detect_tech_stack(project_dir: str) -> list[str]:
    """Detect technologies from project files."""
    stack = []
    indicators = {
        "pyproject.toml": "Python",
        "setup.py": "Python",
        "requirements.txt": "Python",
        "Pipfile": "Python",
        "package.json": "Node.js",
        "tsconfig.json": "TypeScript",
        "mix.exs": "Elixir",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "Gemfile": "Ruby",
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        "docker-compose.yaml": "Docker Compose",
    }
    for filename, tech in indicators.items():
        if os.path.exists(os.path.join(project_dir, filename)):
            if tech not in stack:
                stack.append(tech)
    return stack


def generate_directory_tree(project_dir: str, max_depth: int = 3) -> str:
    """Generate a directory tree string, excluding common noise dirs."""
    exclude = {
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        ".mypy_cache", ".pytest_cache", ".tox", "dist", "build",
        ".egg-info", ".eggs", ".cache",
    }
    lines = []

    def _walk(dir_path: str, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e)) and e not in exclude and not e.startswith(".")]
        files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and not e.startswith(".")]

        for i, d in enumerate(dirs):
            connector = "└── " if i == len(dirs) - 1 and not files else "├── "
            lines.append(f"{prefix}{connector}{d}/")
            extension = "    " if i == len(dirs) - 1 and not files else "│   "
            _walk(os.path.join(dir_path, d), prefix + extension, depth + 1)

        for i, f in enumerate(files):
            connector = "└── " if i == len(files) - 1 else "├── "
            lines.append(f"{prefix}{connector}{f}")

    _walk(project_dir, "", 0)
    return "\n".join(lines)


def detect_key_files(project_dir: str) -> list[str]:
    """Identify key project files."""
    candidates = [
        "README.md", "CLAUDE.md", "CONTRIBUTING.md",
        "setup.sh", "Makefile", "justfile",
        "pyproject.toml", "package.json", "mix.exs",
        "Dockerfile", "docker-compose.yml",
    ]
    found = []
    for c in candidates:
        if os.path.exists(os.path.join(project_dir, c)):
            found.append(c)
    return found


def get_recent_git_changes(project_dir: str, count: int = 10) -> list[str]:
    """Get recent git commit messages."""
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{count}"],
            capture_output=True, text=True, cwd=project_dir, timeout=5,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def generate_project_md(project_dir: str) -> str:
    """Generate PROJECT.md content for the given project directory."""
    project_name = os.path.basename(os.path.abspath(project_dir))
    tech_stack = detect_tech_stack(project_dir)
    tree = generate_directory_tree(project_dir)
    key_files = detect_key_files(project_dir)
    recent_changes = get_recent_git_changes(project_dir)

    sections = [
        f"# Project: {project_name}",
        "",
        "## Tech Stack",
        "",
    ]
    for tech in tech_stack:
        sections.append(f"- {tech}")
    if not tech_stack:
        sections.append("- (none detected)")
    sections.append("")

    sections.extend([
        "## Directory Structure",
        "",
        "```",
        tree if tree else "(empty)",
        "```",
        "",
        "## Key Files",
        "",
    ])
    for f in key_files:
        sections.append(f"- {f}")
    if not key_files:
        sections.append("- (none detected)")
    sections.append("")

    sections.extend([
        "## Recent Changes",
        "",
    ])
    for change in recent_changes:
        sections.append(f"- {change}")
    if not recent_changes:
        sections.append("- (no git history)")

    return "\n".join(sections) + "\n"


def update_project_context(project_dir: Optional[str] = None) -> dict:
    """Main entry point: generate and write PROJECT.md."""
    if project_dir is None:
        project_dir = os.getcwd()

    content = generate_project_md(project_dir)

    output_dir = os.path.join(project_dir, ".crux", "context")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "PROJECT.md")
    with open(output_path, "w") as f:
        f.write(content)

    return {
        "output_path": output_path,
        "content": content,
    }


def main() -> None:
    """CLI entry point."""
    import sys

    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    result = update_project_context(project_dir)
    print(f"Written to: {result['output_path']}")


if __name__ == "__main__":  # pragma: no cover
    main()
