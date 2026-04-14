from __future__ import annotations

from typing import Protocol

from ticket_router_agent.domain.models import RoutingDecision, TicketInput, TicketRecord, SimilarTicket, TicketCategory


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class TicketClassifier(Protocol):
    def predict(self, ticket: TicketInput) -> tuple[TicketCategory, float]:
        ...


class TicketRepository(Protocol):
    def upsert_ticket(self, ticket: TicketRecord) -> TicketRecord:
        ...

    def list_tickets(self) -> list[TicketRecord]:
        ...

    def get_ticket(self, ticket_id: int) -> TicketRecord | None:
        ...

    def record_feedback(self, payload: dict) -> None:
        ...


class SimilarityIndex(Protocol):
    def build(self, tickets: list[TicketRecord]) -> None:
        ...

    def query(self, text: str, top_k: int = 5) -> list[SimilarTicket]:
        ...


class RoutingService(Protocol):
    def classify(self, ticket: TicketInput) -> RoutingDecision:
        ...
