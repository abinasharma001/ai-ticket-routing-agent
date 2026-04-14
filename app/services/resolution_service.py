from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ResolutionService:
    def suggest_best_resolution(self, retrieved_tickets: list[dict[str, Any] | str]) -> dict[str, Any]:
        """Select the best resolution from the most similar ticket.

        Falls back to a generic resolution when no strong match exists.
        """
        candidates = [item for item in retrieved_tickets if isinstance(item, dict)]
        if not candidates:
            return {
                "best_resolution": "Please investigate logs and restart related services.",
                "similarity_score": 0.0,
            }

        best_match = max(candidates, key=lambda item: float(item.get("similarity", 0.0)))
        best_similarity = float(best_match.get("similarity", 0.0))
        if best_similarity < 0.5:
            return {
                "best_resolution": "Please investigate logs and restart related services.",
                "similarity_score": best_similarity,
            }

        return {
            "best_resolution": best_match.get("resolution", ""),
            "similarity_score": best_similarity,
        }
