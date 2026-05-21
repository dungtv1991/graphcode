"""
Embedding Provider — Abstraction layer for embedding models.
Supports: local SentenceTransformer, OpenAI, Azure OpenAI.
"""
import os
import sys
import numpy as np
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        """Encode texts into normalized embedding vectors."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        ...


class LocalProvider(EmbeddingProvider):
    """SentenceTransformer local model."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer
        print(f"Loading local model: {model_name}...", file=sys.stderr)
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        return self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=kwargs.get("batch_size", 32),
            show_progress_bar=kwargs.get("show_progress_bar", False),
        )

    @property
    def dimension(self) -> int:
        return self._dimension


class Model2VecProvider(EmbeddingProvider):
    """Model2Vec static embedding — ~300x faster than transformer, CPU-only, no inference.

    Dùng static distilled model (potion-*). Encode chỉ là token lookup + pooling.
    NOTE: Cần cài thêm `pip install model2vec`. Đã benchmark: accuracy thấp hơn
    MiniLM ~20-30% cho query tiếng Việt mơ hồ + full-stack module retrieval.
    Chỉ dùng khi ưu tiên tốc độ build/start hơn độ chính xác.
    """

    def __init__(self, model_name: str = "minishlab/potion-multilingual-128M"):
        from model2vec import StaticModel  # optional dependency
        print(f"Loading Model2Vec static model: {model_name}...", file=sys.stderr)
        self._model = StaticModel.from_pretrained(model_name)
        self._dimension = int(self._model.encode(["_"]).shape[1])

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        embs = self._model.encode(
            texts,
            show_progress_bar=kwargs.get("show_progress_bar", False),
        )
        embs = np.asarray(embs, dtype=np.float32)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return embs / norms

    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIProvider(EmbeddingProvider):
    """OpenAI embeddings API."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = ""):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required: pip install openai")
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", ""))
        self._model = model
        # text-embedding-3-small = 1536, text-embedding-3-large = 3072
        self._dimension = 1536 if "small" in model else 3072

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        # OpenAI API has batch limit of 2048
        batch_size = min(kwargs.get("batch_size", 512), 2048)
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            batch_embs = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embs)
        arr = np.array(all_embeddings, dtype=np.float32)
        # Normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return arr / norms

    @property
    def dimension(self) -> int:
        return self._dimension


class AzureProvider(EmbeddingProvider):
    """Azure OpenAI embeddings."""

    def __init__(self):
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("openai package required: pip install openai")
        self._client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        )
        self._model = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        self._dimension = 1536 if "small" in self._model else 3072

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        batch_size = min(kwargs.get("batch_size", 512), 2048)
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            batch_embs = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embs)
        arr = np.array(all_embeddings, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return arr / norms

    @property
    def dimension(self) -> int:
        return self._dimension


def create_provider() -> EmbeddingProvider:
    """Factory: create embedding provider based on env vars.
    
    Priority:
    1. AZURE_OPENAI_ENDPOINT → AzureProvider
    2. OPENAI_API_KEY → OpenAIProvider
    3. EMBEDDING_BACKEND=model2vec → Model2VecProvider (fast static)
    4. Fallback → LocalProvider (SentenceTransformer)
    """
    if os.environ.get("AZURE_OPENAI_ENDPOINT"):
        print("Using Azure OpenAI embeddings", file=sys.stderr)
        return AzureProvider()
    elif os.environ.get("OPENAI_API_KEY"):
        model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        print(f"Using OpenAI embeddings: {model}", file=sys.stderr)
        return OpenAIProvider(model=model)
    elif os.environ.get("EMBEDDING_BACKEND", "").lower() == "model2vec":
        model_name = os.environ.get("EMBEDDING_MODEL", "minishlab/potion-multilingual-128M")
        print(f"Using Model2Vec static embeddings: {model_name}", file=sys.stderr)
        return Model2VecProvider(model_name=model_name)
    else:
        model_name = os.environ.get("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        return LocalProvider(model_name=model_name)
