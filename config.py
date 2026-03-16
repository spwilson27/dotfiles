"""
Providers:
    - shell
    - apt
    - pip3
    - brew
    - function

OS:
    - linux (default detection)
    - linux-arch
    - linux-ubuntu
    - macos
"""

CONFIG = [
    {
        "name": "common-shell-marker",
        "provider": "shell",
        "target": [
            'STATE_DIR="${DOTFILES_STATE_DIR:-$PWD/.dotfiles-state}"',
            'mkdir -p "$STATE_DIR"',
            'printf "setup-ran\n" > "$STATE_DIR/common-marker.txt"',
        ],
        "os": ["linux", "macos"],
        "tags": ["all", "dotfile"],
    },
    {
        "name": "ubuntu-selftest-package",
        "provider": "apt",
        "target": ["git"],
        "os": ["linux-ubuntu"],
        "tags": ["selftest"],
    },
    {
        "name": "arch-selftest-command",
        "provider": "shell",
        "target": [
            'cat > /usr/local/bin/dotfiles-selftest-arch <<\'EOF\'',
            '#!/bin/sh',
            'printf "arch-selftest-ok\n"',
            'EOF',
            'chmod +x /usr/local/bin/dotfiles-selftest-arch',
        ],
        "os": ["linux-arch"],
        "tags": ["selftest"],
    },
    {
        "name": "python-tooling-example",
        "provider": "pip3",
        "target": ["wheel"],
        "os": ["linux", "macos"],
        "tags": ["python-tools"],
    },
    {
        "name": "macos-dev-example",
        "provider": "brew",
        "target": ["git"],
        "os": ["macos"],
        "tags": ["dev"],
    },
]
