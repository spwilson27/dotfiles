import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.osinfo import detect_current_os, os_matches, validate_os_override


class OsInfoTests(unittest.TestCase):
    def test_os_matches_linux_generically(self) -> None:
        self.assertTrue(os_matches("linux", "linux-ubuntu"))
        self.assertTrue(os_matches("linux", "linux-arch"))
        self.assertFalse(os_matches("linux-ubuntu", "linux-arch"))
        self.assertFalse(os_matches("macos", "linux-ubuntu"))

    def test_validate_os_override_rejects_unknown_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported OS override"):
            validate_os_override("windows")

    def test_detect_current_os_ubuntu(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            os_release = Path(temp_dir) / "os-release"
            os_release.write_text('ID=ubuntu\nID_LIKE=debian\n', encoding="utf-8")
            with patch("platform.system", return_value="Linux"):
                with patch("lib.osinfo.Path", return_value=os_release):
                    self.assertEqual("linux-ubuntu", detect_current_os())

    def test_detect_current_os_arch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            os_release = Path(temp_dir) / "os-release"
            os_release.write_text('ID=arch\nID_LIKE=archlinux\n', encoding="utf-8")
            with patch("platform.system", return_value="Linux"):
                with patch("lib.osinfo.Path", return_value=os_release):
                    self.assertEqual("linux-arch", detect_current_os())
