from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from loguru import logger

# Lazy-loaded globals
classifier = None
routing_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting FastAPI app (light mode)...")
    yield
    logger.info("🛑 Shutting down app...")

app = FastAPI(
    title="AI Ticket Routing & Resolution API",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------------------
# BASIC ROUTES
# ------------------------------

@app.get("/")
def home():
    return {"message": "AI Ticket Routing API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ------------------------------
# INIT MODEL (LAZY LOAD)
# ------------------------------

@app.get("/init")
def initialize_model():
    global classifier, routing_service

    try:
        from app.models.classifier import TicketClassifier
        from app.services.routing_service import RoutingService

        classifier = TicketClassifier()
        routing_service = RoutingService(classifier)

        return {"message": "Model initialized successfully ✅"}

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# PREDICT ROUTE
# ------------------------------

@app.post("/predict")
def predict_ticket(text: str):
    global classifier, routing_service

    if classifier is None or routing_service is None:
        raise HTTPException(
            status_code=400,
            detail="Model not initialized. Call /init first."
        )

    try:
        result = routing_service.route_ticket(text)

        return {
            "input": text,
            "prediction": result
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# SIMPLE TEST ROUTE
# ------------------------------

@app.get("/test")
def test():
    return {"message": "Test endpoint working 🎯"}