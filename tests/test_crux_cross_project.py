"""Tests for crux_cross_project.py — cross-project aggregation."""

import json
import os

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session
from scripts.lib.crux_cross_project import (
    _count_corrections,
    _count_interactions_for_date,
    _is_safe_path,
    _load_registry,
    _read_corrections,
    _save_registry,
    _scan_directory_bounded,
    _MAX_PROJECTS,
    discover_projects,
    register_project,
    unregister_project,
    aggregate_digests,
    aggregate_corrections,
    generate_user_digest,
)


@pytest.fixture
def env(tmp_path):
    """Multi-project environment with shared home."""
    home = tmp_path / "home"
    home.mkdir()
    init_user(home=str(home))

    projects = {}
    for name in ["alpha", "beta", "gamma"]:
        p = home / "projects" / name
        p.mkdir(parents=True)
        init_project(project_dir=str(p))
        projects[name] = str(p)

    return {"home": str(home), "projects": projects, "tmp": str(tmp_path)}


def _write_interactions(project_dir, count, date_str="2026-03-06"):
    log_dir = os.path.join(project_dir, ".crux", "analytics", "interactions")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"{date_str}.jsonl"), "w") as f:
        for i in range(count):
            f.write(json.dumps({
                "timestamp": f"{date_str}T01:00:00Z",
                "tool_name": "Bash", "tool_input": {},
            }) + "\n")


def _write_corrections(project_dir, count, category="style"):
    corr_dir = os.path.join(project_dir, ".crux", "corrections")
    os.makedirs(corr_dir, exist_ok=True)
    with open(os.path.join(corr_dir, "corrections.jsonl"), "a") as f:
        for i in range(count):
            f.write(json.dumps({
                "original": f"bad{i}", "corrected": f"good{i}",
                "category": category, "mode": "build-py",
                "timestamp": "2026-03-06T01:00:00Z",
            }) + "\n")


def _set_mode(project_dir, mode):
    state = SessionState(active_mode=mode, active_tool="claude-code")
    save_session(state, project_crux_dir=os.path.join(project_dir, ".crux"))


# ---------------------------------------------------------------------------
# discover_projects
# ---------------------------------------------------------------------------

