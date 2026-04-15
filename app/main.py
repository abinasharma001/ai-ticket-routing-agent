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


# =========================
# REQUEST / RESPONSE MODELS
# =========================

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


# =========================
# APP STATE
# =========================

@dataclass
class AppState:
    classifier: TicketClassifier
    resolution_service: ResolutionService
    escalation_service: EscalationService


# =========================
# SAMPLE TRAINING DATA
# =========================

DEFAULT_TRAINING_DATA = [
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
]


# =========================
# APP STARTUP (IMPORTANT)
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(LOG_LEVEL)
    logger.info("🚀 Starting app with model {}", MODEL_NAME)

    training_texts = [
        clean_text(f"{item['title']} {item['description']}")
        for item in DEFAULT_TRAINING_DATA
    ]
    training_labels = [item["category"] for item in DEFAULT_TRAINING_DATA]

    classifier = TicketClassifier()
    classifier.train_model(training_texts, training_labels)

    build_index(
        [
            {
                "id": i + 1,
                "subject": item["title"],
                "description": item["description"],
                "resolution": item["resolution"],
                "category": item["category"],
            }
            for i, item in enumerate(DEFAULT_TRAINING_DATA)
        ]
    )

    app.state.app_state = AppState(
        classifier=classifier,
        resolution_service=ResolutionService(),
        escalation_service=EscalationService(
            confidence_threshold=0.5,
            similarity_threshold=0.4,
        ),
    )

    logger.info("✅ App initialized successfully")
    yield


# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="AI Ticket Routing API",
    version="1.0",
    lifespan=lifespan,
)


# =========================
# HEALTH CHECK (VERY IMPORTANT)
# =========================

@app.get("/")
def root():
    return {"message": "API is running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# MAIN API
# =========================

@app.post("/predict", response_model=PredictResponse)
def predict_ticket(payload: PredictRequest):
    state: AppState = app.state.app_state

    text = clean_text(f"{payload.title} {payload.description}")

    prediction = state.classifier.predict_ticket(text)

    category = prediction["label"]
    confidence = prediction["confidence"]

    department = route_category_to_department(category)

    retrieved = retrieve_similar_tickets(text)

    resolution_result = state.resolution_service.suggest_best_resolution(retrieved)

    similarity_score = resolution_result["similarity_score"]

    escalation_result = state.escalation_service.should_escalate(
        confidence=confidence,
        similarity=similarity_score,
    )

    return PredictResponse(
        category=category,
        department=department,
        confidence=confidence,
        resolution=resolution_result["best_resolution"],
        escalation=escalation_result["escalation_flag"],
        reason=escalation_result["reason"],
        similar_tickets=retrieved,
    )