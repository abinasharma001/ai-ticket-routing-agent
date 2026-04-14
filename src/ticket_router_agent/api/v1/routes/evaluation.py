from fastapi import APIRouter, Depends

from ticket_router_agent.api.v1.dependencies import get_orchestrator, get_repository
from ticket_router_agent.api.v1.schemas.evaluation import EvaluationResponse
from ticket_router_agent.evaluation.metrics import EvaluationMetrics
from ticket_router_agent.services.routing_service import RoutingOrchestrator
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationResponse)
def run_evaluation(
    repository: SQLiteTicketRepository = Depends(get_repository),
    orchestrator: RoutingOrchestrator = Depends(get_orchestrator),
) -> EvaluationResponse:
    tickets = repository.list_tickets()
    expected = [ticket.category.value for ticket in tickets]
    predicted = [orchestrator.classifier.predict(ticket)[0].value for ticket in tickets]
    return EvaluationMetrics().compute(expected, predicted)
