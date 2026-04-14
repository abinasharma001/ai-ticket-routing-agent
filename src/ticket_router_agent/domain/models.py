from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    infrastructure = "Infrastructure"
    application = "Application"
    security = "Security"
    database = "Database"
    storage = "Storage"
    network = "Network"
    access_management = "Access Management"


class TicketInput(BaseModel):
    subject: str = Field(min_length=3)
    description: str = Field(min_length=5)
    reporter: str | None = None
    priority: str | None = None
    source_system: str | None = None

    def text(self) -> str:
        parts = [self.subject, self.description]
        if self.priority:
            parts.append(f"priority: {self.priority}")
        if self.source_system:
            parts.append(f"source: {self.source_system}")
        return "\n".join(parts)


class TicketRecord(BaseModel):
    id: int | None = None
    subject: str
    description: str
    category: TicketCategory
    department: str
    resolution: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimilarTicket(BaseModel):
    ticket_id: int
    subject: str
    category: TicketCategory
    department: str
    resolution: str
    similarity: float


class RoutingDecision(BaseModel):
    category: TicketCategory
    department: str
    confidence: float
    escalate: bool
    repeated_issue: bool = False
    repeated_issue_count: int = 0
    rationale: str
    similar_tickets: list[SimilarTicket] = Field(default_factory=list)
    suggested_resolution: str | None = None


class EvaluationSummary(BaseModel):
    accuracy: float
    f1_macro: float
    sample_size: int


class FeedbackPayload(BaseModel):
    ticket_id: int
    actual_category: TicketCategory
    actual_department: str
    was_helpful: bool | None = None
    notes: str | None = None
