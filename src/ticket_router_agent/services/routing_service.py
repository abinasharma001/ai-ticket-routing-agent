from __future__ import annotations

from dataclasses import dataclass

from ticket_router_agent.core.config import Settings
from ticket_router_agent.domain.departments import CATEGORY_TO_DEPARTMENT
from ticket_router_agent.domain.models import RoutingDecision, TicketCategory, TicketInput
from ticket_router_agent.ml.baseline_classifier import BaselineTicketClassifier
from ticket_router_agent.retrieval.faiss_store import FaissSimilarityIndex
from ticket_router_agent.services.repeat_issue_service import RepeatIssueService
from ticket_router_agent.services.resolution_service import ResolutionService
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository


@dataclass
class RoutingOrchestrator:
    settings: Settings
    classifier: BaselineTicketClassifier
    repository: SQLiteTicketRepository
    similarity_index: FaissSimilarityIndex
    resolution_service: ResolutionService
    repeat_issue_service: RepeatIssueService

    def classify(self, ticket: TicketInput) -> RoutingDecision:
        category, confidence = self.classifier.predict(ticket)
        department = CATEGORY_TO_DEPARTMENT[category]
        similar_tickets = self.similarity_index.query(ticket.text(), top_k=self.settings.default_top_k)
        repeated_issue, repeated_count = self.repeat_issue_service.detect(
            ticket=ticket,
            tickets=self.repository.list_tickets(),
            similar_tickets=similar_tickets,
        )
        suggested_resolution = self.resolution_service.suggest_resolution(ticket, similar_tickets)
        escalate = confidence < self.settings.escalation_threshold or repeated_issue
        rationale = (
            f"Predicted {category.value} with confidence {confidence:.2f}. "
            f"Route to {department}."
        )
        if repeated_issue:
            rationale += f" Repeated issue detected in {repeated_count} recent ticket(s)."
        return RoutingDecision(
            category=category,
            department=department,
            confidence=confidence,
            escalate=escalate,
            repeated_issue=repeated_issue,
            repeated_issue_count=repeated_count,
            rationale=rationale,
            similar_tickets=similar_tickets,
            suggested_resolution=suggested_resolution,
        )
