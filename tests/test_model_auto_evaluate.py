"""Tests for model_auto_evaluate.py — model evaluation pipeline."""

import json
import os
import subprocess
import tempfile

import pytest

from scripts.lib.model_auto_evaluate import (
    EvaluationResult,
    EvaluationScenario,
    ModelEvaluation,
    evaluate_model,
    load_scenarios_from_corrections,
    main,
    query_model,
    run_evaluation,
    score_response,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def make_correction(category="self_correction", mode="build-py"):
    return json.dumps({
        "timestamp": "2026-03-05T10:00:00.000Z",
        "type": "self-correction",
        "category": category,
        "original": "use a for loop to iterate",
        "corrected": "use list comprehension instead of for loop",
        "mode": mode,
    })


class TestEvaluationScenario:
    def test_to_dict(self):
        s = EvaluationScenario("prompt", "expected", "cat", "mode")
        d = s.to_dict()
        assert d["prompt"] == "prompt"
        assert d["category"] == "cat"


class TestEvaluationResult:
    def test_to_dict(self):
        s = EvaluationScenario("p", "e", "c", "m")
        r = EvaluationResult(model="test", scenario=s, response="x" * 600, passed=True, score=0.8)
        d = r.to_dict()
        assert len(d["response"]) <= 500
        assert d["passed"] is True

    def test_to_dict_with_error(self):
        s = EvaluationScenario("p", "e", "c", "m")
        r = EvaluationResult(model="test", scenario=s, error="timeout")
        d = r.to_dict()
        assert d["error"] == "timeout"


class TestModelEvaluation:
    def test_to_dict(self):
        e = ModelEvaluation(model="qwen3:32b", total_scenarios=10, passed=7, failed=2, errors=1, avg_score=0.654)
        d = e.to_dict()
        assert d["model"] == "qwen3:32b"
        assert d["avg_score"] == 0.65


class TestLoadScenarios:
    def test_loads_from_corrections(self, temp_dir):
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            f.write(make_correction() + "\n")
            f.write(make_correction(category="negation") + "\n")
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert len(scenarios) == 2
        assert scenarios[0].category == "self_correction"

    def test_limits_to_max(self, temp_dir):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            for _ in range(30):
                f.write(make_correction() + "\n")
        scenarios = load_scenarios_from_corrections(temp_dir, max_scenarios=5)
        assert len(scenarios) == 5

    def test_handles_missing_dir(self):
        scenarios = load_scenarios_from_corrections("/nonexistent")
        assert scenarios == []

    def test_skips_invalid_json(self, temp_dir):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write("bad json\n")
            f.write(make_correction() + "\n")
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert len(scenarios) == 1

    def test_skips_non_correction_entries(self, temp_dir):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write(json.dumps({"type": "other"}) + "\n")
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert scenarios == []

    def test_skips_non_jsonl_files(self, temp_dir):
        """Covers the continue branch for non-.jsonl files."""
        with open(os.path.join(temp_dir, "notes.txt"), "w") as f:
            f.write("not a jsonl file")
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write(make_correction() + "\n")
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert len(scenarios) == 1

    def test_skips_empty_lines(self, temp_dir):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write("\n" + make_correction() + "\n\n")
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert len(scenarios) == 1

    def test_handles_unreadable_file(self, temp_dir):
        path = os.path.join(temp_dir, "bad.jsonl")
        with open(path, "w") as f:
            f.write(make_correction() + "\n")
        os.chmod(path, 0o000)
        scenarios = load_scenarios_from_corrections(temp_dir)
        assert scenarios == []
        os.chmod(path, 0o644)


class TestQueryModel:
    def test_handles_missing_ollama(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        result = query_model("test", "hello")
        assert result == ""

    def test_handles_timeout(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("ollama", 30)
        monkeypatch.setattr(subprocess, "run", mock_run)
        result = query_model("test", "hello")
        assert result == ""

    def test_handles_failed_command(self, monkeypatch):
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error")
        monkeypatch.setattr(subprocess, "run", mock_run)
        result = query_model("test", "hello")
        assert result == ""

    def test_returns_response(self, monkeypatch):
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="use list comprehension\n", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)
        result = query_model("test", "hello")
        assert result == "use list comprehension"


class TestScoreResponse:
    def test_perfect_match(self):
        assert score_response("use list comprehension", "use list comprehension") == 1.0

    def test_partial_match(self):
        score = score_response("use a list instead", "use list comprehension instead of for loop")
        assert 0 < score < 1.0

    def test_no_match(self):
        assert score_response("completely different text", "use list comprehension") == 0.0

    def test_empty_response(self):
        assert score_response("", "expected") == 0.0

    def test_empty_expected(self):
        assert score_response("response", "") == 0.0

    def test_both_empty(self):
        assert score_response("", "") == 0.0

    def test_whitespace_expected(self):
        assert score_response("response", "   ") == 0.0


class TestEvaluateModel:
    def test_evaluates_with_responses(self, monkeypatch):
        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="use list comprehension instead\n", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)

        scenarios = [
            EvaluationScenario("test prompt", "use list comprehension instead of for loop", "self_correction", "build-py"),
        ]
        result = evaluate_model("test-model", scenarios)
        assert result.total_scenarios == 1
        assert result.passed >= 0
        assert result.avg_score > 0

    def test_evaluates_with_errors(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)

        scenarios = [
            EvaluationScenario("test", "expected", "cat", "mode"),
        ]
        result = evaluate_model("test-model", scenarios)
        assert result.errors == 1
        assert result.passed == 0

    def test_empty_scenarios(self, monkeypatch):
        result = evaluate_model("test-model", [])
        assert result.total_scenarios == 0
        assert result.avg_score == 0.0


class TestRunEvaluation:
    def test_full_pipeline(self, temp_dir, monkeypatch):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write(make_correction() + "\n")

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="list comprehension for loop\n", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)

        result = run_evaluation(["model-a", "model-b"], temp_dir)
        assert result["total_scenarios"] == 1
        assert result["models_evaluated"] == 2
        assert len(result["evaluations"]) == 2
        assert result["best_model"] is not None

    def test_no_scenarios(self, temp_dir):
        result = run_evaluation(["model-a"], temp_dir)
        assert "error" in result

    def test_default_dir(self, temp_dir, monkeypatch):
        monkeypatch.setenv("HOME", temp_dir)
        ref_dir = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(ref_dir)
        result = run_evaluation(["model-a"])
        assert "error" in result  # No corrections in empty dir


class TestCLI:
    def test_cli_with_models(self, temp_dir, monkeypatch, capsys):
        ref_dir = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(ref_dir)
        with open(os.path.join(ref_dir, "test.jsonl"), "w") as f:
            f.write(make_correction() + "\n")
        monkeypatch.setenv("HOME", temp_dir)
        monkeypatch.setattr("sys.argv", ["model_auto_evaluate", "model-a"])

        def mock_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="list comprehension\n", stderr="")
        monkeypatch.setattr(subprocess, "run", mock_run)

        main()
        captured = capsys.readouterr()
        assert "Evaluated" in captured.out

    def test_cli_no_args(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["model_auto_evaluate"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_cli_no_scenarios(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setenv("HOME", temp_dir)
        ref_dir = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(ref_dir)
        monkeypatch.setattr("sys.argv", ["model_auto_evaluate", "model-a"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "No correction scenarios" in captured.out
