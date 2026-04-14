from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EscalationService:
    confidence_threshold: float = 0.5
    similarity_threshold: float = 0.4

    def should_escalate(self, confidence: float, similarity: float) -> dict[str, Any]:
        """Decide escalation using confidence and best-match similarity."""
        if confidence < self.confidence_threshold:
            return {
                "escalation_flag": True,
                "reason": "Low confidence prediction",
            }

        if similarity < self.similarity_threshold:
            return {
                "escalation_flag": True,
                "reason": "No strong match found",
            }

        return {
            "escalation_flag": False,
            "reason": "Prediction confidence and match quality are acceptable",
        }
