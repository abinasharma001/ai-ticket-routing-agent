from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ticket_router_agent.domain.models import SimilarTicket, TicketCategory


@dataclass
class DummyEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            vectors.append(
                [
                    float("server" in lowered or "cpu" in lowered or "disk" in lowered),
                    float("login" in lowered or "access" in lowered or "permission" in lowered),
                    float("vpn" in lowered or "network" in lowered or "latency" in lowered),
                    float("database" in lowered or "backup" in lowered or "replica" in lowered),
                ]
            )
        return vectors


class FakeSimilarityIndex:
    def __init__(self, matches: list[SimilarTicket] | None = None) -> None:
        self.matches = matches or []

    def build(self, tickets):
        self.tickets = tickets

    def query(self, text: str, top_k: int = 5):
        return self.matches[:top_k]


def build_similar_ticket(ticket_id: int, category: TicketCategory, similarity: float = 0.95) -> SimilarTicket:
    return SimilarTicket(
        ticket_id=ticket_id,
        subject=f"Similar issue {ticket_id}",
        category=category,
        department="Application Support",
        resolution="Apply the known fix and monitor the service.",
        similarity=similarity,
    )
