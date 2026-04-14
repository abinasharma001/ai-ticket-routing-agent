from fastapi import Request

from ticket_router_agent.services.routing_service import RoutingOrchestrator
from ticket_router_agent.storage.sqlite_repository import SQLiteTicketRepository


def get_orchestrator(request: Request) -> RoutingOrchestrator:
    return request.app.state.orchestrator


def get_repository(request: Request) -> SQLiteTicketRepository:
    return request.app.state.repository
