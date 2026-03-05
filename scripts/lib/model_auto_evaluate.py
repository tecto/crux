"""Auto-evaluate models against correction scenarios for quality comparison."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvaluationScenario:
    prompt: str
    expected_behavior: str
    category: str
    mode: str

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "expected_behavior": self.expected_behavior,
            "category": self.category,
            "mode": self.mode,
        }


@dataclass
class EvaluationResult:
    model: str
    scenario: EvaluationScenario
    response: str = ""
    passed: bool = False
    score: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "scenario": self.scenario.to_dict(),
            "response": self.response[:500],
            "passed": self.passed,
            "score": self.score,
            "error": self.error,
        }


@dataclass
class ModelEvaluation:
    model: str
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    avg_score: float = 0.0
    results: list[EvaluationResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "total_scenarios": self.total_scenarios,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "avg_score": round(self.avg_score, 2),
        }


def load_scenarios_from_corrections(reflections_dir: str, max_scenarios: int = 20) -> list[EvaluationScenario]:
    """Generate evaluation scenarios from past correction patterns."""
    scenarios = []
    try:
        for filename in sorted(os.listdir(reflections_dir)):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(reflections_dir, filename)
            try:
                with open(filepath, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            if entry.get("type") == "self-correction":
                                scenarios.append(EvaluationScenario(
                                    prompt=entry.get("original", ""),
                                    expected_behavior=entry.get("corrected", ""),
                                    category=entry.get("category", "unknown"),
                                    mode=entry.get("mode", "unknown"),
                                ))
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue
            if len(scenarios) >= max_scenarios:
                break
    except FileNotFoundError:
        pass
    return scenarios[:max_scenarios]


def query_model(model: str, prompt: str, timeout: int = 30) -> str:
    """Send a prompt to a model via Ollama and return the response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def score_response(response: str, expected: str) -> float:
    """Simple keyword overlap scoring between response and expected behavior."""
    if not response or not expected:
        return 0.0

    expected_words = set(expected.lower().split())
    response_words = set(response.lower().split())

    if not expected_words:
        return 0.0

    overlap = expected_words & response_words
    return len(overlap) / len(expected_words)


def evaluate_model(
    model: str,
    scenarios: list[EvaluationScenario],
    timeout: int = 30,
) -> ModelEvaluation:
    """Run all scenarios against a model and collect results."""
    evaluation = ModelEvaluation(model=model, total_scenarios=len(scenarios))

    for scenario in scenarios:
        response = query_model(model, scenario.prompt, timeout)

        if not response:
            result = EvaluationResult(
                model=model,
                scenario=scenario,
                error="No response from model",
            )
            evaluation.errors += 1
        else:
            score = score_response(response, scenario.expected_behavior)
            passed = score >= 0.3
            result = EvaluationResult(
                model=model,
                scenario=scenario,
                response=response,
                passed=passed,
                score=score,
            )
            if passed:
                evaluation.passed += 1
            else:
                evaluation.failed += 1

        evaluation.results.append(result)

    total_scores = sum(r.score for r in evaluation.results)
    evaluation.avg_score = total_scores / len(scenarios) if scenarios else 0.0

    return evaluation


def run_evaluation(
    models: list[str],
    reflections_dir: Optional[str] = None,
    max_scenarios: int = 20,
) -> dict:
    """Main entry point: load scenarios, evaluate models, return comparison."""
    if reflections_dir is None:
        reflections_dir = os.path.join(
            os.environ.get("HOME", ""),
            ".crux", "corrections",
        )

    scenarios = load_scenarios_from_corrections(reflections_dir, max_scenarios)

    if not scenarios:
        return {
            "error": "No correction scenarios found. Run extract_corrections first.",
            "evaluations": [],
        }

    evaluations = []
    for model in models:
        evaluation = evaluate_model(model, scenarios)
        evaluations.append(evaluation.to_dict())

    # Rank by avg_score
    evaluations.sort(key=lambda e: e["avg_score"], reverse=True)

    return {
        "total_scenarios": len(scenarios),
        "models_evaluated": len(models),
        "evaluations": evaluations,
        "best_model": evaluations[0]["model"] if evaluations else None,
    }


def main() -> None:
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: model_auto_evaluate.py <model1> [model2] ...")
        sys.exit(1)

    models = sys.argv[1:]
    result = run_evaluation(models)

    if "error" in result:
        print(result["error"])
        sys.exit(0)

    print(f"Evaluated {result['models_evaluated']} models on {result['total_scenarios']} scenarios:")
    for ev in result["evaluations"]:
        print(f"  {ev['model']}: {ev['passed']}/{ev['total_scenarios']} passed, avg score: {ev['avg_score']}")

    if result["best_model"]:
        print(f"\nBest model: {result['best_model']}")


if __name__ == "__main__":  # pragma: no cover
    main()
