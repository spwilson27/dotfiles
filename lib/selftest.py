from __future__ import annotations

import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class DockerCase:
    name: str
    dockerfile: Path
    image_tag: str
    setup_os: str
    python_command: str
    auto_verify_command: str
    verify_command: str


DOCKER_CASES = (
    DockerCase(
        name="ubuntu",
        dockerfile=ROOT / "tests" / "docker" / "ubuntu.Dockerfile",
        image_tag="dotfiles-selftest-ubuntu",
        setup_os="linux-ubuntu",
        python_command="python3",
        auto_verify_command=(
            'OUTPUT=$('
            'DOTFILES_STATE_DIR=/tmp/dotfiles-auto '
            'python3 ./run.py setup --tag all --tag selftest 2>&1'
            ')\n'
            'printf "%s\\n" "$OUTPUT"\n'
            'printf "%s\\n" "$OUTPUT" | grep -q "\\[info\\] selected OS: linux-ubuntu"\n'
            'command -v git\n'
            'test -f /tmp/dotfiles-auto/common-marker.txt'
        ),
        verify_command="command -v git && test -f ./.dotfiles-state/common-marker.txt",
    ),
    DockerCase(
        name="arch",
        dockerfile=ROOT / "tests" / "docker" / "arch.Dockerfile",
        image_tag="dotfiles-selftest-arch",
        setup_os="linux-arch",
        python_command="python",
        auto_verify_command=(
            'OUTPUT=$('
            'DOTFILES_STATE_DIR=/tmp/dotfiles-auto '
            'python ./run.py setup --tag all --tag selftest 2>&1'
            ')\n'
            'printf "%s\\n" "$OUTPUT"\n'
            'printf "%s\\n" "$OUTPUT" | grep -q "\\[info\\] selected OS: linux-arch"\n'
            'test -x /usr/local/bin/dotfiles-selftest-arch\n'
            '/usr/local/bin/dotfiles-selftest-arch | grep -q arch-selftest-ok\n'
            'test -f /tmp/dotfiles-auto/common-marker.txt'
        ),
        verify_command=(
            "test -x /usr/local/bin/dotfiles-selftest-arch && "
            "/usr/local/bin/dotfiles-selftest-arch | grep -q arch-selftest-ok && "
            "test -f ./.dotfiles-state/common-marker.txt"
        ),
    ),
)


def run_selftest() -> int:
    print("[selftest] running unit tests")
    _run_unit_tests()
    _ensure_docker_available()
    for case in DOCKER_CASES:
        _run_docker_case(case)
    print("[selftest] all checks passed")
    return 0


def open_docker_shell(image_name: str) -> int:
    case = _get_docker_case(image_name)
    _ensure_docker_available()
    print(f"[docker] building {case.name} image")
    _build_docker_image(case)

    container_name = f"dotfiles-shell-{case.name}-{uuid.uuid4().hex[:8]}"
    create_command = [
        "docker",
        "create",
        "-it",
        "--name",
        container_name,
        case.image_tag,
        "/bin/sh",
        "-lc",
        "mkdir -p /workspace && cd /workspace && exec /bin/sh",
    ]

    print(f"[docker] creating {case.name} shell container")
    _run(create_command)
    try:
        print("[docker] copying repository into container")
        _run(["docker", "cp", f"{ROOT}/.", f"{container_name}:/workspace"])
        print("[docker] starting interactive shell")
        completed = subprocess.run(["docker", "start", "-ai", container_name], check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"Command failed with exit code {completed.returncode}: docker start -ai {container_name}"
            )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return 0


def _run_unit_tests() -> None:
    command = _build_test_command()
    runner_name = "pytest" if "pytest" in command else "unittest"
    print(f"[selftest] using {runner_name} for Python tests")
    _run(command)


def _build_test_command() -> list[str]:
    if shutil.which("pytest") is not None:
        return [sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")]
    return [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(ROOT / "tests"),
        "-p",
        "test_*.py",
    ]


def _ensure_docker_available() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is required for selftest, but 'docker' was not found in PATH")
    completed = subprocess.run(["docker", "version"], check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown Docker error"
        raise RuntimeError(f"Docker is required for selftest, but it is not usable: {message}")


def _run_docker_case(case: DockerCase) -> None:
    print(f"[selftest] building {case.name} image")
    _build_docker_image(case)

    print(f"[selftest] validating auto-detected setup in {case.name} container")
    _run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/workspace",
            "-w",
            "/workspace",
            case.image_tag,
            "/bin/sh",
            "-eu",
            "-c",
            case.auto_verify_command,
        ]
    )

    print(f"[selftest] validating overridden setup in {case.name} container")
    script = (
        f"{case.python_command} ./run.py setup --os {case.setup_os} --tag all --tag selftest\n"
        f"{case.verify_command}\n"
    )
    _run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/workspace",
            "-w",
            "/workspace",
            case.image_tag,
            "/bin/sh",
            "-eu",
            "-c",
            script,
        ]
    )


def _run(command: list[str]) -> None:
    printable = " ".join(command)
    print(f"[exec] {printable}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {printable}")


def _build_docker_image(case: DockerCase) -> None:
    _run(
        [
            "docker",
            "build",
            "-f",
            str(case.dockerfile),
            "-t",
            case.image_tag,
            str(ROOT),
        ]
    )


def _get_docker_case(name: str) -> DockerCase:
    for case in DOCKER_CASES:
        if case.name == name:
            return case
    supported = ", ".join(case.name for case in DOCKER_CASES)
    raise ValueError(f"Unsupported docker image '{name}'. Supported values: {supported}")
