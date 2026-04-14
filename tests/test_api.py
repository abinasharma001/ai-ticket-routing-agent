from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_predict_endpoint_returns_expected_keys(monkeypatch):
    monkeypatch.setattr("app.main.build_index", lambda data: None)
    monkeypatch.setattr(
        "app.main.TicketClassifier.train_model",
        lambda self, texts, labels: setattr(self, "is_trained", True),
    )
    monkeypatch.setattr(
        "app.main.TicketClassifier.predict_ticket",
        lambda self, text: {"predicted_label": "Network", "confidence_score": 0.91},
    )
    monkeypatch.setattr("app.main.retrieve_similar_tickets", lambda query: [])

    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "title": "VPN connection drops",
                "description": "Remote staff lose connectivity during work hours.",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"category", "department", "confidence", "resolution", "escalation"}
    assert body["category"] == "Network"
    assert body["confidence"] == 0.91
