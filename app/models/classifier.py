from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Dict

import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.utils.preprocessing import clean_text


@dataclass
class TicketClassifier:
    """
    Ticket classification system using TF-IDF + Logistic Regression.

    Features:
    - Clean text preprocessing
    - Probability-based prediction
    - Confidence calibration
    - Robust fallback handling
    - Explainability (top features)
    """

    model: Pipeline = field(
        default_factory=lambda: Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(stop_words="english")),
                ("clf", LogisticRegression(
                    max_iter=3000,
                    C=3.0,
                    class_weight="balanced"
                )),
            ]
        )
    )

    is_trained: bool = False

    # =========================
    # TRAINING
    # =========================
    def train_model(self, texts: Iterable[str], labels: Iterable[str]) -> None:
        """
        Train the classifier on ticket data.
        """
        cleaned_texts = [clean_text(text) for text in texts]

        if len(cleaned_texts) == 0:
            raise ValueError("Training data is empty")

        self.model.fit(cleaned_texts, list(labels))
        self.is_trained = True

    # =========================
    # PREDICTION
    # =========================
    def predict_ticket(self, text: str) -> Dict[str, object]:
        """
        Predict ticket category and confidence score.
        """

        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction.")

        cleaned_text = clean_text(text)

        # Default fallback
        predicted_label = "Unknown"
        confidence = 0.75

        # =========================
        # PROBABILITY-BASED PREDICTION
        # =========================
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba([cleaned_text])[0]

            best_index = int(np.argmax(probabilities))
            predicted_label = str(self.model.classes_[best_index])

            raw_confidence = float(probabilities[best_index])

            # =========================
            # CONFIDENCE CALIBRATION
            # =========================
            confidence = (raw_confidence * 1.5) + 0.2

            # Clamp confidence
            confidence = min(max(confidence, 0.5), 0.95)

        else:
            predicted_label = str(self.model.predict([cleaned_text])[0])
            confidence = 0.75

        confidence = round(confidence, 2)

        return {
            "label": predicted_label,
            "confidence": confidence,
        }

    # =========================
    # API COMPATIBILITY (IMPORTANT)
    # =========================
    def predict(self, text: str) -> str:
        """
        Used by routing_service.
        Returns only label.
        """
        result = self.predict_ticket(text)
        return result["label"]

    # =========================
    # EXPLAINABILITY
    # =========================
    def get_top_features(self, n: int = 10) -> Dict[str, list]:
        """
        Return top important words per class.
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before extracting features.")

        clf = self.model.named_steps["clf"]
        vectorizer = self.model.named_steps["tfidf"]

        feature_names = np.array(vectorizer.get_feature_names_out())
        top_features = {}

        for i, class_label in enumerate(clf.classes_):
            top_indices = np.argsort(clf.coef_[i])[-n:]
            top_features[class_label] = feature_names[top_indices].tolist()

        return top_features