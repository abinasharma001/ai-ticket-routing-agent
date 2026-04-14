from fastapi import APIRouter, Depends

from ticket_router_agent.api.v1.dependencies import get_orchestrator, get_repository
from ticket_router_agent.api.v1.schemas.tickets import TicketClassifyRequest, TicketClassifyResponse
from ticket_router_agent.domain.models import FeedbackPayload, TicketInput
from ticket_router_agent.services.routing_service import RoutingOrchestrator
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/classify", response_model=TicketClassifyResponse)
def classify_ticket(
    payload: TicketClassifyRequest,
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator),
) -> TicketClassifyResponse:
    return orchestrator.classify(payload)


@router.post("/route", response_model=TicketClassifyResponse)
def route_ticket(
    payload: TicketInput,
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator),
) -> TicketClassifyResponse:
    return orchestrator.classify(payload)


@router.post("/recommend-resolution")
def recommend_resolution(
    payload: TicketInput,
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator),
) -> dict[str, object]:
    decision = orchestrator.classify(payload)
    return {
        "suggested_resolution": decision.suggested_resolution,
        "similar_tickets": decision.similar_tickets,
        "confidence": decision.confidence,
        "escalate": decision.escalate,
    }


@router.post("/detect-repeat")
def detect_repeat(
    payload: TicketInput,
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator),
) -> dict[str, object]:
    decision = orchestrator.classify(payload)
    return {
        "repeated_issue": decision.repeated_issue,
        "repeated_issue_count": decision.repeated_issue_count,
        "similar_tickets": decision.similar_tickets,
    }


@router.post("/feedback")
def ticket_feedback(
    payload: FeedbackPayload,
    repository: SQLiteTicketRepository = Depends(get_repository),
) -> dict[str, str]:
    repository.record_feedback(payload.model_dump())
    return {"status": "recorded"}
