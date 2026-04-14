from __future__ import annotations

import os
from logging import INFO

from dotenv import load_dotenv

load_dotenv()

CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
MODEL_NAME: str = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") or INFO
