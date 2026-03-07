"""Tests for crux_ollama.py — lightweight Ollama REST API client."""

import json
import os
from unittest.mock import patch, MagicMock
from urllib.error import URLError

import pytest

from scripts.lib.crux_ollama import (
    check_ollama_running,
    list_models,
    pull_model,
    generate,
    DEFAULT_ENDPOINT,
)


# ---------------------------------------------------------------------------
# check_ollama_running
# ---------------------------------------------------------------------------

class TestCheckOllamaRunning:
    def test_returns_true_when_ollama_responds(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"models":[]}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            assert check_ollama_running() is True

    def test_returns_false_when_connection_refused(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=URLError("Connection refused")):
            assert check_ollama_running() is False

    def test_returns_false_on_timeout(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=TimeoutError("timed out")):
            assert check_ollama_running() is False

    def test_uses_custom_endpoint(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp) as mock_open:
            check_ollama_running(endpoint="http://custom:1234")
            call_arg = mock_open.call_args[0][0]
            assert "custom:1234" in (call_arg if isinstance(call_arg, str) else call_arg.full_url)

    def test_default_endpoint(self):
        assert DEFAULT_ENDPOINT == "http://localhost:11434"


# ---------------------------------------------------------------------------
# list_models
# ---------------------------------------------------------------------------

class TestListModels:
    def test_returns_model_list(self):
        resp_data = {"models": [
            {"name": "qwen3:8b", "size": 4_000_000_000},
            {"name": "qwen3:32b", "size": 16_000_000_000},
        ]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = list_models()
            assert result["success"] is True
            assert len(result["models"]) == 2
            assert result["models"][0]["name"] == "qwen3:8b"

    def test_returns_error_on_connection_failure(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=URLError("refused")):
            result = list_models()
            assert result["success"] is False
            assert "error" in result

    def test_returns_error_on_malformed_json(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'not json'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = list_models()
            assert result["success"] is False
            assert "error" in result

    def test_empty_model_list(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"models": []}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = list_models()
            assert result["success"] is True
            assert result["models"] == []


# ---------------------------------------------------------------------------
# pull_model
# ---------------------------------------------------------------------------

class TestPullModel:
    def test_successful_pull(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = pull_model("qwen3:8b")
            assert result["success"] is True
            assert result["model"] == "qwen3:8b"

    def test_pull_sends_correct_payload(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp) as mock_open:
            pull_model("llama3:8b")
            req = mock_open.call_args[0][0]
            body = json.loads(req.data)
            assert body["name"] == "llama3:8b"
            assert req.get_header("Content-type") == "application/json"

    def test_pull_connection_error(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=URLError("refused")):
            result = pull_model("qwen3:8b")
            assert result["success"] is False
            assert "error" in result

    def test_pull_timeout(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=TimeoutError("timed out")):
            result = pull_model("qwen3:8b")
            assert result["success"] is False

    def test_pull_malformed_response(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'not json'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = pull_model("qwen3:8b")
            assert result["success"] is False
            assert "error" in result

    def test_pull_empty_model_name(self):
        result = pull_model("")
        assert result["success"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_successful_generation(self):
        resp_data = {
            "response": "This script has no security issues.",
            "done": True,
            "model": "qwen3:8b",
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = generate(model="qwen3:8b", prompt="Review this script")
            assert result["success"] is True
            assert result["response"] == "This script has no security issues."
            assert result["model"] == "qwen3:8b"

    def test_generation_with_system_prompt(self):
        resp_data = {"response": "ok", "done": True, "model": "qwen3:8b"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp) as mock_open:
            generate(model="qwen3:8b", prompt="test", system="You are an auditor")
            req = mock_open.call_args[0][0]
            body = json.loads(req.data)
            assert body["system"] == "You are an auditor"
            assert body["prompt"] == "test"
            assert body["model"] == "qwen3:8b"
            assert body["stream"] is False

    def test_generation_connection_error(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=URLError("refused")):
            result = generate(model="qwen3:8b", prompt="test")
            assert result["success"] is False
            assert "error" in result

    def test_generation_timeout(self):
        with patch("scripts.lib.crux_ollama.urlopen", side_effect=TimeoutError("timed out")):
            result = generate(model="qwen3:8b", prompt="test")
            assert result["success"] is False

    def test_generation_malformed_response(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'not json at all'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp):
            result = generate(model="qwen3:8b", prompt="test")
            assert result["success"] is False
            assert "error" in result

    def test_generation_uses_custom_endpoint(self):
        resp_data = {"response": "ok", "done": True, "model": "m"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp) as mock_open:
            generate(model="m", prompt="p", endpoint="http://gpu:11434")
            req = mock_open.call_args[0][0]
            assert "gpu:11434" in req.full_url

    def test_generation_custom_timeout(self):
        resp_data = {"response": "ok", "done": True, "model": "m"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("scripts.lib.crux_ollama.urlopen", return_value=mock_resp) as mock_open:
            generate(model="m", prompt="p", timeout=300)
            _, kwargs = mock_open.call_args
            assert kwargs.get("timeout") == 300

    def test_generation_empty_prompt(self):
        result = generate(model="qwen3:8b", prompt="")
        assert result["success"] is False
        assert "error" in result

    def test_generation_empty_model(self):
        result = generate(model="", prompt="test")
        assert result["success"] is False
        assert "error" in result
