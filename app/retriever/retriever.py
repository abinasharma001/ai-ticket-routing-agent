from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:  # pragma: no cover - fallback for environments without faiss
    faiss = None


@dataclass
class RetrievalItem:
    ticket_id: Any
    ticket_text: str
    resolution: str
    similarity: float


@dataclass
class SemanticRetriever:
    model_name: str = "all-MiniLM-L6-v2"
    top_k: int = 3
    model: SentenceTransformer | None = field(init=False)
    index: Any = field(default=None, init=False)
    tickets: list[dict[str, Any]] = field(default_factory=list, init=False)
    embeddings: np.ndarray | None = field(default=None, init=False)
    _data_signature: tuple[int, int] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Load the embedding model once during retriever initialization."""
        if SentenceTransformer is not None:
            self.model = SentenceTransformer(self.model_name)
        else:
            self.model = None

    def build_index(self, data: list[dict[str, Any]]) -> None:
        """Build and cache embeddings/index for retrieval.

        Reuses cached artifacts if the dataset signature has not changed.
        """
        self.tickets = data or []
        if not self.tickets:
            self.index = None
            self.embeddings = None
            self._data_signature = None
            return

        signature = self._compute_signature(self.tickets)
        if self._data_signature == signature and self.embeddings is not None and self.index is not None:
            return

        if self.model is None:
            self.index = None
            self.embeddings = None
            self._data_signature = None
            return

        texts = [self._ticket_to_text(ticket) for ticket in self.tickets]
        self.embeddings = np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype="float32")

        if faiss is not None:
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(self.embeddings)
        else:
            self.index = self.embeddings
        self._data_signature = signature

    def retrieve_similar_tickets(self, query: str) -> list[dict[str, Any] | str]:
        """Retrieve the top 3 similar tickets for a query.

        If FAISS is unavailable, cosine similarity is used.
        If the dataset is empty, returns a fallback suggestion list.
        """
        if not query:
            return ["No similar tickets found. Suggested resolution based on AI model."]
        if self.index is None or not self.tickets or self.model is None:
            return ["No similar tickets found. Suggested resolution based on AI model."]

        query_embedding = np.asarray(self.model.encode([query], normalize_embeddings=True), dtype="float32")

        if faiss is not None and hasattr(self.index, "search"):
            scores, indices = self.index.search(query_embedding, min(3, len(self.tickets)))
            ranked = zip(indices[0], scores[0])
        else:
            stored_embeddings = np.asarray(self.index, dtype="float32")
            similarities = cosine_similarity(query_embedding, stored_embeddings)[0]
            ranked_indices = np.argsort(similarities)[::-1][: min(3, len(self.tickets))]
            ranked = ((int(index), float(similarities[index])) for index in ranked_indices)

        results: list[dict[str, Any]] = []
        for index, score in ranked:
            if index < 0:
                continue
            ticket = self.tickets[int(index)]
            results.append(
                {
                    "ticket_id": ticket.get("ticket_id", ticket.get("id")),
                    "ticket_text": self._ticket_to_text(ticket),
                    "resolution": ticket.get("resolution", ""),
                    "similarity": float(score),
                }
            )
        if not results:
            return ["No similar tickets found. Suggested resolution based on AI model."]
        return results

    @staticmethod
    def _compute_signature(tickets: list[dict[str, Any]]) -> tuple[int, int]:
        descriptions = "|".join(str(item.get("description", item.get("ticket_text", ""))) for item in tickets)
        return len(tickets), hash(descriptions)

    @staticmethod
    def _ticket_to_text(ticket: dict[str, Any]) -> str:
        subject = str(ticket.get("subject", ""))
        description = str(ticket.get("description", ticket.get("ticket_text", "")))
        return f"{subject}\n{description}".strip()


_retriever = SemanticRetriever()


def build_index(data: list[dict[str, Any]]) -> None:
    _retriever.build_index(data)


def retrieve_similar_tickets(query: str) -> list[dict[str, Any] | str]:
    return _retriever.retrieve_similar_tickets(query)
