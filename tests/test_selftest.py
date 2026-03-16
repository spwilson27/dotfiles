import subprocess
import sys
import unittest
from unittest.mock import call, patch

from lib.selftest import ROOT, _build_test_command, open_docker_shell


class SelftestRunnerTests(unittest.TestCase):
    def test_prefers_pytest_when_available(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/pytest"):
            command = _build_test_command()

        self.assertEqual([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], command)

    def test_falls_back_to_unittest_when_pytest_is_unavailable(self) -> None:
        with patch("shutil.which", return_value=None):
            command = _build_test_command()

        self.assertEqual(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(ROOT / "tests"),
                "-p",
                "test_*.py",
            ],
            command,
        )

    def test_open_docker_shell_builds_copies_starts_and_cleans_up(self) -> None:
        with patch("lib.selftest._ensure_docker_available") as ensure_docker:
            with patch("lib.selftest._build_docker_image") as build_image:
                with patch("lib.selftest._run") as run_command:
                    with patch("lib.selftest.uuid.uuid4") as uuid4:
                        with patch("lib.selftest.subprocess.run") as subprocess_run:
                            uuid4.return_value.hex = "deadbeefcafebabe"
                            subprocess_run.return_value.returncode = 0

                            exit_code = open_docker_shell("ubuntu")

        container_name = "dotfiles-shell-ubuntu-deadbeef"
        self.assertEqual(0, exit_code)
        ensure_docker.assert_called_once_with()
        build_image.assert_called_once()
        self.assertEqual("ubuntu", build_image.call_args.args[0].name)
        run_command.assert_has_calls(
            [
                call(
                    [
                        "docker",
                        "create",
                        "-it",
                        "--name",
                        container_name,
                        "dotfiles-selftest-ubuntu",
                        "/bin/sh",
                        "-lc",
                        "mkdir -p /workspace && cd /workspace && exec /bin/sh",
                    ]
                ),
                call(["docker", "cp", f"{ROOT}/.", f"{container_name}:/workspace"]),
            ]
        )
        subprocess_run.assert_has_calls(
            [
                call(["docker", "start", "-ai", container_name], check=False),
                call(
                    ["docker", "rm", "-f", container_name],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
            ]
        )

    def test_open_docker_shell_cleans_up_after_start_failure(self) -> None:
        with patch("lib.selftest._ensure_docker_available"):
            with patch("lib.selftest._build_docker_image"):
                with patch("lib.selftest._run"):
                    with patch("lib.selftest.uuid.uuid4") as uuid4:
                        with patch("lib.selftest.subprocess.run") as subprocess_run:
                            uuid4.return_value.hex = "12345678abcdef00"
                            subprocess_run.side_effect = [
                                unittest.mock.Mock(returncode=1),
                                unittest.mock.Mock(returncode=0),
                            ]

                            with self.assertRaisesRegex(RuntimeError, "docker start -ai"):
                                open_docker_shell("arch")

        container_name = "dotfiles-shell-arch-12345678"
        subprocess_run.assert_has_calls(
            [
                call(["docker", "start", "-ai", container_name], check=False),
                call(
                    ["docker", "rm", "-f", container_name],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
            ]
        )

    def test_open_docker_shell_rejects_unknown_image(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported docker image"):
            open_docker_shell("fedora")
