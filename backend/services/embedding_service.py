"""
embedding_service.py — Sentence-transformer embedding generation.
FIXED: Model loaded ONCE at startup via lifespan, not per request.
Change Tracker:
  v1.0 — initial
"""

from typing import List, Optional
from config.settings import settings
from config.logging_config import logger


class EmbeddingService:
    """
    Wraps sentence-transformers model.
    Model instance is injected from app.state (set in lifespan).
    Never create a new model instance per request — too slow.
    """

    def __init__(self, model=None):
        """
        model: pre-loaded SentenceTransformer instance from app.state.
        If None, attempts to load inline (only for testing).
        """
        self._model = model

    def fn_set_model(self, model) -> None:
        """Set the pre-loaded model (called from lifespan startup)."""
        self._model = model
        logger.info(f"EmbeddingService model set: {settings.EMBEDDING_MODEL}")

    def fn_embed_text(self, text: str) -> List[float]:
        """
        Generate a 384-dim embedding for a single text string.
        Returns list of floats.
        """
        if self._model is None:
            raise RuntimeError("Embedding model not loaded. Check lifespan startup.")
        try:
            var_embedding = self._model.encode(text, normalize_embeddings=True)
            return var_embedding.tolist()
        except Exception as e:
            logger.error(f"fn_embed_text error: {e}")
            raise

    def fn_embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        More efficient than calling fn_embed_text in a loop.
        """
        if self._model is None:
            raise RuntimeError("Embedding model not loaded.")
        try:
            var_embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False,
            )
            return [emb.tolist() for emb in var_embeddings]
        except Exception as e:
            logger.error(f"fn_embed_batch error: {e}")
            raise


# ── Global singleton — model set in main.py lifespan ────────
embedding_service = EmbeddingService()