"""Tests for audit_modes.py — mode prompt audit against design rules."""

import os
import tempfile

import pytest

from scripts.lib.audit_modes import (
    ModeAuditResult,
    audit_all_modes,
    audit_mode_file,
    check_persona,
    count_words,
    find_negative_phrases,
    main,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def write_mode(temp_dir, name, content):
    path = os.path.join(temp_dir, f"{name}.md")
    with open(path, "w") as f:
        f.write(content)
    return path


# Create a prompt that's exactly in the target range (150-200 words)
GOOD_PROMPT = "# Build Python\n\n" + "You are an expert Python developer. " + " ".join(["word"] * 155) + "\n"
SHORT_PROMPT = "# Short\n\nYou are a helper. Do things.\n"
LONG_PROMPT = "# Long\n\nYou are an expert. " + " ".join(["word"] * 210) + "\n"
NEGATIVE_PROMPT = "# Negative\n\nYou are an expert. Don't use globals. Never repeat yourself. Avoid complexity. " + " ".join(["word"] * 150) + "\n"
NO_PERSONA_PROMPT = "# Plain Mode\n\n" + " ".join(["focus"] * 160) + "\n"


class TestCountWords:
    def test_counts_text_words(self):
        assert count_words("hello world foo bar") == 4

    def test_skips_headers(self):
        assert count_words("# Header\n\nhello world") == 2

    def test_skips_empty_lines(self):
        assert count_words("hello\n\nworld") == 2

    def test_empty_content(self):
        assert count_words("") == 0

    def test_only_headers(self):
        assert count_words("# Header\n## Sub") == 0


class TestFindNegativePhrases:
    def test_finds_dont(self):
        result = find_negative_phrases("Don't use globals")
        assert len(result) >= 1

    def test_finds_never(self):
        result = find_negative_phrases("Never repeat code")
        assert any("never" in r.lower() for r in result)

    def test_finds_avoid(self):
        result = find_negative_phrases("Avoid complexity")
        assert any("avoid" in r.lower() for r in result)

    def test_no_negatives(self):
        result = find_negative_phrases("Use clear variable names")
        assert result == []

    def test_finds_do_not(self):
        result = find_negative_phrases("Do not modify production files")
        assert len(result) >= 1


class TestCheckPersona:
    def test_finds_you_are(self):
        assert check_persona("You are an expert Python developer") is True

    def test_finds_your_role(self):
        assert check_persona("Your role is to review code") is True

    def test_finds_as_a(self):
        assert check_persona("As a security expert, review this") is True

    def test_finds_specialist(self):
        assert check_persona("A debugging specialist focused on root cause") is True

    def test_no_persona(self):
        assert check_persona("Review the code and find bugs") is False


class TestModeAuditResult:
    def test_to_dict(self):
        r = ModeAuditResult(
            mode="build-py", file_path="/modes/build-py.md",
            word_count=175, word_count_ok=True, has_persona=True,
        )
        d = r.to_dict()
        assert d["mode"] == "build-py"
        assert d["word_count_ok"] is True


class TestAuditModeFile:
    def test_good_prompt(self, temp_dir):
        path = write_mode(temp_dir, "build-py", GOOD_PROMPT)
        result = audit_mode_file(path)
        assert result.word_count_ok is True
        assert result.positive_framing_ok is True
        assert result.has_persona is True
        assert result.issues == []

    def test_short_prompt(self, temp_dir):
        path = write_mode(temp_dir, "short", SHORT_PROMPT)
        result = audit_mode_file(path)
        assert result.word_count_ok is False
        assert any("below" in i for i in result.issues)

    def test_long_prompt(self, temp_dir):
        path = write_mode(temp_dir, "long", LONG_PROMPT)
        result = audit_mode_file(path)
        assert result.word_count_ok is False
        assert any("exceeds" in i for i in result.issues)

    def test_negative_framing(self, temp_dir):
        path = write_mode(temp_dir, "negative", NEGATIVE_PROMPT)
        result = audit_mode_file(path)
        assert result.positive_framing_ok is False
        assert len(result.negative_phrases) >= 3

    def test_no_persona(self, temp_dir):
        path = write_mode(temp_dir, "nopersona", NO_PERSONA_PROMPT)
        result = audit_mode_file(path)
        assert result.has_persona is False
        assert any("persona" in i.lower() for i in result.issues)


class TestAuditAllModes:
    def test_audits_all_files(self, temp_dir):
        write_mode(temp_dir, "build-py", GOOD_PROMPT)
        write_mode(temp_dir, "debug", SHORT_PROMPT)
        result = audit_all_modes(temp_dir)
        assert result["total_modes"] == 2
        assert result["passing"] == 1
        assert result["failing"] == 1

    def test_skips_template(self, temp_dir):
        write_mode(temp_dir, "_template", "# Template\n\nSkip me\n")
        write_mode(temp_dir, "build-py", GOOD_PROMPT)
        result = audit_all_modes(temp_dir)
        assert result["total_modes"] == 1

    def test_handles_missing_dir(self):
        result = audit_all_modes("/nonexistent/modes")
        assert result["total_modes"] == 0

    def test_default_dir(self, temp_dir, monkeypatch):
        modes_dir = os.path.join(temp_dir, "modes")
        os.makedirs(modes_dir)
        write_mode(modes_dir, "test", GOOD_PROMPT)
        monkeypatch.chdir(temp_dir)
        result = audit_all_modes()
        assert result["total_modes"] == 1


class TestCLI:
    def test_cli_all_pass(self, temp_dir, monkeypatch, capsys):
        write_mode(temp_dir, "build-py", GOOD_PROMPT)
        monkeypatch.setattr("sys.argv", ["audit_modes", temp_dir])
        main()
        captured = capsys.readouterr()
        assert "1/1 passing" in captured.out
        assert "[PASS]" in captured.out

    def test_cli_with_failures(self, temp_dir, monkeypatch, capsys):
        write_mode(temp_dir, "bad", SHORT_PROMPT)
        monkeypatch.setattr("sys.argv", ["audit_modes", temp_dir])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.out

    def test_cli_default_dir(self, temp_dir, monkeypatch, capsys):
        modes_dir = os.path.join(temp_dir, "modes")
        os.makedirs(modes_dir)
        write_mode(modes_dir, "test", GOOD_PROMPT)
        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr("sys.argv", ["audit_modes"])
        main()
        captured = capsys.readouterr()
        assert "1/1 passing" in captured.out
