from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ticket_router_agent.core.config import Settings
from ticket_router_agent.embeddings.provider import build_embedding_provider
from ticket_router_agent.evaluation.metrics import EvaluationMetrics
from ticket_router_agent.ml.baseline_classifier import BaselineTicketClassifier
from ticket_router_agent.retrieval.faiss_store import FaissSimilarityIndex
from ticket_router_agent.services.repeat_issue_service import RepeatIssueService
from ticket_router_agent.services.resolution_service import ResolutionService
from ticket_router_agent.services.routing_service import RoutingOrchestrator
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository
from ticket_router_agent.domain.models import TicketCategory, TicketRecord


def load_seed_tickets(path: Path) -> list[TicketRecord]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [
        TicketRecord(
            id=item.get("id"),
            subject=item["subject"],
            description=item["description"],
            category=TicketCategory(item["category"]),
            department=item["department"],
            resolution=item["resolution"],
            created_at=datetime.fromisoformat(item.get("created_at") or datetime.utcnow().isoformat()),
            updated_at=datetime.fromisoformat(item.get("updated_at") or datetime.utcnow().isoformat()),
            metadata=item.get("metadata", {}),
        )
        for item in raw_items
    ]


def seed_repository(repository: SQLiteTicketRepository, seed_path: Path) -> None:
    if repository.list_tickets():
        return
    for ticket in load_seed_tickets(seed_path):
        repository.upsert_ticket(ticket)


def build_services(settings: Settings) -> RoutingOrchestrator:
    repository = SQLiteTicketRepository(settings.sqlite_path)
    seed_repository(repository, settings.seed_data_path)
    tickets = repository.list_tickets()

    classifier = BaselineTicketClassifier()
    classifier.fit(tickets)

    embedding_provider = build_embedding_provider(settings)
    similarity_index = FaissSimilarityIndex(
        index_path=settings.faiss_index_path,
        metadata_path=settings.faiss_metadata_path,
        embedding_provider=embedding_provider,
    )
    similarity_index.build(tickets)

    return RoutingOrchestrator(
        settings=settings,
        classifier=classifier,
        repository=repository,
        similarity_index=similarity_index,
        resolution_service=ResolutionService(),
        repeat_issue_service=RepeatIssueService(settings),
    )


def run_evaluation(settings: Settings) -> dict[str, float | int]:
    orchestrator = build_services(settings)
    tickets = orchestrator.repository.list_tickets()
    expected = [ticket.category.value for ticket in tickets]
    predicted = [orchestrator.classifier.predict(ticket)[0].value for ticket in tickets]
    summary = EvaluationMetrics().compute(expected, predicted)
    return summary.model_dump()
