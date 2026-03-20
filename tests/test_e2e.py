"""End-to-end tests that verify setup actually copied files to the right places.

These tests are meant to run inside a docker container AFTER ./run.py setup --tag dotfiles.
"""

import os
import unittest
from pathlib import Path

from config import CopyFiles, CopyDirs, config


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path)))


class TestFilesWereCopied(unittest.TestCase):
    """Verify that every file/dir referenced in config was actually placed at its destination."""

    def test_copy_files_destinations_exist(self):
        missing = []
        for entry in config:
            if not isinstance(entry, CopyFiles):
                continue
            for pair in entry.files:
                dst = _expand(pair[1])
                if not dst.exists():
                    missing.append(str(dst))
        self.assertFalse(missing, f"Expected files not found after setup: {missing}")

    def test_copy_dirs_destinations_exist(self):
        missing = []
        for entry in config:
            if not isinstance(entry, CopyDirs):
                continue
            for pair in entry.dirs:
                dst = _expand(pair[1])
                if not dst.exists():
                    missing.append(str(dst))
        self.assertFalse(missing, f"Expected directories not found after setup: {missing}")

    def test_copied_files_are_not_empty(self):
        empty = []
        for entry in config:
            if not isinstance(entry, CopyFiles):
                continue
            for pair in entry.files:
                dst = _expand(pair[1])
                if dst.exists() and dst.stat().st_size == 0:
                    empty.append(str(dst))
        self.assertFalse(empty, f"Copied files are unexpectedly empty: {empty}")
