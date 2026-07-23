from __future__ import annotations

import io
from time import perf_counter

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

from app.models.classifier import TicketClassifier
from app.services.routing_service import route_category_to_department
from app.utils.db import init_db, get_all_tickets, log_prediction, get_prediction_history
from app.retriever.retriever import build_index, retrieve_similar_tickets
from app.services.resolution_service import ResolutionService
from app.utils.email_service import send_escalation_email

resolution_service = ResolutionService()

MAX_IMAGE_BYTES = 5 * 1024 * 1024

# ------------------------------
# GLOBAL MODEL
# ------------------------------

classifier = TicketClassifier()
is_trained = False

# ------------------------------
# FASTAPI APP
# ------------------------------

app = FastAPI(
    title="AI Ticket Routing API",
    version="1.0.0",
    description="AI-powered ticket routing, similarity search, OCR analysis, and escalation services.",
)


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "Unhandled error on %s %s after %.2f ms: %s",
            request.method,
            request.url.path,
            elapsed_ms,
            exc,
        )
        raise

    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info("%s %s -> %s in %.2f ms", request.method, request.url.path, response.status_code, elapsed_ms)
    response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.2f}"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled application error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})

# ------------------------------
# REQUEST SCHEMA
# ------------------------------

class TicketRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)

class EscalationRequest(BaseModel):
    issue: str = Field(..., min_length=1, max_length=20_000)
    category: str = Field(..., min_length=1, max_length=120)
    department: str = Field(..., min_length=1, max_length=120)

# ------------------------------
# AUTO LOAD MODEL (IMPORTANT 🔥)
# ------------------------------

@app.on_event("startup")
def load_model():
    global is_trained

    try:
        logger.info("🚀 Training model on startup...")

        texts = [
            "Server is down",
            "Database connection error",
            "Login not working",
            "Network latency issue",
            "Disk storage full"
        ]

        labels = [
            "Infrastructure",
            "Database",
            "Application",
            "Network",
            "Storage"
        ]

        classifier.train_model(texts, labels)
        is_trained = True

        logger.info("✅ Model trained successfully")
        
        logger.info("🚀 Initializing Database and Retriever Index...")
        init_db()
        tickets = get_all_tickets()
        build_index(tickets)
        logger.info("✅ Retriever indexed successfully")

    except Exception as e:
        logger.error(f"❌ Startup initialization failed: {e}")




def _safe_http_error(status_code: int, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=message)


def _format_similar_ticket(ticket: dict[str, object]) -> dict[str, object]:
    raw_similarity = float(ticket.get("similarity", 0.0) or 0.0)
    return {
        "id": ticket.get("ticket_id", ticket.get("id")),
        "title": ticket.get("ticket_text", "").split("\n")[0] if ticket.get("ticket_text") else "",
        "ticket_text": ticket.get("ticket_text", ""),
        "resolution": ticket.get("resolution"),
        "score": raw_similarity,
        "category": ticket.get("category", ""),
        "department": ticket.get("department", ""),
    }


def process_ticket(text: str) -> dict[str, object]:
    ticket_started_at = perf_counter()
    result = classifier.predict_ticket(text)
    department = route_category_to_department(result["label"])

    similar_tickets = retrieve_similar_tickets(text)
    resolution_data = resolution_service.suggest_best_resolution(similar_tickets)

    formatted_similar: list[dict[str, object]] = []
    for similar_ticket in similar_tickets:
        if isinstance(similar_ticket, dict):
            formatted_similar.append(_format_similar_ticket(similar_ticket))

    processing_ms = (perf_counter() - ticket_started_at) * 1000

    try:
        log_prediction(text, result["label"], department, result["confidence"], processing_ms=processing_ms)
    except Exception as exc:
        logger.exception("Failed to persist prediction history: %s", exc)

    return {
        "category": result["label"],
        "department": department,
        "confidence": result["confidence"],
        "solution": resolution_data.get("best_resolution"),
        "similar_tickets": formatted_similar,
        "processing_ms": round(processing_ms, 2),
    }

# ------------------------------
# ROUTES
# ------------------------------

@app.get("/")
def home():
    try:
        return {"message": "AI Ticket Routing API is running 🚀"}
    except Exception as exc:
        logger.exception("Home endpoint failed: %s", exc)
        raise _safe_http_error(500, "Service unavailable.") from exc

@app.get("/health")
def health():
    try:
        return {"status": "ok"}
    except Exception as exc:
        logger.exception("Health endpoint failed: %s", exc)
        raise _safe_http_error(500, "Service unavailable.") from exc

@app.post("/predict")
def predict_ticket(request: TicketRequest):
    global is_trained

    try:
        if not is_trained:
            raise _safe_http_error(503, "Model not ready.")

        return process_ticket(request.text)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prediction error: %s", exc)
        raise _safe_http_error(500, "Prediction failed. Please try again.") from exc

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    global is_trained

    if not is_trained:
        raise _safe_http_error(503, "Model not ready.")

    if pytesseract is None:
        raise _safe_http_error(503, "OCR engine is not available on the server.")

    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise _safe_http_error(400, "Only image uploads are supported.")

        image_bytes = await file.read()
        if not image_bytes:
            raise _safe_http_error(400, "Uploaded file is empty.")
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise _safe_http_error(413, "Uploaded image is too large. Please use a file under 5 MB.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            image = Image.open(io.BytesIO(image_bytes))
            extracted_text = pytesseract.image_to_string(image)
        except Exception as ocr_e:
            logger.exception("Tesseract OCR failed: %s", ocr_e)
            raise _safe_http_error(500, "OCR engine failure. Please try another image.") from ocr_e
        
        if not extracted_text.strip():
            raise _safe_http_error(422, "No text could be extracted from the uploaded image.")

        result = process_ticket(extracted_text)
        result["extracted_text"] = extracted_text
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Image analysis error: %s", exc)
        raise _safe_http_error(500, "Image analysis failed. Please try again.") from exc

@app.post("/escalate")
def escalate_ticket(request: EscalationRequest):
    try:
        success = send_escalation_email(request.issue, request.category, request.department)
        if success:
            return {"message": "Escalation email sent successfully."}
        else:
            raise _safe_http_error(500, "Failed to send escalation email.")
    except ValueError as ve:
        raise _safe_http_error(503, str(ve))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Escalation error: %s", exc)
        raise _safe_http_error(500, "Escalation failed. Please try again.") from exc

@app.get("/history")
def get_history():
    try:
        return get_prediction_history()
    except Exception as exc:
        logger.exception("History endpoint failed: %s", exc)
        raise _safe_http_error(500, "Unable to load history.") from exc


@app.get("/test")
def test():
    try:
        return {"message": "Test endpoint working 🎯"}
    except Exception as exc:
        logger.exception("Test endpoint failed: %s", exc)
        raise _safe_http_error(500, "Service unavailable.") from exc