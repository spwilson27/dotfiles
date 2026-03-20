#!/usr/bin/env python3

import argparse
import difflib
import os
import signal
import platform
from pathlib import Path

from config import config, Runner, CopyFiles, CopyDirs


def detect_os() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system != "linux":
        raise RuntimeError(f"Unsupported operating system: {platform.system()}")

    os_release = Path("/etc/os-release")
    if os_release.exists():
        text = os_release.read_text(encoding="utf-8").lower()
        if "ubuntu" in text or "debian" in text:
            return "linux-ubuntu"
        if "arch" in text:
            return "linux-arch"
    return "linux"


def os_matches(entry_os: str, selected_os: str) -> bool:
    if entry_os == "linux":
        return selected_os.startswith("linux")
    return entry_os == selected_os


def run_setup(selected_os: str, tags: set[str] | None = None, dry_run: bool = False, reverse: bool = False) -> int:
    runner = Runner(dry_run=dry_run)
    count = 0
    for entry in config:
        # Filter by OS
        if entry.os_ and not any(os_matches(o, selected_os) for o in entry.os_):
            continue
        # Filter by tags
        if tags and entry.tags and not tags.intersection(entry.tags):
            continue

        print(f"[info] running {type(entry).__name__}")
        if hasattr(entry, 'run'):
            if 'reverse' in entry.run.__code__.co_varnames:
                entry.run(runner, reverse=reverse)
            else:
                entry.run(runner)
        count += 1

    print(f"[info] executed {count} entries")
    return runner.returncode


def _expand(path: str) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def run_diff(selected_os: str, tags: set[str] | None = None) -> int:
    """Print unified diffs between source and destination for copy entries."""
    has_diff = False
    for entry in config:
        if entry.os_ and not any(os_matches(o, selected_os) for o in entry.os_):
            continue
        if tags and entry.tags and not tags.intersection(entry.tags):
            continue

        pairs: list[list[str]] = []
        if isinstance(entry, CopyFiles):
            pairs = entry.files
        elif isinstance(entry, CopyDirs):
            pairs = entry.dirs
        else:
            continue

        for pair in pairs:
            src = _expand(pair[0])
            dst = _expand(pair[1])
            if isinstance(entry, CopyDirs):
                has_diff |= _diff_dirs(src, dst)
            else:
                has_diff |= _diff_files(src, dst)

    return 1 if has_diff else 0


def _diff_files(src: str, dst: str) -> bool:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file() and not dst_path.is_file():
        return False
    src_lines = src_path.read_text().splitlines(keepends=True) if src_path.is_file() else []
    dst_lines = dst_path.read_text().splitlines(keepends=True) if dst_path.is_file() else []
    diff = list(difflib.unified_diff(dst_lines, src_lines, fromfile=dst, tofile=src))
    if diff:
        print("".join(diff), end="")
        return True
    return False


_SKIP_DIRS = {".git"}


def _iter_files(root: Path) -> set[str]:
    """Collect relative file paths, skipping hidden VCS directories."""
    result: set[str] = set()
    if not root.is_dir():
        return result
    for f in root.rglob("*"):
        if f.is_file() and not any(p.name in _SKIP_DIRS for p in f.parents if p != root):
            result.add(str(f.relative_to(root)))
    return result


def _diff_dirs(src: str, dst: str) -> bool:
    src_path, dst_path = Path(src), Path(dst)
    all_files = _iter_files(src_path) | _iter_files(dst_path)
    has_diff = False
    for rel in sorted(all_files):
        has_diff |= _diff_files(str(src_path / rel), str(dst_path / rel))
    return has_diff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dotfiles setup runner")
    parser.add_argument("command", choices=["setup", "pull", "diff", "test", "sandbox"], help="setup = copy to system, pull = copy from system, diff = show diffs between source and destination, test = run tests in docker containers, sandbox = open interactive docker shell")
    parser.add_argument("--os", dest="os_override", help="Override detected OS")
    parser.add_argument("--tag", dest="tags", action="append", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--distro", dest="distros", action="append", default=None, help="Distro(s) to test (ubuntu, arch). Repeatable. Defaults to all.")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild of docker image (sandbox command)")
    args = parser.parse_args(argv)

    if args.command == "test":
        from tests.docker_runner import run_docker_tests
        return run_docker_tests(args.distros)

    if args.command == "sandbox":
        from tests.docker_sandbox import run_docker_sandbox
        distro = args.distros[0] if args.distros else None
        return run_docker_sandbox(distro, rebuild=args.rebuild)

    selected_os = args.os_override or detect_os()
    tags = set(args.tags) if args.tags else None

    if args.command == "diff":
        return run_diff(selected_os, tags=tags)

    reverse = args.command == "pull"
    print(f"[info] selected OS: {selected_os}")
    return run_setup(selected_os, tags=tags, dry_run=args.dry_run, reverse=reverse)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    raise SystemExit(main())
