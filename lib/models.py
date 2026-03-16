from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence, Tuple


SUPPORTED_PROVIDERS = {"apt", "brew", "function", "pip3", "shell"}
SUPPORTED_OS_TARGETS = {"macos", "linux", "linux-ubuntu", "linux-arch"}


@dataclass(frozen=True)
class SetupEntry:
    name: str
    provider: str
    target: Any
    os_targets: Tuple[str, ...]
    tags: Tuple[str, ...]


def as_tuple(value: object, field_name: str) -> Tuple[str, ...]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Sequence):
        items = list(value)
    else:
        raise ValueError(f"Expected '{field_name}' to be a string or list of strings")

    if not items or any(not isinstance(item, str) or not item.strip() for item in items):
        raise ValueError(f"Expected '{field_name}' to contain non-empty strings")
    return tuple(item.strip() for item in items)


def validate_os_targets(os_targets: Iterable[str]) -> Tuple[str, ...]:
    normalized = tuple(os_targets)
    invalid = [item for item in normalized if item not in SUPPORTED_OS_TARGETS]
    if invalid:
        options = ", ".join(sorted(SUPPORTED_OS_TARGETS))
        bad = ", ".join(invalid)
        raise ValueError(f"Unsupported OS target(s): {bad}. Supported values: {options}")
    return normalized


def is_callable_target(value: object) -> bool:
    return callable(value) or (isinstance(value, str) and value.strip())
