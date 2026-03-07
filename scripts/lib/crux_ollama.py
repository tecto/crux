"""Lightweight Ollama REST API client using only stdlib."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "http://localhost:11434"


def check_ollama_running(endpoint: str = DEFAULT_ENDPOINT) -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        with urlopen(f"{endpoint}/api/tags", timeout=5) as resp:
            return resp.status == 200
    except (URLError, TimeoutError, OSError):
        return False


def list_models(endpoint: str = DEFAULT_ENDPOINT) -> dict:
    """List models available in Ollama."""
    try:
        with urlopen(f"{endpoint}/api/tags", timeout=10) as resp:
            data = json.loads(resp.read())
            return {"success": True, "models": data.get("models", [])}
    except (URLError, TimeoutError, OSError) as exc:
        return {"success": False, "error": f"Connection failed: {exc}", "models": []}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"success": False, "error": f"Invalid response: {exc}", "models": []}


def pull_model(name: str, endpoint: str = DEFAULT_ENDPOINT) -> dict:
    """Pull a model from the Ollama registry."""
    if not name:
        return {"success": False, "error": "Model name required"}

    req = Request(
        f"{endpoint}/api/pull",
        data=json.dumps({"name": name}).encode(),
        headers={"Content-type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
            return {"success": True, "model": name, "status": data.get("status", "unknown")}
    except (URLError, TimeoutError, OSError) as exc:
        return {"success": False, "error": f"Connection failed: {exc}", "model": name}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"success": False, "error": f"Invalid response: {exc}", "model": name}


def generate(
    model: str,
    prompt: str,
    system: str | None = None,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = 120,
) -> dict:
    """Generate a completion from an Ollama model (non-streaming)."""
    if not model:
        return {"success": False, "error": "Model name required"}
    if not prompt:
        return {"success": False, "error": "Prompt required"}

    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    req = Request(
        f"{endpoint}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return {
                "success": True,
                "response": data.get("response", ""),
                "model": data.get("model", model),
                "done": data.get("done", True),
            }
    except (URLError, TimeoutError, OSError) as exc:
        return {"success": False, "error": f"Connection failed: {exc}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"success": False, "error": f"Invalid response: {exc}"}
