"""Tests for preflight_validator.py — TDD, written before implementation."""

import json
import stat
import textwrap
from pathlib import Path

import pytest

from scripts.lib.preflight_validator import validate_script, ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_script(tmp_path: Path, name: str, content: str) -> Path:
    """Write a script file and return its path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


VALID_LOW = """\
    #!/bin/bash
    ################################################################################
    # Name: good-low
    # Risk: low
    # Created: 2026-03-05
    # Status: session
    # Description: Lists files
    ################################################################################
    set -euo pipefail
    main() {
        ls -la
    }
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        main "$@"
    fi
"""

VALID_MEDIUM = """\
    #!/bin/bash
    ################################################################################
    # Name: good-med
    # Risk: medium
    # Created: 2026-03-05
    # Status: session
    # Description: Edits a config
    ################################################################################
    set -euo pipefail
    DRY_RUN="${DRY_RUN:-0}"
    main() {
        if [[ "$DRY_RUN" == "1" ]]; then
            echo "Would edit config"
        else
            echo "new" > ./config.txt
        fi
    }
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        main "$@"
    fi
"""

VALID_HIGH = """\
    #!/bin/bash
    ################################################################################
    # Name: good-high
    # Risk: high
    # Created: 2026-03-05
    # Status: session
    # Description: Deploys the app
    ################################################################################
    set -euo pipefail
    DRY_RUN="${DRY_RUN:-0}"
    main() {
        if [[ "$DRY_RUN" == "1" ]]; then
            echo "Would deploy"
        fi
    }
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        main "$@"
    fi
