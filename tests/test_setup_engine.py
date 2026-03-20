import unittest
from pathlib import Path
from unittest.mock import patch

from config import Shell, CopyFiles, CopyDirs, CopySecretFiles, Runner, config
from run import run_setup, os_matches


class TestOsMatches(unittest.TestCase):
    def test_linux_matches_linux_ubuntu(self):
        self.assertTrue(os_matches("linux", "linux-ubuntu"))

    def test_linux_matches_linux_arch(self):
        self.assertTrue(os_matches("linux", "linux-arch"))

    def test_linux_matches_linux(self):
        self.assertTrue(os_matches("linux", "linux"))

    def test_macos_does_not_match_linux(self):
        self.assertFalse(os_matches("macos", "linux"))

    def test_exact_match(self):
        self.assertTrue(os_matches("macos", "macos"))


class TestRunSetup(unittest.TestCase):
    def test_filters_by_os(self):
        test_config = [
            Shell(cmds=["echo linux"], os_=["linux"], tags=[]),
            Shell(cmds=["echo macos"], os_=["macos"], tags=[]),
        ]

        with patch("run.config", test_config):
            run_setup("linux-ubuntu", dry_run=True)

        # Only the linux entry should have been "run" (dry-run prints)

    def test_filters_by_tag(self):
        test_config = [
            Shell(cmds=["echo dev"], os_=["linux"], tags=["dev"]),
            Shell(cmds=["echo prod"], os_=["linux"], tags=["prod"]),
        ]

        with patch("run.config", test_config):
            run_setup("linux-ubuntu", tags={"dev"}, dry_run=True)

    def test_no_os_filter_runs_all(self):
        test_config = [
            Shell(cmds=["echo a"], os_=[], tags=[]),
            Shell(cmds=["echo b"], os_=[], tags=[]),
        ]

        with patch("run.config", test_config):
            result = run_setup("linux-ubuntu", dry_run=True)
        self.assertEqual(0, result)

    def test_runner_dry_run_does_not_execute(self):
        runner = Runner(dry_run=True)
        # Should print but not actually run
        runner.call(["echo", "test"])
        runner.shell("echo test")


class TestAllDotfilesReferenced(unittest.TestCase):
    def test_all_dotfiles_in_config(self):
        repo_root = Path(__file__).parent.parent
        dotfiles_dir = repo_root / "dotfiles"

        referenced_sources = set()
        for entry in config:
            if isinstance(entry, (CopyFiles, CopySecretFiles)):
                for pair in entry.files:
                    referenced_sources.add(Path(pair[0]).name)
            elif isinstance(entry, CopyDirs):
                for pair in entry.dirs:
                    referenced_sources.add(Path(pair[0]).name)

        missing = []
        for f in dotfiles_dir.iterdir():
            if f.name not in referenced_sources:
                missing.append(f.name)

        self.assertFalse(
            missing,
            f"Dotfiles not referenced in any config entry: {sorted(missing)}",
        )


class TestCopyFiles(unittest.TestCase):
    def test_copies_src_to_dst(self):
        entry = CopyFiles(files=[["src", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call:
            entry.run(runner)
        calls = [c.args[0] for c in mock_call.call_args_list]
        cp_call = next(c for c in calls if c[0] == "cp")
        self.assertEqual(cp_call[-2], "src")
        self.assertEqual(cp_call[-1], "dst")

    def test_reverse_copies_dst_to_src(self):
        entry = CopyFiles(files=[["src", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call:
            entry.run(runner, reverse=True)
        calls = [c.args[0] for c in mock_call.call_args_list]
        cp_call = next(c for c in calls if c[0] == "cp")
        self.assertEqual(cp_call[-2], "dst")
        self.assertEqual(cp_call[-1], "src")


class TestCopyDirs(unittest.TestCase):
    def test_syncs_src_to_dst(self):
        entry = CopyDirs(dirs=[["src", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call:
            entry.run(runner)
        calls = [c.args[0] for c in mock_call.call_args_list]
        cp_call = next(c for c in calls if c[0] == "cp")
        self.assertEqual(cp_call[-2], "src")
        self.assertEqual(cp_call[-1], "dst")

    def test_reverse_syncs_dst_to_src(self):
        entry = CopyDirs(dirs=[["src", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call:
            entry.run(runner, reverse=True)
        calls = [c.args[0] for c in mock_call.call_args_list]
        cp_call = next(c for c in calls if c[0] == "cp")
        self.assertEqual(cp_call[-2], "dst")
        self.assertEqual(cp_call[-1], "src")


class TestCopySecretFiles(unittest.TestCase):
    def test_decrypts_src_to_dst(self):
        """Normal direction: decrypt from git store to filesystem."""
        entry = CopySecretFiles(files=[["src.gpg", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call, \
             patch.object(runner, "secret_pass", return_value="pass"):
            entry.run(runner, reverse=False)
        calls = [c.args[0] for c in mock_call.call_args_list]
        gpg_call = next(c for c in calls if c[0] == "gpg")
        self.assertIn("--decrypt", gpg_call)
        self.assertEqual(gpg_call[-2], "dst")
        self.assertEqual(gpg_call[-1], "src.gpg")

    def test_reverse_encrypts_dst_to_src(self):
        """Reverse direction: encrypt from filesystem back to git store."""
        entry = CopySecretFiles(files=[["src.gpg", "dst"]], os_=["linux"])
        runner = Runner(dry_run=True)
        with patch.object(runner, "call") as mock_call, \
             patch.object(runner, "secret_pass", return_value="pass"):
            entry.run(runner, reverse=True)
        calls = [c.args[0] for c in mock_call.call_args_list]
        gpg_call = next(c for c in calls if c[0] == "gpg")
        self.assertNotIn("--decrypt", gpg_call)
        self.assertEqual(gpg_call[-2], "src.gpg")
        self.assertEqual(gpg_call[-1], "dst")
