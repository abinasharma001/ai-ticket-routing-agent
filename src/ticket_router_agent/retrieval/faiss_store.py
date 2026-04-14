from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ticket_router_agent.domain.interfaces import EmbeddingProvider, SimilarityIndex
from ticket_router_agent.domain.models import SimilarTicket, TicketCategory, TicketRecord


@dataclass
class FaissSimilarityIndex(SimilarityIndex):
    index_path: Path
    metadata_path: Path
    embedding_provider: EmbeddingProvider
    dimension: int | None = None

    def __post_init__(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._metadata: list[dict] = []
        self._faiss = self._import_faiss()

    def _import_faiss(self):
        try:
            import faiss

            return faiss
        except ImportError:
            return None

    def build(self, tickets: list[TicketRecord]) -> None:
        if not tickets:
            self._index = None
            self._metadata = []
            return

        texts = [f"{ticket.subject}\n{ticket.description}" for ticket in tickets]
        vectors = np.array(self.embedding_provider.embed(texts), dtype="float32")
        if vectors.ndim != 2:
            raise ValueError("Embeddings must be a 2D matrix")
        dimension = vectors.shape[1]
        self.dimension = dimension
        self._metadata = [self._serialize_ticket(ticket) for ticket in tickets]
        self.metadata_path.write_text(json.dumps(self._metadata, indent=2), encoding="utf-8")
        if self._faiss is not None:
            self._faiss.normalize_L2(vectors)
            index = self._faiss.IndexFlatIP(dimension)
            index.add(vectors)
            self._index = index
            self._faiss.write_index(index, str(self.index_path))
        else:
            self._index = vectors

    def load(self) -> None:
        if self.index_path.exists() and self.metadata_path.exists() and self._faiss is not None:
            self._index = self._faiss.read_index(str(self.index_path))
            self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        elif self.metadata_path.exists():
            self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def query(self, text: str, top_k: int = 5) -> list[SimilarTicket]:
        if self._index is None:
            self.load()
        if self._index is None or not self._metadata:
            return []

        vector = np.array(self.embedding_provider.embed([text]), dtype="float32")
        if self._faiss is not None and hasattr(self._index, "search"):
            self._faiss.normalize_L2(vector)
            scores, indices = self._index.search(vector, min(top_k, len(self._metadata)))
        else:
            stored_vectors = np.asarray(self._index, dtype="float32")
            vector = vector / np.linalg.norm(vector, axis=1, keepdims=True)
            stored_vectors = stored_vectors / np.linalg.norm(stored_vectors, axis=1, keepdims=True)
            scores_matrix = vector @ stored_vectors.T
            indices = np.argsort(scores_matrix[0])[::-1][: min(top_k, len(self._metadata))]
            scores = np.array([scores_matrix[0][indices]], dtype="float32")
            indices = np.array([indices], dtype="int64")
        similar_tickets: list[SimilarTicket] = []
        for score, index_position in zip(scores[0], indices[0]):
            if index_position < 0:
                continue
            metadata = self._metadata[int(index_position)]
            similar_tickets.append(
                SimilarTicket(
                    ticket_id=int(metadata["id"]),
                    subject=metadata["subject"],
                    category=TicketCategory(metadata["category"]),
                    department=metadata["department"],
                    resolution=metadata["resolution"],
                    similarity=float(max(score, 0.0)),
                )
            )
        return similar_tickets

    def _serialize_ticket(self, ticket: TicketRecord) -> dict:
        return {
            "id": ticket.id,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category.value,
            "department": ticket.department,
            "resolution": ticket.resolution,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "metadata": ticket.metadata,
        }