"""


# ---------------------------------------------------------------------------
# ValidationResult structure
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_pass_result(self):
        r = ValidationResult(passed=True, errors=[], script_path="/x.sh")
        assert r.passed is True
        assert r.errors == []

    def test_fail_result(self):
        r = ValidationResult(passed=False, errors=["bad"], script_path="/x.sh")
        assert r.passed is False
        assert "bad" in r.errors

    def test_to_dict(self):
        r = ValidationResult(passed=True, errors=[], script_path="/x.sh")
        d = r.to_dict()
        assert d["passed"] is True
        assert d["script_path"] == "/x.sh"
        assert d["errors"] == []

    def test_to_json(self):
        r = ValidationResult(passed=True, errors=[], script_path="/x.sh")
        j = json.loads(r.to_json())
        assert j["passed"] is True


# ---------------------------------------------------------------------------
# Valid scripts pass
# ---------------------------------------------------------------------------

class TestValidScripts:
    def test_valid_low_risk(self, tmp_path):
        p = make_script(tmp_path, "good-low.sh", VALID_LOW)
        r = validate_script(str(p))
        assert r.passed is True, r.errors

    def test_valid_medium_risk(self, tmp_path):
        p = make_script(tmp_path, "good-med.sh", VALID_MEDIUM)
        r = validate_script(str(p))
        assert r.passed is True, r.errors

    def test_valid_high_risk(self, tmp_path):
        p = make_script(tmp_path, "good-high.sh", VALID_HIGH)
        r = validate_script(str(p))
        assert r.passed is True, r.errors


# ---------------------------------------------------------------------------
# Check 1: Risk vs. destructive operations
# ---------------------------------------------------------------------------

class TestRiskClassification:
    def test_low_risk_with_rm_rejected(self, tmp_path):
        p = make_script(tmp_path, "bad.sh", VALID_LOW.replace("ls -la", "rm -rf ./build"))
        r = validate_script(str(p))
        assert r.passed is False
        assert any("destructive" in e.lower() for e in r.errors)

    def test_low_risk_with_delete_rejected(self, tmp_path):
        content = VALID_LOW.replace("ls -la", "delete_old_data")
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("destructive" in e.lower() for e in r.errors)

    def test_low_risk_with_drop_rejected(self, tmp_path):
        content = VALID_LOW.replace("ls -la", 'psql -c "drop table users"')
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("destructive" in e.lower() for e in r.errors)

    def test_medium_risk_with_rm_allowed(self, tmp_path):
        content = VALID_MEDIUM.replace(
            'echo "new" > ./config.txt',
            "rm -rf ./build"
        )
        p = make_script(tmp_path, "ok.sh", content)
        r = validate_script(str(p))
        assert r.passed is True, r.errors

    def test_rm_in_comment_not_flagged(self, tmp_path):
        content = VALID_LOW.replace(
            "ls -la",
            "# we used to rm files here\n    echo safe"
        )
        p = make_script(tmp_path, "ok.sh", content)
        r = validate_script(str(p))
        assert r.passed is True, r.errors


# ---------------------------------------------------------------------------
# Check 2: DRY_RUN support
# ---------------------------------------------------------------------------

class TestDryRunSupport:
    def test_medium_without_dryrun_rejected(self, tmp_path):
        content = """\
            #!/bin/bash
            ################################################################################
            # Name: no-dryrun
            # Risk: medium
            # Created: 2026-03-05
            # Status: session
            # Description: Edits a file without safety
            ################################################################################
            set -euo pipefail
            main() {
                echo "edit" > ./file.txt
            }
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                main "$@"
            fi
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("DRY_RUN" in e for e in r.errors)

    def test_high_without_dryrun_rejected(self, tmp_path):
        content = """\
            #!/bin/bash
            ################################################################################
            # Name: no-dryrun-high
            # Risk: high
            # Created: 2026-03-05
            # Status: session
            # Description: Deploys without safety
            ################################################################################
            set -euo pipefail
            main() {
                echo "deploy"
            }
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                main "$@"
            fi
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("DRY_RUN" in e for e in r.errors)

    def test_low_without_dryrun_allowed(self, tmp_path):
        p = make_script(tmp_path, "ok.sh", VALID_LOW)
        r = validate_script(str(p))
        assert r.passed is True


# ---------------------------------------------------------------------------
# Check 3: Template compliance
# ---------------------------------------------------------------------------

class TestTemplateCompliance:
    def test_missing_pipefail_rejected(self, tmp_path):
        content = VALID_LOW.replace("set -euo pipefail", "")
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("set -euo pipefail" in e for e in r.errors)

    def test_missing_main_rejected(self, tmp_path):
        content = """\
            #!/bin/bash
            ################################################################################
            # Name: no-main
            # Risk: low
            # Created: 2026-03-05
            # Status: session
            # Description: No main function
            ################################################################################
            set -euo pipefail
            echo "hello"
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("main" in e.lower() for e in r.errors)

    def test_missing_header_rejected(self, tmp_path):
        content = """\
            #!/bin/bash
            set -euo pipefail
            main() { echo "hello"; }
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("Risk" in e for e in r.errors)

    def test_missing_shebang_rejected(self, tmp_path):
        content = VALID_LOW.lstrip().replace("#!/bin/bash\n", "")
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("shebang" in e.lower() for e in r.errors)


# ---------------------------------------------------------------------------
# Check 4: Path containment
# ---------------------------------------------------------------------------

class TestPathContainment:
    def test_write_to_absolute_root_rejected(self, tmp_path):
        content = VALID_MEDIUM.replace(
            'echo "new" > ./config.txt',
            'echo "bad" > /etc/passwd'
        )
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("path" in e.lower() or "root" in e.lower() or "outside" in e.lower() for e in r.errors)

    def test_append_to_absolute_root_rejected(self, tmp_path):
        content = VALID_MEDIUM.replace(
            'echo "new" > ./config.txt',
            'echo "bad" >> /etc/hosts'
        )
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("path" in e.lower() or "root" in e.lower() or "outside" in e.lower() for e in r.errors)

    def test_write_to_relative_path_allowed(self, tmp_path):
        p = make_script(tmp_path, "ok.sh", VALID_MEDIUM)
        r = validate_script(str(p))
        assert r.passed is True


# ---------------------------------------------------------------------------
# Check 5: Multi-file writes need transaction
# ---------------------------------------------------------------------------

class TestTransactionRequirement:
    def test_multi_file_without_transaction_rejected(self, tmp_path):
        content = """\
            #!/bin/bash
            ################################################################################
            # Name: multi-no-tx
            # Risk: medium
            # Created: 2026-03-05
            # Status: session
            # Description: Multi-file without transaction
            ################################################################################
            set -euo pipefail
            DRY_RUN="${DRY_RUN:-0}"
            main() {
                echo "a" > ./file1.txt
                echo "b" > ./file2.txt
                echo "c" > ./file3.txt
            }
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                main "$@"
            fi
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("transaction" in e.lower() for e in r.errors)

    def test_multi_file_with_transaction_allowed(self, tmp_path):
        content = """\
            #!/bin/bash
            ################################################################################
            # Name: multi-tx
            # Risk: high
            # Created: 2026-03-05
            # Status: session
            # Description: Multi-file transaction
            ################################################################################
            set -euo pipefail
            DRY_RUN="${DRY_RUN:-0}"
            TRANSACTION_STEPS=(
                "step_one"
                "step_two"
            )
            step_one() { echo "a" > ./file1.txt; }
            step_two() { echo "b" > ./file2.txt; }
            rollback() { git checkout .; }
            main() {
                for step in "${TRANSACTION_STEPS[@]}"; do
                    if ! $step; then rollback; return 1; fi
                done
            }
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                main "$@"
            fi
        """
        p = make_script(tmp_path, "ok.sh", content)
        r = validate_script(str(p))
        assert r.passed is True, r.errors

    def test_single_redirect_not_flagged(self, tmp_path):
        p = make_script(tmp_path, "ok.sh", VALID_MEDIUM)
        r = validate_script(str(p))
        assert r.passed is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_nonexistent_file(self):
        r = validate_script("/tmp/nonexistent_crux_test.sh")
        assert r.passed is False
        assert any("not found" in e.lower() or "does not exist" in e.lower() for e in r.errors)

    def test_multiple_failures_reported(self, tmp_path):
        content = """\
            # no shebang, no header, no pipefail, no main
            echo "bad" > /etc/thing
        """
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert len(r.errors) >= 2  # Should collect multiple errors

    def test_result_json_roundtrip(self, tmp_path):
        p = make_script(tmp_path, "ok.sh", VALID_LOW)
        r = validate_script(str(p))
        d = json.loads(r.to_json())
        assert d["passed"] is True
        assert d["script_path"] == str(p)

    def test_invalid_risk_level(self, tmp_path):
        content = VALID_LOW.replace("# Risk: low", "# Risk: extreme")
        p = make_script(tmp_path, "bad.sh", content)
        r = validate_script(str(p))
        assert r.passed is False
        assert any("extreme" in e for e in r.errors)

    def test_inline_comment_stripped(self, tmp_path):
        content = VALID_LOW.replace("ls -la", "echo safe  # rm dangerous stuff")
        p = make_script(tmp_path, "ok.sh", content)
        r = validate_script(str(p))
        assert r.passed is True  # rm is in inline comment, not executable


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_pass(self, tmp_path, monkeypatch, capsys):
        from scripts.lib.preflight_validator import main as cli_main
        p = make_script(tmp_path, "ok.sh", VALID_LOW)
        monkeypatch.setattr("sys.argv", ["preflight_validator", str(p)])
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 0
        assert "PASS" in capsys.readouterr().out

    def test_cli_fail(self, tmp_path, monkeypatch, capsys):
        from scripts.lib.preflight_validator import main as cli_main
        content = """\
            # no shebang
            echo "bad"
        """
        p = make_script(tmp_path, "bad.sh", content)
        monkeypatch.setattr("sys.argv", ["preflight_validator", str(p)])
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        assert "FAIL" in capsys.readouterr().out

    def test_cli_no_args(self, monkeypatch, capsys):
        from scripts.lib.preflight_validator import main as cli_main
        monkeypatch.setattr("sys.argv", ["preflight_validator"])
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr().out
        assert "Usage" in captured or "usage" in captured

    def test_cli_json_output(self, tmp_path, monkeypatch, capsys):
        from scripts.lib.preflight_validator import main as cli_main
        p = make_script(tmp_path, "ok.sh", VALID_LOW)
        monkeypatch.setattr("sys.argv", ["preflight_validator", "--json", str(p)])
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 0
        d = json.loads(capsys.readouterr().out)
        assert d["passed"] is True

    def test_cli_json_fail(self, tmp_path, monkeypatch, capsys):
        from scripts.lib.preflight_validator import main as cli_main
        content = """\
            # no shebang
            echo "bad"
        """
        p = make_script(tmp_path, "bad.sh", content)
        monkeypatch.setattr("sys.argv", ["preflight_validator", "--json", str(p)])
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1
        d = json.loads(capsys.readouterr().out)
        assert d["passed"] is False
