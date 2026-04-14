from __future__ import annotations

from fastapi import FastAPI

from ticket_router_agent.api.v1.routes.evaluation import router as evaluation_router
from ticket_router_agent.api.v1.routes.health import router as health_router
from ticket_router_agent.api.v1.routes.tickets import router as tickets_router
from ticket_router_agent.bootstrap import build_services
from ticket_router_agent.core.config import get_settings
from ticket_router_agent.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def startup_event() -> None:
    app.state.settings = settings
    app.state.orchestrator = build_services(settings)
    app.state.repository = app.state.orchestrator.repository


app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(tickets_router, prefix=settings.api_prefix)
app.include_router(evaluation_router, prefix=settings.api_prefix)
