from __future__ import annotations

from typing import Iterable, Sequence

from lib.config_loader import load_config
from lib.osinfo import detect_current_os, validate_os_override
from lib.planner import filter_entries, normalize_tags
from lib.providers import ProviderExecutor


def run_setup(os_override: str | None = None, tags: Sequence[str] | None = None) -> int:
    selected_os = validate_os_override(os_override) if os_override else detect_current_os()
    selected_tags = normalize_tags(tags)

    print(f"[info] selected OS: {selected_os}")
    print(f"[info] selected tags: {', '.join(sorted(selected_tags))}")

    entries = load_config()
    plan = filter_entries(entries, selected_os=selected_os, tags=selected_tags)
    if not plan:
        print("[info] no matching entries")
        return 0

    print(f"[info] executing {len(plan)} entr{'y' if len(plan) == 1 else 'ies'}")
    executor = ProviderExecutor()
    for entry in plan:
        executor.execute(entry)
    print("[info] setup complete")
    return 0
