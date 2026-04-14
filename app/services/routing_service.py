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