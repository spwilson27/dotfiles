import unittest

from lib.cli import build_parser


class CliTests(unittest.TestCase):
    def test_docker_command_defaults_to_ubuntu(self) -> None:
        args = build_parser().parse_args(["docker"])
        self.assertEqual("docker", args.command)
        self.assertEqual("ubuntu", args.image)

    def test_docker_command_accepts_arch_image(self) -> None:
        args = build_parser().parse_args(["docker", "--image", "arch"])
        self.assertEqual("docker", args.command)
        self.assertEqual("arch", args.image)
