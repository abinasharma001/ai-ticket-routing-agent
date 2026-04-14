from __future__ import annotations

from dataclasses import dataclass

from ticket_router_agent.domain.models import SimilarTicket, TicketInput


@dataclass
class ResolutionService:
    def suggest_resolution(self, ticket: TicketInput, similar_tickets: list[SimilarTicket]) -> str:
        if not similar_tickets:
            return (
                "No closely matched historical ticket was found. "
                "Collect more details, validate impact, and route for manual triage."
            )

        top_ticket = similar_tickets[0]
        resolution_lines = [
            f"Most similar case: {top_ticket.subject} ({top_ticket.department}, {top_ticket.category.value}).",
            f"Historical resolution: {top_ticket.resolution}",
            "Recommended action: verify the same root cause, apply the historical fix, and confirm with the requester.",
        ]
        if len(similar_tickets) > 1:
            resolution_lines.append(
                f"Additional similar cases reviewed: {len(similar_tickets) - 1}."
            )
        return " ".join(resolution_lines)