class TestDiscoverProjects:
    def test_finds_projects_in_home(self, env):
        # Projects are siblings of home in tmp_path, not children of home
        # Register them first
        for p in env["projects"].values():
            register_project(p, env["home"])

        result = discover_projects(env["home"])
        assert len(result) >= 3

    def test_finds_projects_via_registry(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        result = discover_projects(env["home"])
        assert env["projects"]["alpha"] in result

    def test_empty_when_no_projects(self, tmp_path):
        home = tmp_path / "empty-home"
        home.mkdir()
        init_user(home=str(home))
        result = discover_projects(str(home))
        assert result == []

    def test_deduplicates_results(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        register_project(env["projects"]["alpha"], env["home"])  # duplicate add
        result = discover_projects(env["home"])
        assert result.count(env["projects"]["alpha"]) == 1

    def test_skips_removed_projects(self, env):
        fake_path = "/tmp/nonexistent-project-abc123"
        projects = [fake_path]
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump({"projects": projects}, f)
        result = discover_projects(env["home"])
        assert fake_path not in result


# ---------------------------------------------------------------------------
# register_project / unregister_project
# ---------------------------------------------------------------------------

class TestRegisterProject:
    def test_register_new_project(self, env):
        result = register_project(env["projects"]["alpha"], env["home"])
        assert result["registered"] is True
        assert result["total_projects"] == 1

    def test_register_duplicate_returns_false(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        result = register_project(env["projects"]["alpha"], env["home"])
        assert result["registered"] is False
        assert "already" in result["reason"]

    def test_unregister_existing(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        result = unregister_project(env["projects"]["alpha"], env["home"])
        assert result["unregistered"] is True

    def test_unregister_nonexistent(self, env):
        result = unregister_project("/nonexistent", env["home"])
        assert result["unregistered"] is False


# ---------------------------------------------------------------------------
# aggregate_digests
# ---------------------------------------------------------------------------

class TestAggregateDigests:
    def test_aggregates_interactions_across_projects(self, env):
        for name, path in env["projects"].items():
            register_project(path, env["home"])
            _write_interactions(path, 10)

        result = aggregate_digests(env["home"], date_str="2026-03-06")
        assert result["total_projects"] >= 3
        assert result["total_interactions"] >= 30

    def test_aggregates_corrections(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])
            _write_corrections(path, 5)

        result = aggregate_digests(env["home"])
        assert result["total_corrections"] >= 15

    def test_collects_modes_used(self, env):
        for name, path in env["projects"].items():
            register_project(path, env["home"])
            _set_mode(path, "build-py" if name != "gamma" else "debug")

        result = aggregate_digests(env["home"])
        assert "build-py" in result["modes_used"]
        assert "debug" in result["modes_used"]

    def test_empty_projects(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])

        result = aggregate_digests(env["home"])
        assert result["total_interactions"] == 0
        assert result["total_corrections"] == 0

    def test_per_project_breakdown(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        _write_interactions(env["projects"]["alpha"], 5)

        result = aggregate_digests(env["home"], date_str="2026-03-06")
        assert len(result["projects"]) >= 1
        alpha_summary = next(p for p in result["projects"] if p["project"] == env["projects"]["alpha"])
        assert alpha_summary["interactions"] == 5


# ---------------------------------------------------------------------------
# aggregate_corrections
# ---------------------------------------------------------------------------

class TestAggregateCorrections:
    def test_detects_cross_project_patterns(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])
            _write_corrections(path, 3, category="style")

        result = aggregate_corrections(env["home"])
        assert len(result["cross_project_patterns"]) >= 1
        style_pattern = next(p for p in result["patterns"] if p["category"] == "style")
        assert style_pattern["cross_project"] is True
        assert style_pattern["project_count"] >= 3

    def test_single_project_not_cross_project(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        _write_corrections(env["projects"]["alpha"], 3, category="logic")

        result = aggregate_corrections(env["home"])
        logic = next(p for p in result["patterns"] if p["category"] == "logic")
        assert logic["cross_project"] is False

    def test_no_corrections_returns_empty(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])

        result = aggregate_corrections(env["home"])
        assert result["patterns"] == []
        assert result["cross_project_patterns"] == []

    def test_multiple_categories(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])
        _write_corrections(env["projects"]["alpha"], 2, category="style")
        _write_corrections(env["projects"]["beta"], 3, category="logic")
        _write_corrections(env["projects"]["gamma"], 1, category="style")

        result = aggregate_corrections(env["home"])
        cats = {p["category"] for p in result["patterns"]}
        assert "style" in cats
        assert "logic" in cats

    def test_handles_malformed_corrections(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        corr_dir = os.path.join(env["projects"]["alpha"], ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"category": "style"}) + "\n")

        result = aggregate_corrections(env["home"])
        assert len(result["patterns"]) == 1


# ---------------------------------------------------------------------------
# generate_user_digest
# ---------------------------------------------------------------------------

