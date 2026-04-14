from __future__ import annotations

from datetime import datetime, timedelta

from ticket_router_agent.core.config import Settings
from ticket_router_agent.domain.models import TicketCategory, TicketInput, TicketRecord
from ticket_router_agent.evaluation.metrics import EvaluationMetrics
from ticket_router_agent.ml.baseline_classifier import BaselineTicketClassifier
from ticket_router_agent.services.repeat_issue_service import RepeatIssueService
from ticket_router_agent.services.resolution_service import ResolutionService
from ticket_router_agent.services.routing_service import RoutingOrchestrator
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository

from tests.conftest import FakeSimilarityIndex, build_similar_ticket


def build_repo(tmp_path):
    repository = SQLiteTicketRepository(tmp_path / "tickets.db")
    base_time = datetime.utcnow() - timedelta(days=1)
    seed_tickets = [
        TicketRecord(
            subject="VPN disconnects for remote staff",
            description="Remote users lose VPN access every few minutes.",
            category=TicketCategory.network,
            department="Network Operations",
            resolution="Adjusted tunnel keepalive settings.",
            created_at=base_time,
            updated_at=base_time,
        ),
        TicketRecord(
            subject="Database backup fails overnight",
            description="The nightly backup job cannot reach the target mount.",
            category=TicketCategory.database,
            department="Database Administration",
            resolution="Restored the mount and reran the backup.",
            created_at=base_time,
            updated_at=base_time,
        ),
        TicketRecord(
            subject="Access request missing payroll permissions",
            description="New hire cannot open the payroll portal after onboarding.",
            category=TicketCategory.access_management,
            department="Identity and Access Management",
            resolution="Synced role membership and confirmed access.",
            created_at=base_time,
            updated_at=base_time,
        ),
    ]
    for ticket in seed_tickets:
        repository.upsert_ticket(ticket)
    return repository


def build_classifier(repository):
    classifier = BaselineTicketClassifier()
    classifier.fit(repository.list_tickets())
    return classifier


def test_routing_trains_and_routes(tmp_path):
    repository = build_repo(tmp_path)
    classifier = build_classifier(repository)
    similarity_index = FakeSimilarityIndex(
        matches=[
            build_similar_ticket(1, TicketCategory.network),
            build_similar_ticket(2, TicketCategory.network),
            build_similar_ticket(3, TicketCategory.network),
        ]
    )
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'tickets.db'}",
        seed_data_path=tmp_path / "seed.json",
        faiss_index_path=tmp_path / "faiss.index",
        faiss_metadata_path=tmp_path / "faiss.json",
        escalation_threshold=0.60,
    )
    orchestrator = RoutingOrchestrator(
        settings=settings,
        classifier=classifier,
        repository=repository,
        similarity_index=similarity_index,
        resolution_service=ResolutionService(),
        repeat_issue_service=RepeatIssueService(settings),
    )

    decision = orchestrator.classify(
        TicketInput(
            subject="VPN connection drops in the evening",
            description="Remote workers are disconnected from the VPN repeatedly during file transfers.",
        )
    )

    assert decision.category == TicketCategory.network
    assert decision.department == "Network Operations"
    assert decision.repeated_issue is True
    assert decision.escalate is True
    assert decision.confidence > 0.0
    assert decision.suggested_resolution is not None


def test_evaluation_metrics_compute_values():
    summary = EvaluationMetrics().compute(["A", "B", "B"], ["A", "B", "A"])

    assert summary.sample_size == 3
    assert summary.accuracy == 2 / 3
    assert 0.0 <= summary.f1_macro <= 1.0
