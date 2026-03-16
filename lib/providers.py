from __future__ import annotations

import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from lib.config_loader import resolve_function_target
from lib.models import SetupEntry


@dataclass
class CommandRunner:
    env: Mapping[str, str] | None = None

    def run(self, command: Sequence[str], check: bool = True, cwd: str | None = None) -> None:
        printable = " ".join(command)
        print(f"[exec] {printable}")
        completed = subprocess.run(
            list(command),
            check=False,
            cwd=cwd,
            env=dict(self.env) if self.env is not None else None,
        )
        if check and completed.returncode != 0:
            raise RuntimeError(f"Command failed with exit code {completed.returncode}: {printable}")

    def run_shell_script(self, script_lines: Iterable[str], check: bool = True, cwd: str | None = None) -> None:
        script = "set -eu\n" + "\n".join(script_lines) + "\n"
        print("[exec] /bin/sh -eu -c '<script>'")
        completed = subprocess.run(
            ["/bin/sh", "-eu", "-c", script],
            check=False,
            cwd=cwd,
            env=dict(self.env) if self.env is not None else None,
        )
        if check and completed.returncode != 0:
            raise RuntimeError(f"Shell task failed with exit code {completed.returncode}")


class ProviderExecutor:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner(env=os.environ.copy())
        self._providers = {
            "apt": self._run_apt,
            "brew": self._run_brew,
            "function": self._run_function,
            "pip3": self._run_pip3,
            "shell": self._run_shell,
        }

    def execute(self, entry: SetupEntry) -> None:
        provider = self._providers.get(entry.provider)
        if provider is None:
            raise RuntimeError(f"Unsupported provider at runtime: {entry.provider}")
        print(f"[setup] {entry.name} ({entry.provider})")
        provider(entry.target)

    def _run_apt(self, target: Sequence[str]) -> None:
        self.runner.run(["apt-get", "update"])
        self.runner.run(["apt-get", "install", "-y", *target], check=True)

    def _run_brew(self, target: Sequence[str]) -> None:
        if shutil.which("brew") is None:
            raise RuntimeError("brew provider requested, but Homebrew is not installed")
        self.runner.run(["brew", "install", *target], check=True)

    def _run_pip3(self, target: Sequence[str]) -> None:
        executable = shutil.which("pip3")
        if executable is None:
            raise RuntimeError("pip3 provider requested, but pip3 is not installed")
        self.runner.run([executable, "install", *target], check=True)

    def _run_shell(self, target: Sequence[str]) -> None:
        self.runner.run_shell_script(target, check=True)

    def _run_function(self, target: object) -> None:
        callable_target = resolve_function_target(target)
        print(f"[exec] python callable {callable_target.__module__}.{callable_target.__name__}")
        with _patched_environ(self.runner.env):
            callable_target()


@contextmanager
def _patched_environ(env: Mapping[str, str] | None):
    if env is None:
        yield
        return

    original = os.environ.copy()
    os.environ.clear()
    os.environ.update(env)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)
