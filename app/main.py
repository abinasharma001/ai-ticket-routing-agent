from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel, Field

from app.config.settings import CONFIDENCE_THRESHOLD, LOG_LEVEL, MODEL_NAME
from app.models.classifier import TicketClassifier
from app.retriever.retriever import build_index, retrieve_similar_tickets
from app.services.escalation import EscalationService
from app.services.resolution_service import ResolutionService
from app.services.routing_service import route_category_to_department
from app.utils.logging import configure_logging
from app.utils.preprocessing import clean_text


class PredictRequest(BaseModel):
    title: str = Field(default="")
    description: str = Field(default="")


class PredictResponse(BaseModel):
    category: str
    department: str
    confidence: float
    resolution: str
    escalation: bool
    reason: str
    similar_tickets: list[Any]


@dataclass
class AppState:
    classifier: TicketClassifier
    resolution_service: ResolutionService
    escalation_service: EscalationService


DEFAULT_TRAINING_DATA: list[dict[str, str]] = [
    {
        "title": "VPN connection drops for remote users",
        "description": "Remote staff cannot stay connected to the VPN during work hours.",
        "category": "Network",
        "resolution": "Adjust VPN keepalive settings and verify gateway stability.",
    },
    {
        "title": "Application login page returns 500",
        "description": "Users receive a server error when signing into the portal.",
        "category": "Application",
        "resolution": "Restart the app service and check the authentication backend.",
    },
    {
        "title": "Suspicious MFA prompts detected",
        "description": "Multiple users report unexpected MFA prompts after failed login attempts.",
        "category": "Security",
        "resolution": "Block suspicious IPs and review conditional access policies.",
    },
    {
        "title": "Database backup job failed overnight",
        "description": "The nightly database backup could not reach the target mount.",
        "category": "Database",
        "resolution": "Restore the storage mount and rerun the backup job.",
    },
    {
        "title": "Shared storage volume nearly full",
        "description": "New uploads fail because the file share is above capacity.",
        "category": "Storage",
        "resolution": "Archive stale data and expand the storage volume.",
    },
    {
        "title": "New employee cannot access payroll system",
        "description": "Access request is pending and the user cannot open the payroll portal.",
        "category": "Access Management",
        "resolution": "Approve the role-based access package and sync group membership.",
    },
    {
        "title": "Server CPU spikes after patch deployment",
        "description": "Production servers are hitting sustained high CPU usage after the latest patch rollout.",
        "category": "Infrastructure",
        "resolution": "Rollback the patch on affected nodes and reschedule after capacity review.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(LOG_LEVEL)
    logger.info("Starting {} with model {}", app.title, MODEL_NAME)
    training_texts = [clean_text(f"{item['title']} {item['description']}") for item in DEFAULT_TRAINING_DATA]
    training_labels = [item["category"] for item in DEFAULT_TRAINING_DATA]

    classifier = TicketClassifier()
    classifier.train_model(training_texts, training_labels)

    build_index(
        [
            {
                "id": index + 1,
                "subject": item["title"],
                "description": item["description"],
                "resolution": item["resolution"],
                "category": item["category"],
            }
            for index, item in enumerate(DEFAULT_TRAINING_DATA)
        ]
    )

    app.state.app_state = AppState(
        classifier=classifier,
        resolution_service=ResolutionService(),
        escalation_service=EscalationService(confidence_threshold=0.5, similarity_threshold=0.4),
    )
    logger.info("Application state initialized and retrieval index built")
    yield


app = FastAPI(
    title="AI Powered Intelligent Ticket Routing & Resolution Agent",
    description="FastAPI service for AI ticket classification, routing, retrieval, resolution, and escalation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict_ticket(payload: PredictRequest) -> PredictResponse:
    """Predict category, route department, retrieve similar tickets, and return resolution/escalation."""
    state: AppState = app.state.app_state

    combined_text = clean_text(f"{payload.title} {payload.description}")
    prediction = state.classifier.predict_ticket(combined_text)
    category = str(prediction["label"])
    confidence = float(prediction["confidence"])
    department = route_category_to_department(category)

    retrieved_tickets = retrieve_similar_tickets(combined_text)
    resolution_result = state.resolution_service.suggest_best_resolution(retrieved_tickets)
    similarity_score = float(resolution_result["similarity_score"])
    escalation_result = state.escalation_service.should_escalate(
        confidence=confidence,
        similarity=similarity_score,
    )

    escalation_flag = bool(escalation_result["escalation_flag"])
    reason = str(escalation_result["reason"])

    similarity_values = [
        float(ticket.get("similarity", 0.0))
        for ticket in retrieved_tickets
        if isinstance(ticket, dict)
    ]

    logger.info(
        "Confidence score={:.2f}",
        confidence,
    )
    logger.info("Similarity scores={}", similarity_values)
    logger.info(
        "Escalation decision={} reason='{}'",
        escalation_flag,
        reason,
    )
    logger.info(
        "Predicted category={} department={} confidence={:.2f}",
        category,
        department,
        confidence,
    )

    return PredictResponse(
        category=category,
        department=department,
        confidence=confidence,
        resolution=str(resolution_result["best_resolution"]),
        escalation=escalation_flag,
        reason=reason,
        similar_tickets=retrieved_tickets,
    )
