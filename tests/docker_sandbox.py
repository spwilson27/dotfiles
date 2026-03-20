"""Interactive Docker sandbox for manual dotfiles testing."""

import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent

DISTROS = {
    "ubuntu": TESTS_DIR / "docker" / "ubuntu.Dockerfile",
    "arch": TESTS_DIR / "docker" / "arch.Dockerfile",
}

IMAGE_TAG_PREFIX = "dotfiles-sandbox"


def build_image(distro: str, dockerfile: Path) -> bool:
    tag = f"{IMAGE_TAG_PREFIX}-{distro}"
    print(f"[sandbox] building image {tag} from {dockerfile.name}")
    result = subprocess.run(
        ["docker", "build", "-f", str(dockerfile), "-t", tag, str(REPO_ROOT)],
    )
    return result.returncode == 0


def run_sandbox(distro: str) -> int:
    tag = f"{IMAGE_TAG_PREFIX}-{distro}"
    print(f"[sandbox] creating {distro} container")

    create = subprocess.run(
        ["docker", "create", "-it", "-w", "/dotfiles", tag, "/bin/bash"],
        capture_output=True, text=True,
    )
    if create.returncode != 0:
        print(f"[sandbox] failed to create container: {create.stderr.strip()}")
        return 1

    container_id = create.stdout.strip()

    print(f"[sandbox] copying repo into container")
    cp = subprocess.run(
        ["docker", "cp", f"{REPO_ROOT}/.", f"{container_id}:/dotfiles"],
    )
    if cp.returncode != 0:
        subprocess.run(["docker", "rm", container_id], capture_output=True)
        print(f"[sandbox] failed to copy repo into container")
        return 1

    print(f"[sandbox] starting shell (changes are isolated — exit to discard)")
    subprocess.run(["docker", "start", "-ai", container_id])

    subprocess.run(["docker", "rm", container_id], capture_output=True)
    return 0


def run_docker_sandbox(distro: str | None = None, rebuild: bool = False) -> int:
    selected = distro or "ubuntu"
    if selected not in DISTROS:
        print(f"[sandbox] unknown distro '{selected}'. Available: {', '.join(DISTROS)}")
        return 1

    dockerfile = DISTROS[selected]
    tag = f"{IMAGE_TAG_PREFIX}-{selected}"

    # Check if image exists already (skip build unless --rebuild)
    if rebuild or not _image_exists(tag):
        if not build_image(selected, dockerfile):
            print(f"[sandbox] failed to build image for {selected}")
            return 1
    else:
        print(f"[sandbox] using existing image {tag} (use --rebuild to force rebuild)")

    return run_sandbox(selected)


def _image_exists(tag: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", tag],
        capture_output=True,
    )
    return result.returncode == 0
