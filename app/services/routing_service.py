from __future__ import annotations

from typing import Any


CATEGORY_TO_DEPARTMENT: dict[str, str] = {
    "Infrastructure": "Infra Team",
    "Application": "Application Team",
    "Security": "Security Team",
    "Database": "Database Team",
    "Storage": "Storage Team",
    "Network": "Network Team",
    "Access Management": "Identity & Access Team",
}


def route_category_to_department(category: Any) -> str:
    category_name = str(category).strip()
    return CATEGORY_TO_DEPARTMENT.get(category_name, "General Support Team")


# ✅ ADD THIS CLASS (IMPORTANT)
class RoutingService:
    def __init__(self, classifier):
        self.classifier = classifier

    def route_ticket(self, text: str) -> dict:
        # Step 1: Predict category
        category = self.classifier.predict(text)

        # Step 2: Map to department
        department = route_category_to_department(category)

        return {
            "category": category,
            "department": department,
            "confidence": 0.85  # dummy for now
        }