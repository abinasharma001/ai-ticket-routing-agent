from __future__ import annotations

from dataclasses import dataclass

from ticket_router_agent.core.config import Settings
from ticket_router_agent.domain.interfaces import EmbeddingProvider


@dataclass
class SentenceTransformerEmbeddingProvider:
    model_name: str

    def __post_init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


@dataclass
class OpenAIEmbeddingProvider:
    api_key: str
    model_name: str

    def __post_init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=self.api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddingProvider(settings.openai_api_key, settings.openai_embedding_model)
    return SentenceTransformerEmbeddingProvider(settings.sentence_transformers_model)
