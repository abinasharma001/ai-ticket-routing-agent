from __future__ import annotations

from dataclasses import dataclass

from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ticket_router_agent.domain.models import TicketCategory, TicketInput, TicketRecord


@dataclass
class BaselineTicketClassifier:
    model_path: str | None = None

    def __post_init__(self) -> None:
        self.pipeline: Pipeline = Pipeline(
            steps=[
                ("vectorizer", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
                ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
        self._is_fitted = False

    def fit(self, tickets: list[TicketRecord]) -> None:
        texts = [f"{ticket.subject}\n{ticket.description}" for ticket in tickets]
        labels = [ticket.category.value for ticket in tickets]
        self.pipeline.fit(texts, labels)
        self._is_fitted = True

    def predict(self, ticket: TicketInput) -> tuple[TicketCategory, float]:
        if not self._is_fitted:
            raise RuntimeError("Classifier must be trained before prediction")
        probabilities = self.pipeline.predict_proba([ticket.text()])[0]
        label_index = int(probabilities.argmax())
        predicted_label = self.pipeline.classes_[label_index]
        return TicketCategory(predicted_label), float(probabilities[label_index])

    def evaluate(self, tickets: list[TicketRecord]) -> tuple[list[str], list[str]]:
        texts = [f"{ticket.subject}\n{ticket.description}" for ticket in tickets]
        expected = [ticket.category.value for ticket in tickets]
        predicted = self.pipeline.predict(texts).tolist()
        return expected, predicted

    def save(self, path: str | None = None) -> None:
        if path is None and self.model_path is None:
            raise ValueError("A model path is required to save the classifier")
        dump(self.pipeline, path or self.model_path)

    def load(self, path: str | None = None) -> None:
        self.pipeline = load(path or self.model_path)
        self._is_fitted = True