class TestGenerateUserDigest:
    def test_generates_digest_file(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])
            _write_interactions(path, 5)
            _write_corrections(path, 2, category="style")
            _set_mode(path, "build-py")

        result = generate_user_digest(env["home"], date_str="2026-03-06")
        assert os.path.exists(result["output_path"])
        assert "2026-03-06" in result["date"]
        assert "User Digest" in result["content"]

    def test_digest_includes_cross_project_patterns(self, env):
        for path in env["projects"].values():
            register_project(path, env["home"])
            _write_corrections(path, 3, category="style")

        result = generate_user_digest(env["home"])
        assert "Cross-Project" in result["content"]
        assert "style" in result["content"]

    def test_digest_includes_per_project_breakdown(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        _write_interactions(env["projects"]["alpha"], 10)
        _set_mode(env["projects"]["alpha"], "debug")

        result = generate_user_digest(env["home"], date_str="2026-03-06")
        assert "alpha" in result["content"]
        assert "debug" in result["content"]

    def test_empty_digest_when_no_data(self, tmp_path):
        """Projects exist but have no analytics data."""
        home = tmp_path / "empty_home"
        home.mkdir()
        init_user(home=str(home))
        result = generate_user_digest(str(home))
        assert result["digest"]["total_projects"] == 0
        assert result["digest"]["total_interactions"] == 0

    def test_returns_digest_and_correction_data(self, env):
        result = generate_user_digest(env["home"])
        assert "digest" in result
        assert "corrections" in result
        assert "content" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_corrupt_registry_handled(self, env):
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            f.write("not json")
        result = discover_projects(env["home"])
        assert isinstance(result, list)

    def test_permission_error_handled(self, env, monkeypatch):
        import scripts.lib.crux_cross_project as cp
        original_listdir = os.listdir

        def mock_listdir(path):
            if "personal" in path or path == env["home"]:
                raise PermissionError("no access")
            return original_listdir(path)

        monkeypatch.setattr(os, "listdir", mock_listdir)
        result = discover_projects(env["home"])
        assert isinstance(result, list)

    def test_discovers_projects_in_home_subdir(self, env):
        """Projects in ~/projects/ should be found."""
        projects_dir = os.path.join(env["home"], "projects")
        os.makedirs(projects_dir, exist_ok=True)
        proj = os.path.join(projects_dir, "myproject")
        os.makedirs(proj)
        init_project(project_dir=proj)

        result = discover_projects(env["home"])
        assert proj in result

    def test_missing_session_state(self, env):
        register_project(env["projects"]["alpha"], env["home"])
        # Don't set any mode — session state file may not exist
        result = aggregate_digests(env["home"])
        alpha = next(p for p in result["projects"] if p["project"] == env["projects"]["alpha"])
        # active_mode should be the default or None
        assert isinstance(alpha["active_mode"], (str, type(None)))


# ---------------------------------------------------------------------------
# Coverage gap tests
# ---------------------------------------------------------------------------


class TestIsSafePathEdge:
    def test_oserror_returns_false(self, monkeypatch):
        """Line 57-58: OSError/ValueError in _is_safe_path returns False."""
        monkeypatch.setattr(os.path, "realpath", lambda p: (_ for _ in ()).throw(OSError("bad")))
        assert _is_safe_path("/some/path", "/home") is False


class TestLoadRegistryEdge:
    def test_registry_too_large(self, env):
        """Lines 68-69: Registry file too large refuses to load."""
        import scripts.lib.crux_cross_project as cp
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump({"projects": []}, f)
        original_getsize = os.path.getsize
        def mock_getsize(path):
            if path == registry_path:
                return cp._MAX_FILE_SIZE + 1
            return original_getsize(path)
        import unittest.mock
        with unittest.mock.patch("os.path.getsize", side_effect=mock_getsize):
            result = _load_registry(env["home"])
        assert result == []

    def test_registry_not_dict(self, env):
        """Lines 75-76: Registry data is not a dict."""
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump([1, 2, 3], f)
        result = _load_registry(env["home"])
        assert result == []

    def test_projects_not_list(self, env):
        """Lines 81-82: projects key is not a list."""
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump({"projects": "not-a-list"}, f)
        result = _load_registry(env["home"])
        assert result == []


class TestSaveRegistryEdge:
    def test_filters_unsafe_paths(self, env):
        """Line 111: Save registry filters unsafe paths and warns."""
        # Register a valid project first
        register_project(env["projects"]["alpha"], env["home"])
        # Manually save with an unsafe path mixed in
        projects = [env["projects"]["alpha"], "/outside/home/unsafe"]
        _save_registry(env["home"], projects)
        # Reload and verify unsafe path was filtered
        loaded = _load_registry(env["home"])
        assert "/outside/home/unsafe" not in loaded

    def test_atomic_write_failure_cleans_up(self, env):
        """Lines 122-127: Exception during atomic write cleans up temp file."""
        import unittest.mock
        with unittest.mock.patch("os.replace", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                _save_registry(env["home"], [env["projects"]["alpha"]])

    def test_atomic_write_failure_unlink_also_fails(self, env):
        """Lines 125-126: os.unlink fails too during cleanup (except OSError: pass)."""
        import unittest.mock
        original_replace = os.replace
        original_unlink = os.unlink
        def mock_replace(src, dst):
            if dst.endswith("projects.json"):
                raise OSError("disk full")
            return original_replace(src, dst)
        def mock_unlink(path):
            if path.endswith(".json.tmp"):
                raise OSError("cannot unlink")
            return original_unlink(path)
        with unittest.mock.patch("os.replace", side_effect=mock_replace):
            with unittest.mock.patch("os.unlink", side_effect=mock_unlink):
                with pytest.raises(OSError, match="disk full"):
                    _save_registry(env["home"], [env["projects"]["alpha"]])


class TestDiscoverProjectsEdge:
    def test_max_projects_from_registry(self, env, monkeypatch):
        """Lines 151-152: Hit max projects limit from registry."""
        # Create a fake registry with _MAX_PROJECTS entries all pointing to dirs with .crux
        fake_projects = []
        for i in range(_MAX_PROJECTS):
            p = os.path.join(env["home"], "projects", f"proj_{i}")
            os.makedirs(os.path.join(p, ".crux"), exist_ok=True)
            fake_projects.append(p)
        registry_path = os.path.join(env["home"], ".crux", "projects.json")
        with open(registry_path, "w") as f:
            json.dump({"projects": fake_projects}, f)
        result = discover_projects(env["home"])
        assert len(result) >= _MAX_PROJECTS

    def test_timeout(self, env, monkeypatch):
        """Lines 158-159: Discovery times out."""
        import time
        import scripts.lib.crux_cross_project as cp
        # Make time.time() return a huge value after first call
        call_count = [0]
        def mock_time():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0.0
            return 999999.0
        monkeypatch.setattr(time, "time", mock_time)
        result = discover_projects(env["home"])
        assert isinstance(result, list)

    def test_scan_root_outside_home(self, env, monkeypatch):
        """Line 167: Scan root fails _is_safe_path check."""
        import scripts.lib.crux_cross_project as cp
        original_is_safe = cp._is_safe_path

        def mock_is_safe(path, home):
            # Make scan roots fail safety check but let registry paths pass
            if path.endswith("projects") or path.endswith("personal") or path.endswith("work") or path.endswith("src") or path.endswith("dev") or path == home:
                return False
            return original_is_safe(path, home)

        monkeypatch.setattr(cp, "_is_safe_path", mock_is_safe)
        result = discover_projects(env["home"])
        assert isinstance(result, list)

    def test_max_projects_from_scan(self, env, monkeypatch):
        """Lines 174-175: Hit max projects limit during scanning."""
        import scripts.lib.crux_cross_project as cp
        monkeypatch.setattr(cp, "_MAX_PROJECTS", 1)
        # Create two projects in projects dir
        for name in ["p1", "p2"]:
            p = os.path.join(env["home"], "projects", name)
            os.makedirs(os.path.join(p, ".crux"), exist_ok=True)
        result = discover_projects(env["home"])
        # _scan_directory_bounded checks len(found) + len(already_found) >= _MAX_PROJECTS
        # before adding more, so the limit of 1 is strictly enforced.
        assert len(result) <= 1

    def test_permission_error_during_scan(self, env, monkeypatch):
        """Lines 177-178: PermissionError during scanning is caught."""
        import scripts.lib.crux_cross_project as cp
        def mock_scan(*args, **kwargs):
            raise PermissionError("no access")
        monkeypatch.setattr(cp, "_scan_directory_bounded", mock_scan)
        result = discover_projects(env["home"])
        assert isinstance(result, list)


class TestScanDirectoryBounded:
    def test_max_depth_zero(self, env):
        """Line 196: max_depth <= 0 returns empty set."""
        result = _scan_directory_bounded(env["home"], env["home"], 0, set())
        assert result == set()

    def test_skips_hidden_dirs(self, env):
        """Line 202: Skip hidden directories other than .crux."""
        hidden = os.path.join(env["home"], "projects", ".hidden_project")
        os.makedirs(os.path.join(hidden, ".crux"), exist_ok=True)
        result = _scan_directory_bounded(
            os.path.join(env["home"], "projects"), env["home"], 2, set()
        )
        assert hidden not in result

    def test_unsafe_path_in_scan(self, env, monkeypatch):
        """Line 208: Unsafe path skipped during scan."""
        import scripts.lib.crux_cross_project as cp
        original_is_safe = cp._is_safe_path

        def mock_is_safe(path, home):
            if "alpha" in path:
                return False
            return original_is_safe(path, home)

        monkeypatch.setattr(cp, "_is_safe_path", mock_is_safe)
        result = _scan_directory_bounded(
            os.path.join(env["home"], "projects"), env["home"], 2, set()
        )
        assert all("alpha" not in p for p in result)

    def test_max_projects_in_scan(self, env, monkeypatch):
        """Line 218: Max projects reached during recursive scan."""
        import scripts.lib.crux_cross_project as cp
        monkeypatch.setattr(cp, "_MAX_PROJECTS", 1)
        result = _scan_directory_bounded(
            os.path.join(env["home"], "projects"), env["home"], 2, set()
        )
        assert len(result) <= 1

    def test_oserror_in_listdir(self, env, monkeypatch):
        """Lines 225-226: OSError during listdir is caught."""
        original_listdir = os.listdir
        def mock_listdir(path):
            if "projects" in path:
                raise OSError("I/O error")
            return original_listdir(path)
        monkeypatch.setattr(os, "listdir", mock_listdir)
        result = _scan_directory_bounded(
            os.path.join(env["home"], "projects"), env["home"], 2, set()
        )
        assert result == set()


class TestRegisterProjectEdge:
    def test_register_outside_home(self, tmp_path):
        """Lines 241-242: Reject project outside home directory."""
        home = tmp_path / "home"
        home.mkdir()
        init_user(home=str(home))
        outside = tmp_path / "outside"
        outside.mkdir()
        result = register_project(str(outside), str(home))
        assert result["registered"] is False
        assert result["reason"] == "path_outside_home_directory"

    def test_register_nonexistent_dir(self, env):
        """Line 250: Register a path that is within home but doesn't exist."""
        nonexistent = os.path.join(env["home"], "projects", "does_not_exist")
        result = register_project(nonexistent, env["home"])
        assert result["registered"] is False
        assert result["reason"] == "directory_not_found"

    def test_register_max_projects(self, env, monkeypatch):
        """Line 259: Max projects reached during registration."""
        import scripts.lib.crux_cross_project as cp
        monkeypatch.setattr(cp, "_MAX_PROJECTS", 1)
        register_project(env["projects"]["alpha"], env["home"])
        result = register_project(env["projects"]["beta"], env["home"])
        assert result["registered"] is False
        assert result["reason"] == "max_projects_reached"


class TestCountInteractionsEdge:
    def test_oserror_reading_interactions(self, env):
        """Lines 297-298: OSError reading interactions file."""
        proj = env["projects"]["alpha"]
        log_dir = os.path.join(proj, ".crux", "analytics", "interactions")
        os.makedirs(log_dir, exist_ok=True)
        # Create a file that exists but will cause read issues
        filepath = os.path.join(log_dir, "2026-03-06.jsonl")
        with open(filepath, "w") as f:
            f.write("line1\n")
        # Make the file unreadable by mocking open
        import unittest.mock
        import builtins
        original_open = builtins.open
        def mock_open(path, *args, **kwargs):
            if str(path) == filepath:
                raise OSError("cannot read")
            return original_open(path, *args, **kwargs)
        with unittest.mock.patch("builtins.open", side_effect=mock_open):
            result = _count_interactions_for_date(proj, "2026-03-06")
        assert result == 0


class TestCountCorrectionsEdge:
    def test_oserror_reading_corrections(self, env):
        """Lines 312-313: OSError reading corrections file."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        filepath = os.path.join(corr_dir, "corrections.jsonl")
        with open(filepath, "w") as f:
            f.write("line1\n")
        import unittest.mock
        import builtins
        original_open = builtins.open
        def mock_open(path, *args, **kwargs):
            if str(path) == filepath:
                raise OSError("cannot read")
            return original_open(path, *args, **kwargs)
        with unittest.mock.patch("builtins.open", side_effect=mock_open):
            result = _count_corrections(proj)
        assert result == 0


class TestReadCorrectionsEdge:
    def test_blank_lines_skipped(self, env):
        """Line 342: Blank lines in corrections file are skipped."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write("\n")
            f.write(json.dumps({"category": "valid"}) + "\n")
            f.write("\n")
            f.write("  \n")
        result = _read_corrections(proj)
        assert len(result) == 1
        assert result[0]["category"] == "valid"

    def test_non_dict_entry_skipped(self, env):
        """Lines 346: Non-dict entries are skipped."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write(json.dumps([1, 2, 3]) + "\n")  # a list, not a dict
            f.write(json.dumps({"category": "valid"}) + "\n")
        result = _read_corrections(proj)
        assert len(result) == 1
        assert result[0]["category"] == "valid"

    def test_non_dict_entry_strict_raises(self, env):
        """Lines 347-349: Non-dict entry in strict mode raises ValueError."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write(json.dumps([1, 2, 3]) + "\n")
        with pytest.raises(ValueError, match="expected dict"):
            _read_corrections(proj, strict=True)

    def test_json_decode_error_strict_raises(self, env):
        """Lines 358-361: JSONDecodeError in strict mode raises ValueError."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write("not valid json\n")
        with pytest.raises(ValueError, match="invalid JSON"):
            _read_corrections(proj, strict=True)

    def test_oserror_reading_corrections_file(self, env):
        """Lines 360-361: OSError when reading corrections file."""
        proj = env["projects"]["alpha"]
        corr_dir = os.path.join(proj, ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        filepath = os.path.join(corr_dir, "corrections.jsonl")
        with open(filepath, "w") as f:
            f.write("data\n")
        import unittest.mock
        import builtins
        original_open = builtins.open
        def mock_open(path, *args, **kwargs):
            if str(path) == filepath:
                raise OSError("cannot read")
            return original_open(path, *args, **kwargs)
        with unittest.mock.patch("builtins.open", side_effect=mock_open):
            result = _read_corrections(proj)
        assert result == []


class TestGenerateUserDigestEdge:
    def test_atomic_write_failure(self, env, monkeypatch):
        """Lines 516-521: Exception during digest atomic write cleans up."""
        for path in env["projects"].values():
            register_project(path, env["home"])
        import unittest.mock
        original_replace = os.replace
        def mock_replace(src, dst):
            if dst.endswith(".md"):
                raise OSError("disk full")
            return original_replace(src, dst)
        with unittest.mock.patch("os.replace", side_effect=mock_replace):
            with pytest.raises(OSError, match="disk full"):
                generate_user_digest(env["home"])

    def test_atomic_write_failure_unlink_also_fails(self, env, monkeypatch):
        """Lines 519-520: os.unlink fails too during digest cleanup."""
        for path in env["projects"].values():
            register_project(path, env["home"])
        import unittest.mock
        original_replace = os.replace
        original_unlink = os.unlink
        def mock_replace(src, dst):
            if dst.endswith(".md"):
                raise OSError("disk full")
            return original_replace(src, dst)
        def mock_unlink(path):
            if path.endswith(".md.tmp"):
                raise OSError("cannot unlink")
            return original_unlink(path)
        with unittest.mock.patch("os.replace", side_effect=mock_replace):
            with unittest.mock.patch("os.unlink", side_effect=mock_unlink):
                with pytest.raises(OSError, match="disk full"):
                    generate_user_digest(env["home"])
