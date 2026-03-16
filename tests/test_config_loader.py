import sys
import tempfile
import unittest
from pathlib import Path

from lib.config_loader import load_config, parse_entry


class ConfigLoaderTests(unittest.TestCase):
    def test_parse_entry_rejects_unknown_provider(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported provider"):
            parse_entry(
                {
                    "name": "bad",
                    "provider": "nope",
                    "target": "thing",
                    "os": "linux",
                    "tags": "all",
                }
            )

    def test_parse_entry_normalizes_scalar_fields(self) -> None:
        entry = parse_entry(
            {
                "name": "shell-task",
                "provider": "shell",
                "target": "echo hello",
                "os": "linux",
                "tags": "all",
            }
        )
        self.assertEqual(("echo hello",), entry.target)
        self.assertEqual(("linux",), entry.os_targets)
        self.assertEqual(("all",), entry.tags)

    def test_parse_entry_accepts_function_provider_import_target(self) -> None:
        entry = parse_entry(
            {
                "name": "function-task",
                "provider": "function",
                "target": "tests.helpers:write_helper_marker",
                "os": "linux",
                "tags": "all",
            }
        )
        self.assertEqual("tests.helpers:write_helper_marker", entry.target)

    def test_parse_entry_rejects_invalid_function_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "module.path:callable_name"):
            parse_entry(
                {
                    "name": "bad-function",
                    "provider": "function",
                    "target": "tests.helpers.write_helper_marker",
                    "os": "linux",
                    "tags": "all",
                }
            )

    def test_load_config_accepts_direct_function_target_from_test_module(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            module_path = temp_path / "temp_function_config.py"
            module_path.write_text(
                "\n".join(
                    [
                        "def callback():",
                        "    return None",
                        "",
                        "CONFIG = [",
                        "    {",
                        '        "name": "function-task",',
                        '        "provider": "function",',
                        '        "target": callback,',
                        '        "os": "linux",',
                        '        "tags": "all",',
                        "    }",
                        "]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            sys.path.insert(0, temp_dir)
            try:
                loaded = load_config("temp_function_config")
            finally:
                sys.path.remove(temp_dir)
                sys.modules.pop("temp_function_config", None)

        self.assertEqual(1, len(loaded))
        self.assertEqual("function", loaded[0].provider)
        self.assertTrue(callable(loaded[0].target))
