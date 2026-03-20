from __future__ import annotations

import argparse

from lib.config_loader import load_config
from lib.selftest import open_docker_shell, run_selftest
from lib.setup_engine import run_setup


def _available_tags() -> list[str]:
    """Collect all unique tags defined across config entries."""
    try:
        entries = load_config()
    except (ValueError, ImportError):
        return []
    tags: set[str] = set()
    for entry in entries:
        tags.update(entry.tags)
    return sorted(tags)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal dotfiles setup runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    available = _available_tags()
    tag_help = "Select one or more tags. Repeat the flag or provide comma-separated values. Defaults to all."
    if available:
        tag_help += f" Available tags: {', '.join(available)}"

    setup_parser = subparsers.add_parser("setup", help="Run setup tasks from config.py")
    setup_parser.add_argument(
        "--os",
        dest="os_override",
        help="Override detected OS (macos, linux, linux-ubuntu, linux-arch)",
    )
    setup_parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        default=None,
        help=tag_help,
    )

    subparsers.add_parser("selftest", help="Run unit tests and Docker-based setup validation")
    docker_parser = subparsers.add_parser(
        "docker",
        help="Build a Linux container image, copy this repo into it, and start an interactive shell",
    )
    docker_parser.add_argument(
        "--image",
        choices=["ubuntu", "arch"],
        default="ubuntu",
        help="Select the Linux container image to open. Defaults to ubuntu.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "setup":
        return run_setup(os_override=args.os_override, tags=args.tags)
    if args.command == "selftest":
        return run_selftest()
    if args.command == "docker":
        return open_docker_shell(args.image)
    parser.error(f"Unsupported command: {args.command}")
    return 2
