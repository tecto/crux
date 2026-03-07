"""Query and update model registry with available models from Ollama."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelInfo:
    name: str
    size: str = ""
    quantization: str = ""
    modified: str = ""
    family: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "quantization": self.quantization,
            "modified": self.modified,
            "family": self.family,
        }


def query_ollama_models() -> list[ModelInfo]:
    """Query Ollama for available local models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []

        models = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                size = parts[2] if len(parts) > 2 else ""
                modified = " ".join(parts[3:]) if len(parts) > 3 else ""
                # Parse quantization from name (e.g., qwen3:8b-q4_K_M)
                quant = ""
                if "-q" in name.lower() or ":q" in name.lower():
                    quant_parts = name.lower().split("q")
                    if len(quant_parts) > 1:
                        quant = "q" + quant_parts[-1].split(":")[0].split("-")[0]

                models.append(ModelInfo(
                    name=name,
                    size=size,
                    quantization=quant,
                    modified=modified,
                ))
        return models
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def load_registry(registry_path: str) -> dict:
    """Load model registry from file."""
    try:
        with open(registry_path, "r") as f:
            return json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"models": [], "active": None, "lastUpdated": None}


def save_registry(registry: dict, registry_path: str) -> None:
    """Save model registry to file."""
    from datetime import datetime
    registry["lastUpdated"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)


def update_registry(
    registry_path: Optional[str] = None,
    include_ollama: bool = True,
) -> dict:
    """Update the model registry with locally available models."""
    if registry_path is None:
        registry_path = os.path.join(
            os.environ.get("HOME", ""),
            ".crux", "models", "registry.json",
        )

    registry = load_registry(registry_path)

    if include_ollama:
        ollama_models = query_ollama_models()
        existing_names = {m["name"] for m in registry["models"]}

        added = 0
        for model in ollama_models:
            if model.name not in existing_names:
                registry["models"].append(model.to_dict())
                added += 1
    else:
        ollama_models = []
        added = 0

    save_registry(registry, registry_path)

    return {
        "registry_path": registry_path,
        "total_models": len(registry["models"]),
        "newly_added": added,
        "active": registry["active"],
        "ollama_available": len(ollama_models),
    }


def main() -> None:
    """CLI entry point."""
    import sys

    registry_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = update_registry(registry_path)
    print(f"Registry updated: {result['total_models']} models, {result['newly_added']} new")


if __name__ == "__main__":  # pragma: no cover
    main()
