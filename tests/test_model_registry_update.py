"""Tests for model_registry_update.py — model registry management."""

import json
import os
import subprocess
import tempfile

import pytest

from scripts.lib.model_registry_update import (
    ModelInfo,
    load_registry,
    main,
    query_ollama_models,
    save_registry,
    update_registry,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestModelInfo:
    def test_to_dict(self):
        m = ModelInfo(name="qwen3:32b", size="18GB", quantization="Q4_K_M")
        d = m.to_dict()
        assert d["name"] == "qwen3:32b"
        assert d["size"] == "18GB"

    def test_defaults(self):
        m = ModelInfo(name="test")
        assert m.size == ""
        assert m.quantization == ""


class TestQueryOllamaModels:
    def test_handles_missing_ollama(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("ollama not found")
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert models == []

    def test_handles_timeout(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("ollama", 10)
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert models == []

    def test_handles_failed_command(self, monkeypatch):
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error")
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert models == []

    def test_parses_output(self, monkeypatch):
        output = "NAME                    ID              SIZE      MODIFIED\nqwen3:32b               abc123          18 GB     2 hours ago\nllama3:8b               def456          4.7 GB    1 day ago\n"
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert len(models) == 2
        assert models[0].name == "qwen3:32b"

    def test_handles_empty_output(self, monkeypatch):
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="NAME\n", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert models == []

    def test_parses_quantization_from_name(self, monkeypatch):
        output = "NAME                    ID              SIZE      MODIFIED\nqwen3:8b-q4_K_M         abc123          4.7 GB    1 day ago\n"
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)
        models = query_ollama_models()
        assert len(models) == 1
        assert models[0].quantization.startswith("q")


class TestLoadRegistry:
    def test_loads_existing(self, temp_dir):
        path = os.path.join(temp_dir, "registry.json")
        data = {"models": [{"name": "test"}], "active": "test", "lastUpdated": "2026-03-05"}
        with open(path, "w") as f:
            json.dump(data, f)
        registry = load_registry(path)
        assert len(registry["models"]) == 1
        assert registry["active"] == "test"

    def test_returns_empty_for_missing(self, temp_dir):
        registry = load_registry(os.path.join(temp_dir, "nope.json"))
        assert registry["models"] == []
        assert registry["active"] is None

    def test_returns_empty_for_invalid_json(self, temp_dir):
        path = os.path.join(temp_dir, "bad.json")
        with open(path, "w") as f:
            f.write("not json")
        registry = load_registry(path)
        assert registry["models"] == []


class TestSaveRegistry:
    def test_saves_and_creates_dir(self, temp_dir):
        path = os.path.join(temp_dir, "new", "dir", "registry.json")
        registry = {"models": [{"name": "test"}], "active": "test"}
        save_registry(registry, path)

        assert os.path.exists(path)
        loaded = json.loads(open(path).read())
        assert loaded["lastUpdated"] is not None
        assert len(loaded["models"]) == 1


class TestUpdateRegistry:
    def test_updates_without_ollama(self, temp_dir):
        path = os.path.join(temp_dir, "registry.json")
        result = update_registry(path, include_ollama=False)
        assert result["total_models"] == 0
        assert result["newly_added"] == 0
        assert os.path.exists(path)

    def test_updates_with_existing_models(self, temp_dir):
        path = os.path.join(temp_dir, "registry.json")
        data = {"models": [{"name": "existing"}], "active": "existing", "lastUpdated": None}
        with open(path, "w") as f:
            json.dump(data, f)

        result = update_registry(path, include_ollama=False)
        assert result["total_models"] == 1
        assert result["active"] == "existing"

    def test_adds_new_ollama_models(self, temp_dir, monkeypatch):
        path = os.path.join(temp_dir, "registry.json")
        output = "NAME\nqwen3:32b abc 18GB\n"
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)

        result = update_registry(path, include_ollama=True)
        assert result["newly_added"] == 1
        assert result["ollama_available"] == 1

    def test_skips_duplicate_models(self, temp_dir, monkeypatch):
        path = os.path.join(temp_dir, "registry.json")
        data = {"models": [{"name": "qwen3:32b"}], "active": None, "lastUpdated": None}
        with open(path, "w") as f:
            json.dump(data, f)

        output = "NAME\nqwen3:32b abc 18GB\n"
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)

        result = update_registry(path, include_ollama=True)
        assert result["newly_added"] == 0
        assert result["total_models"] == 1

    def test_default_path(self, temp_dir, monkeypatch):
        monkeypatch.setenv("HOME", temp_dir)
        result = update_registry(include_ollama=False)
        assert os.path.exists(result["registry_path"])


class TestCLI:
    def test_cli_output(self, temp_dir, monkeypatch, capsys):
        path = os.path.join(temp_dir, "registry.json")
        monkeypatch.setattr("sys.argv", ["model_registry_update", path])
        # Mock ollama
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        main()
        captured = capsys.readouterr()
        assert "Registry updated" in captured.out

    def test_cli_default(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setenv("HOME", temp_dir)
        monkeypatch.setattr("sys.argv", ["model_registry_update"])
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        main()
        captured = capsys.readouterr()
        assert "Registry updated" in captured.out
