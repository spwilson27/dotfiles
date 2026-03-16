import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from lib.models import SetupEntry
from lib.setup_engine import run_setup


class SetupEngineTests(unittest.TestCase):
    def test_run_setup_uses_auto_detected_os_when_no_override_is_provided(self) -> None:
        entries = [
            SetupEntry(
                name="generic-linux",
                provider="shell",
                target=("echo generic",),
                os_targets=("linux",),
                tags=("all",),
            ),
            SetupEntry(
                name="ubuntu-only",
                provider="shell",
                target=("echo ubuntu",),
                os_targets=("linux-ubuntu",),
                tags=("all",),
            ),
            SetupEntry(
                name="arch-only",
                provider="shell",
                target=("echo arch",),
                os_targets=("linux-arch",),
                tags=("all",),
            ),
        ]
        executed_entries: list[str] = []

        class FakeExecutor:
            def execute(self, entry: SetupEntry) -> None:
                executed_entries.append(entry.name)

        with patch("lib.setup_engine.detect_current_os", return_value="linux-ubuntu"):
            with patch("lib.setup_engine.load_config", return_value=entries):
                with patch("lib.setup_engine.ProviderExecutor", return_value=FakeExecutor()):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        exit_code = run_setup()

        self.assertEqual(0, exit_code)
        self.assertEqual(["generic-linux", "ubuntu-only"], executed_entries)
        self.assertIn("[info] selected OS: linux-ubuntu", output.getvalue())
