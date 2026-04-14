from __future__ import annotations

import re
from typing import Any


def clean_text(text: Any) -> str:
    if text is None:
        return ""

    cleaned = str(text).strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
