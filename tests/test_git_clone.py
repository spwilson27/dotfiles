import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.models import SetupEntry
from lib.providers import CommandRunner, ProviderExecutor
from lib.config_loader import parse_entry


class GitCloneProviderTests(unittest.TestCase):
    def test_git_clone_clones_repo_to_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a local bare repo to clone from
            src = Path(temp_dir) / "source.git"
            dest = Path(temp_dir) / "cloned"

            runner = CommandRunner(env=os.environ.copy())
            # Init a bare repo as clone source
            runner.run(["git", "init", "--bare", str(src)])

            executor = ProviderExecutor(runner=runner)
            entry = SetupEntry(
                name="clone-test",
                provider="git_clone",
                target=(str(src), str(dest)),
                os_targets=("linux",),
                tags=("all",),
            )

            executor.execute(entry)
            self.assertTrue(dest.exists())
            self.assertTrue((dest / ".git").exists())

    def test_git_clone_removes_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            src = Path(temp_dir) / "source.git"
            dest = Path(temp_dir) / "cloned"

            runner = CommandRunner(env=os.environ.copy())
            runner.run(["git", "init", "--bare", str(src)])

            # Pre-create destination with a marker file
            dest.mkdir()
            marker = dest / "old-marker.txt"
            marker.write_text("should be removed")

            executor = ProviderExecutor(runner=runner)
            entry = SetupEntry(
                name="clone-replace",
                provider="git_clone",
                target=(str(src), str(dest)),
                os_targets=("linux",),
                tags=("all",),
            )

            executor.execute(entry)
            self.assertTrue(dest.exists())
            self.assertFalse(marker.exists())

    def test_git_clone_expands_user_in_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            src = Path(temp_dir) / "source.git"

            runner = CommandRunner(env=os.environ.copy())
            runner.run(["git", "init", "--bare", str(src)])

            dest_relative = os.path.join(temp_dir, "home-test")
            with patch.dict(os.environ, {"TEST_CLONE_DIR": dest_relative}):
                executor = ProviderExecutor(runner=CommandRunner(env=os.environ.copy()))
                entry = SetupEntry(
                    name="clone-expand",
                    provider="git_clone",
                    target=(str(src), "$TEST_CLONE_DIR"),
                    os_targets=("linux",),
                    tags=("all",),
                )

                executor.execute(entry)
                self.assertTrue(Path(dest_relative).exists())

    def test_git_clone_rejects_wrong_target_length(self) -> None:
        executor = ProviderExecutor(runner=CommandRunner(env={}))
        entry = SetupEntry(
            name="clone-bad",
            provider="git_clone",
            target=("only-one-element",),
            os_targets=("linux",),
            tags=("all",),
        )
        with self.assertRaisesRegex(RuntimeError, "repo_url, destination"):
            executor.execute(entry)

    def test_git_clone_fails_on_invalid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "cloned"
            executor = ProviderExecutor(runner=CommandRunner(env=os.environ.copy()))
            entry = SetupEntry(
                name="clone-fail",
                provider="git_clone",
                target=("/nonexistent/repo", str(dest)),
                os_targets=("linux",),
                tags=("all",),
            )
            with self.assertRaises(RuntimeError):
                executor.execute(entry)


class GitCloneConfigLoaderTests(unittest.TestCase):
    def test_parse_git_clone_entry(self) -> None:
        raw = {
            "name": "nvim-config",
            "provider": "git_clone",
            "target": ["https://github.com/example/repo", "~/.config/nvim"],
            "os": ["linux", "macos"],
            "tags": ["dotfiles"],
        }
        entry = parse_entry(raw, index=0)
        self.assertEqual(entry.provider, "git_clone")
        self.assertEqual(entry.target, ("https://github.com/example/repo", "~/.config/nvim"))

    def test_parse_git_clone_rejects_single_target(self) -> None:
        raw = {
            "name": "bad-clone",
            "provider": "git_clone",
            "target": "just-a-string",
            "os": "linux",
            "tags": "dotfiles",
        }
        # This should parse fine (as_tuple makes it a 1-tuple) - runtime catches the error
        entry = parse_entry(raw, index=0)
        self.assertEqual(len(entry.target), 1)
