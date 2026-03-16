from __future__ import annotations

import platform
from pathlib import Path


def detect_current_os() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system != "linux":
        raise RuntimeError(f"Unsupported operating system: {platform.system()}")

    distro = _detect_linux_distro()
    if distro == "ubuntu":
        return "linux-ubuntu"
    if distro == "arch":
        return "linux-arch"
    return "linux"


def _detect_linux_distro() -> str | None:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return None

    values: dict[str, str] = {}
    for line in os_release.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        values[key] = raw_value.strip().strip('"')

    identifiers = {
        values.get("ID", "").lower(),
        values.get("ID_LIKE", "").lower(),
    }
    joined = " ".join(item for item in identifiers if item)
    if "ubuntu" in joined or "debian" in joined:
        return "ubuntu"
    if "arch" in joined:
        return "arch"
    return None


def validate_os_override(name: str) -> str:
    valid = {"macos", "linux", "linux-ubuntu", "linux-arch"}
    if name not in valid:
        supported = ", ".join(sorted(valid))
        raise ValueError(f"Unsupported OS override '{name}'. Supported values: {supported}")
    return name


def os_matches(entry_os: str, selected_os: str) -> bool:
    if entry_os == "linux":
        return selected_os.startswith("linux")
    return entry_os == selected_os
