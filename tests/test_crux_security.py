"""Tests for crux_security.py — closing coverage gaps."""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestValidatePathWithinBase:
    """Tests for validate_path_within_base."""

    def test_resolve_raises_value_error(self, tmp_path):
        """Lines 49-50: except (ValueError, OSError) branch."""
        from scripts.lib.crux_security import validate_path_within_base

        path = MagicMock(spec=Path)
        path.resolve.side_effect = ValueError("cannot compute")
        assert validate_path_within_base(path, tmp_path) is False

    def test_resolve_raises_os_error(self, tmp_path):
        """Lines 49-50: OSError variant."""
        from scripts.lib.crux_security import validate_path_within_base

        path = MagicMock(spec=Path)
        path.resolve.side_effect = OSError("permission denied")
        assert validate_path_within_base(path, tmp_path) is False


class TestSafeGlobFiles:
    """Tests for safe_glob_files."""

    def test_not_a_directory(self, tmp_path):
        """Line 64: return [] when directory is not a dir."""
        from scripts.lib.crux_security import safe_glob_files

        # Pass a file path, not a directory
        f = tmp_path / "afile.txt"
        f.write_text("hello")
        result = safe_glob_files(f, "*.txt")
        assert result == []

    def test_nonexistent_directory(self, tmp_path):
        """Line 64: return [] for nonexistent path."""
        from scripts.lib.crux_security import safe_glob_files

        result = safe_glob_files(tmp_path / "nope", "*.txt")
        assert result == []

    def test_skips_symlinks(self, tmp_path):
        """Line 72: continue on symlink."""
        from scripts.lib.crux_security import safe_glob_files

        real_file = tmp_path / "real.md"
        real_file.write_text("content")
        link = tmp_path / "link.md"
        link.symlink_to(real_file)

        result = safe_glob_files(tmp_path, "*.md")
        # Only the real file should be returned, not the symlink
        assert len(result) == 1
        assert result[0].name == "real.md"

    def test_skips_path_outside_base(self, tmp_path):
        """Line 75: continue when resolved path is outside base."""
        from scripts.lib.crux_security import safe_glob_files

        # Create a file outside the base directory
        outside = tmp_path / "outside"
        outside.mkdir()
        outside_file = outside / "secret.md"
        outside_file.write_text("secret")

        # Create a subdir that we'll glob from
        inside = tmp_path / "inside"
        inside.mkdir()
        inside_file = inside / "safe.md"
        inside_file.write_text("safe")

        # Create a symlink from inside to outside (but symlinks are already
        # filtered by line 72). To hit line 75, we need validate_path_within_base
        # to return False for a non-symlink. Mock it.
        with patch("scripts.lib.crux_security.validate_path_within_base") as mock_validate:
            # First call returns False (skipped), second returns True (kept)
            mock_validate.side_effect = [False, True]
            # Add another file so glob returns two items
            another = inside / "also.md"
            another.write_text("also")
            result = safe_glob_files(inside, "*.md")
            assert len(result) == 1


class TestAtomicSymlink:
    """Tests for atomic_symlink."""

    def test_rename_oserror_cleans_up(self, tmp_path):
        """Lines 105-111: except OSError branch + cleanup."""
        from scripts.lib.crux_security import atomic_symlink

        source = str(tmp_path / "source")
        target = str(tmp_path / "target_link")

        with patch("scripts.lib.crux_security.os.rename", side_effect=OSError("rename failed")):
            with pytest.raises(OSError, match="rename failed"):
                atomic_symlink(source, target)

    def test_rename_oserror_cleanup_also_fails(self, tmp_path):
        """Lines 107-110: inner except OSError on os.unlink."""
        from scripts.lib.crux_security import atomic_symlink

        source = str(tmp_path / "source")
        target = str(tmp_path / "target_link")

        original_unlink = os.unlink
        call_count = 0

        def unlink_side_effect(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (line 100): let it succeed (removes temp file)
                return original_unlink(path)
            else:
                # Second call (line 108 in except): fail
                raise OSError("unlink failed")

        with patch("scripts.lib.crux_security.os.rename", side_effect=OSError("rename failed")):
            with patch("scripts.lib.crux_security.os.unlink", side_effect=unlink_side_effect):
                with pytest.raises(OSError, match="rename failed"):
                    atomic_symlink(source, target)


class TestSecureWriteFile:
    """Tests for secure_write_file."""

    def test_write_exception_cleans_up(self, tmp_path):
        """Lines 146-152: except Exception branch + temp file cleanup."""
        from scripts.lib.crux_security import secure_write_file

        target = str(tmp_path / "output.txt")

        with patch("scripts.lib.crux_security.os.fchmod", side_effect=PermissionError("fchmod failed")):
            with pytest.raises(PermissionError, match="fchmod failed"):
                secure_write_file(target, "content")

        # Temp file should have been cleaned up
        remaining = list(tmp_path.glob(".crux_write_*"))
        assert len(remaining) == 0

    def test_write_exception_cleanup_oserror(self, tmp_path):
        """Lines 148-151: inner os.unlink OSError during cleanup."""
        from scripts.lib.crux_security import secure_write_file

        target = str(tmp_path / "output.txt")

        # os.write raises, then os.unlink also raises during cleanup
        original_write = os.write

        def mock_write(fd, data):
            raise IOError("write failed")

        with patch("scripts.lib.crux_security.os.write", side_effect=IOError("write failed")):
            with patch("scripts.lib.crux_security.os.unlink", side_effect=OSError("unlink failed")):
                with pytest.raises(IOError, match="write failed"):
                    secure_write_file(target, "content")


class TestValidateAndCanonicalizeDir:
    """Tests for validate_and_canonicalize_dir."""

    def test_not_a_directory(self, tmp_path):
        """Line 189: return None when path is a file, not a dir."""
        from scripts.lib.crux_security import validate_and_canonicalize_dir

        f = tmp_path / "afile.txt"
        f.write_text("hello")
        assert validate_and_canonicalize_dir(str(f)) is None

    def test_oserror_returns_none(self):
        """Lines 187-188: except (OSError, ValueError) branch."""
        from scripts.lib.crux_security import validate_and_canonicalize_dir

        with patch("scripts.lib.crux_security.os.path.realpath", side_effect=OSError("bad")):
            assert validate_and_canonicalize_dir("/some/path") is None

    def test_value_error_returns_none(self):
        """Lines 187-188: ValueError variant."""
        from scripts.lib.crux_security import validate_and_canonicalize_dir

        with patch("scripts.lib.crux_security.os.path.realpath", side_effect=ValueError("bad")):
            assert validate_and_canonicalize_dir("/some/path") is None
