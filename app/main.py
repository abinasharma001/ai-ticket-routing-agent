from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.models.classifier import TicketClassifier
from app.services.routing_service import route_category_to_department

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
    version="1.0.0"
)

# ------------------------------
# REQUEST SCHEMA
# ------------------------------

class TicketRequest(BaseModel):
    text: str

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

    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")

# ------------------------------
# ROUTES
# ------------------------------

@app.get("/")
def home():
    return {"message": "AI Ticket Routing API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict_ticket(request: TicketRequest):
    global is_trained

    if not is_trained:
        raise HTTPException(
            status_code=500,
            detail="Model not ready"
        )

    try:
        result = classifier.predict_ticket(request.text)

        department = route_category_to_department(result["label"])

        return {
            "input": request.text,
            "category": result["label"],
            "confidence": result["confidence"],
            "department": department
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test():
    return {"message": "Test endpoint working 🎯"}