from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from loguru import logger
import io

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

class EscalationRequest(BaseModel):
    issue: str
    category: str
    department: str

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

# ------------------------------
# ROUTES
# ------------------------------

@app.get("/")
def home():
    return {"message": "AI Ticket Routing API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

def process_ticket(text: str):
    result = classifier.predict_ticket(text)
    department = route_category_to_department(result["label"])
    
    similar_tickets = retrieve_similar_tickets(text)
    resolution_data = resolution_service.suggest_best_resolution(similar_tickets)
    
    formatted_similar = []
    for st in similar_tickets:
        if isinstance(st, dict):
            formatted_similar.append({
                "id": st.get("ticket_id"),
                "title": st.get("ticket_text", "").split("\n")[0] if "ticket_text" in st else "",
                "resolution": st.get("resolution"),
                "score": st.get("similarity")
            })

    # Log to history
    log_prediction(text, result["label"], department, result["confidence"])

    return {
        "category": result["label"],
        "department": department,
        "confidence": result["confidence"],
        "solution": resolution_data.get("best_resolution"),
        "similar_tickets": formatted_similar
    }

@app.post("/predict")
def predict_ticket(request: TicketRequest):
    global is_trained

    if not is_trained:
        raise HTTPException(
            status_code=500,
            detail="Model not ready"
        )

    try:
        return process_ticket(request.text)

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    global is_trained

    if not is_trained:
        raise HTTPException(status_code=500, detail="Model not ready")
        
    if pytesseract is None:
        raise HTTPException(status_code=500, detail="pytesseract is not installed")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        extracted_text = pytesseract.image_to_string(image)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from image")
            
        result = process_ticket(extracted_text)
        result["extracted_text"] = extracted_text
        return result
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/escalate")
def escalate_ticket(request: EscalationRequest):
    success = send_escalation_email(request.issue, request.category, request.department)
    if success:
        return {"message": "Escalation email sent successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to send escalation email. Check server logs.")

@app.get("/history")
def get_history():
    return get_prediction_history()


@app.get("/test")
def test():
    return {"message": "Test endpoint working 🎯"}