# AI Powered Intelligent Ticket Routing & Resolution Agent

AI Powered Intelligent Ticket Routing & Resolution Agent is a FastAPI-based system for classifying IT support tickets, routing them to the correct department, retrieving similar historical incidents, suggesting the best resolution, and escalating low-confidence or frequently repeated issues.

The project is designed as a clean, production-style baseline with a modular Python architecture, configurable embeddings, a scikit-learn classifier, FAISS-powered semantic retrieval, and evaluation support for accuracy and F1.

## Features

- Classifies tickets into Infrastructure, Application, Security, Database, Storage, Network, and Access Management.
- Routes each ticket to the appropriate department or team.
- Uses retrieval-augmented search to surface similar historical tickets.
- Suggests the best known resolution from retrieved cases.
- Returns a confidence score for the prediction.
- Escalates low-confidence or frequently repeated issues.
- Supports Sentence Transformers embeddings by default.
- Supports OpenAI embeddings as an optional configuration.
- Includes a TF-IDF + Logistic Regression baseline classifier.
- Includes accuracy and F1 evaluation utilities.
- Uses SQLite for local persistence and seed data.
- Uses `loguru` for structured application logging.
- Includes FastAPI Swagger UI and ReDoc auto-generated docs.
- Includes an optional Dockerfile for containerized deployment.
- Includes an optional Streamlit UI for quick ticket prediction.

## Architecture

```text
Client
	|
	v
FastAPI App (app/main.py)
	|
	+--> Preprocessing (app/utils/preprocessing.py)
	|
	+--> Classifier (app/models/classifier.py)
	|        |
	|        +--> Predict category + confidence
	|
	+--> Routing (app/services/routing_service.py)
	|        |
	|        +--> Category -> Department
	|
	+--> Retriever (app/retriever/retriever.py)
	|        |
	|        +--> Sentence Transformers embeddings
	|        +--> FAISS similarity search
	|
	+--> Resolution Engine (app/services/resolution_service.py)
	|        |
	|        +--> Best historical resolution
	|
	+--> Escalation (app/services/escalation.py)
					 |
					 +--> Confidence threshold
					 +--> Repeat-issue frequency
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update values if needed.

### 5. Optional: run tests

```bash
pytest
```

## Run Command

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI auto docs are available at:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

## Optional Streamlit UI

Start the UI with:

```bash
streamlit run streamlit_app.py
```

The UI sends requests to `http://127.0.0.1:8000/predict`.

## Optional Docker Build

Build the container image:

```bash
docker build -t ticket-routing-agent .
```

Run the container:

```bash
docker run -p 8000:8000 ticket-routing-agent
```

## Sample API Request

`POST /predict`

```json
{
	"title": "VPN connection drops for remote staff",
	"description": "Users lose VPN access every few minutes during work hours."
}
```

## Sample API Response

```json
{
	"category": "Network",
	"department": "Network Team",
	"confidence": 0.91,
	"resolution": "Adjust VPN keepalive settings and verify gateway stability.",
	"escalation": false
}
```

## Project Structure

```text
app/
├── config/
├── models/
├── retriever/
├── services/
├── utils/
└── main.py

tests/
data/
requirements.txt
README.md
```

## Main Components

- `app/main.py`: FastAPI application and `/predict` endpoint.
- `app/models/classifier.py`: TF-IDF + Logistic Regression baseline classifier.
- `app/retriever/retriever.py`: Semantic search and similar ticket retrieval.
- `app/services/resolution_service.py`: Best-resolution selection from retrieved tickets.
- `app/services/escalation.py`: Escalation decision logic.
- `app/services/routing_service.py`: Category-to-department routing.
- `app/utils/preprocessing.py`: Text cleaning and normalization.
- `app/utils/evaluation.py`: Accuracy and F1 metrics.

## Future Improvements

- Replace the baseline classifier with a stronger fine-tuned model.
- Add a persistent FAISS index build pipeline and scheduled reindexing.
- Store tickets and feedback in a production database such as PostgreSQL.
- Add authentication and role-based access control.
- Add request tracing, structured logs, and observability dashboards.
- Add a feedback loop so agent resolutions improve over time.
- Add Docker and Compose support for one-command local startup.
- Add more comprehensive API, integration, and regression tests.

## Notes

- Sentence Transformers is the default embedding provider.
- OpenAI embeddings are supported through configuration.
- FAISS is enabled on supported platforms; on Windows the retriever falls back to a NumPy similarity search path so the project still runs cleanly.
- SQLite is used for local persistence so the project can run without external services.
