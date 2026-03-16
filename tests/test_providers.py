import tempfile
import unittest
from pathlib import Path

from lib.models import SetupEntry
from lib.providers import CommandRunner, ProviderExecutor


class ProvidersTests(unittest.TestCase):
    def test_shell_provider_runs_commands_in_single_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "value.txt"
            runner = CommandRunner(env={"TARGET_FILE": str(path)})
            executor = ProviderExecutor(runner=runner)
            entry = SetupEntry(
                name="shell-persistence",
                provider="shell",
                target=(
                    'VALUE="persisted"',
                    'printf "%s" "$VALUE" > "$TARGET_FILE"',
                ),
                os_targets=("linux",),
                tags=("all",),
            )

            executor.execute(entry)
            self.assertEqual("persisted", path.read_text(encoding="utf-8"))

    def test_runtime_rejects_unknown_provider(self) -> None:
        executor = ProviderExecutor(runner=CommandRunner(env={}))
        entry = SetupEntry(
            name="bad-runtime",
            provider="unknown",
            target=("echo nope",),
            os_targets=("linux",),
            tags=("all",),
        )
        with self.assertRaisesRegex(RuntimeError, "Unsupported provider"):
            executor.execute(entry)

    def test_function_provider_runs_imported_callable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / "function.txt"
            runner = CommandRunner(env={"FUNCTION_MARKER_FILE": str(marker)})
            executor = ProviderExecutor(runner=runner)
            entry = SetupEntry(
                name="function-task",
                provider="function",
                target="tests.helpers:write_helper_marker",
                os_targets=("linux",),
                tags=("all",),
            )

            executor.execute(entry)
            self.assertEqual("helper-ran", marker.read_text(encoding="utf-8"))

    def test_function_provider_runs_direct_callable(self) -> None:
        called: list[str] = []

        def callback() -> None:
            called.append("ok")

        executor = ProviderExecutor(runner=CommandRunner(env={}))
        entry = SetupEntry(
            name="function-direct",
            provider="function",
            target=callback,
            os_targets=("linux",),
            tags=("all",),
        )

        executor.execute(entry)
        self.assertEqual(["ok"], called)
