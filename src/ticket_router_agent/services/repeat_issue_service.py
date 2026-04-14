from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ticket_router_agent.core.config import Settings
from ticket_router_agent.domain.models import SimilarTicket, TicketInput, TicketRecord


@dataclass
class RepeatIssueService:
    settings: Settings

    def detect(self, ticket: TicketInput, tickets: list[TicketRecord], similar_tickets: list[SimilarTicket]) -> tuple[bool, int]:
        cutoff = datetime.utcnow() - timedelta(days=self.settings.repeat_issue_window_days)
        recent_tickets = [item for item in tickets if item.created_at >= cutoff]
        matched_ids = {
            item.ticket_id
            for item in similar_tickets
            if item.similarity >= 0.80
        }
        count = sum(1 for ticket_item in recent_tickets if ticket_item.id in matched_ids)
        return count >= self.settings.repeat_issue_min_count, count
