"""Docker-based integration test runner for ubuntu and arch linux."""

import subprocess
import pexpect
from pathlib import Path

TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent

DISTROS = {
    "ubuntu": TESTS_DIR / "docker" / "ubuntu.Dockerfile",
    "arch": TESTS_DIR / "docker" / "arch.Dockerfile",
}

IMAGE_TAG_PREFIX = "dotfiles-test"


def build_image(distro: str, dockerfile: Path) -> bool:
    tag = f"{IMAGE_TAG_PREFIX}-{distro}"
    print(f"[test] building image {tag} from {dockerfile.name}")
    result = subprocess.run(
        ["docker", "build", "-f", str(dockerfile), "-t", tag, str(REPO_ROOT)],
        capture_output=False,
    )
    return result.returncode == 0


def run_in_container(distro: str, cmd: list[str], label: str) -> int:
    tag = f"{IMAGE_TAG_PREFIX}-{distro}"
    print(f"\n[test] {label} in {distro} container")
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT}:/dotfiles:ro",
            "-w", "/dotfiles",
            tag,
        ] + cmd,
    )
    return result.returncode


def run_pexpect_command(distro: str, label: str, bash_script: str, password_prompts: int = 1) -> int:
    """Run a bash script in a docker container, using pexpect to answer password prompts."""
    tag = f"{IMAGE_TAG_PREFIX}-{distro}"
    print(f"\n[test] {label} in {distro} container")
    child = pexpect.spawn(
        "docker", [
            "run", "--rm", "-it",
            "-v", f"{REPO_ROOT}:/dotfiles:ro",
            "-w", "/dotfiles",
            tag,
            "bash", "-c", bash_script,
        ],
        encoding="utf-8",
        timeout=60,
    )
    child.logfile_read = __import__("sys").stdout
    for _ in range(password_prompts):
        child.expect("Secret Pass:")
        child.sendline("testpassword")
    child.expect(pexpect.EOF)
    child.close()
    return child.exitstatus or 0


SETUP_FIXTURE = " ".join([
    "cp -r /dotfiles /dotfiles-rw && cd /dotfiles-rw",
    "&& echo 'test-credential' > /tmp/test-cred",
    "&& echo testpassword | gpg --batch -c --passphrase-fd 0 --output dotfiles/git-credentials.gpg /tmp/test-cred",
])


def run_setup_e2e(distro: str) -> int:
    """Run forward setup + e2e verification."""
    return run_pexpect_command(
        distro,
        "running setup + e2e verification",
        f"{SETUP_FIXTURE} && python3 run.py setup --tag dotfiles"
        " && python3 -m pytest tests/test_e2e.py -v --tb=short",
        password_prompts=0,
    )


def run_reverse_e2e(distro: str) -> int:
    """Run forward setup, then reverse (pull), then verify the round-trip."""
    return run_pexpect_command(
        distro,
        "running reverse (pull) + round-trip verification",
        f"{SETUP_FIXTURE} && python3 run.py setup --tag dotfiles"
        " && python3 run.py pull --tag secrets"
        " && python3 -m pytest tests/test_e2e_reverse.py -v --tb=short",
        password_prompts=2,
    )


def run_tests_in_container(distro: str) -> int:
    rc = run_in_container(
        distro,
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short", "--ignore=tests/test_e2e.py", "--ignore=tests/test_e2e_reverse.py"],
        "running unit tests",
    )
    if rc != 0:
        return rc

    # Run setup (with pexpect to handle password prompt) and e2e verification
    rc = run_setup_e2e(distro)
    if rc != 0:
        return rc

    # Run reverse (pull) and verify round-trip encryption
    return run_reverse_e2e(distro)


def run_docker_tests(distros: list[str] | None = None) -> int:
    selected = distros or list(DISTROS.keys())
    unknown = [d for d in selected if d not in DISTROS]
    if unknown:
        print(f"[test] unknown distro(s): {', '.join(unknown)}. Available: {', '.join(DISTROS)}")
        return 1

    failures = []
    for distro in selected:
        dockerfile = DISTROS[distro]
        if not build_image(distro, dockerfile):
            print(f"[test] failed to build image for {distro}")
            failures.append(distro)
            continue

        rc = run_tests_in_container(distro)
        if rc != 0:
            failures.append(distro)

    if failures:
        print(f"\n[test] FAILED on: {', '.join(failures)}")
        return 1

    print(f"\n[test] all distros passed: {', '.join(selected)}")
    return 0
