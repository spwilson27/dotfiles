from __future__ import annotations

from typing import Iterable, List, Sequence, Set

from lib.models import SetupEntry
from lib.osinfo import os_matches


def normalize_tags(tags: Sequence[str] | None) -> Set[str]:
    if not tags:
        return {"all"}

    normalized: Set[str] = set()
    for item in tags:
        for part in item.split(","):
            value = part.strip()
            if value:
                normalized.add(value)
    if not normalized:
        return {"all"}
    return normalized


def filter_entries(entries: Iterable[SetupEntry], selected_os: str, tags: Set[str]) -> List[SetupEntry]:
    filtered: List[SetupEntry] = []
    for entry in entries:
        if not any(os_matches(os_target, selected_os) for os_target in entry.os_targets):
            continue
        if not tags.intersection(entry.tags):
            continue
        filtered.append(entry)
    return filtered
