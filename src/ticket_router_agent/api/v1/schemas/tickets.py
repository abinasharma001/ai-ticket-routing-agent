from __future__ import annotations

from ticket_router_agent.domain.models import RoutingDecision, TicketInput


class TicketClassifyRequest(TicketInput):
    pass


class TicketRouteRequest(TicketInput):
    pass


class TicketResolutionRequest(TicketInput):
    pass


class TicketRepeatRequest(TicketInput):
    pass


class TicketClassifyResponse(RoutingDecision):
    pass
