from __future__ import annotations

import os
from pathlib import Path


def write_helper_marker() -> None:
    marker = os.environ["FUNCTION_MARKER_FILE"]
    Path(marker).write_text("helper-ran", encoding="utf-8")
