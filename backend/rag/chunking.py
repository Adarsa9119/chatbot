"""
chunking.py — Recursive text chunking for RAG pipeline.
Change Tracker:
  v1.0 — initial
"""

from typing import List
from config.settings import settings
from config.logging_config import logger


class TextChunker:
    """
    Splits extracted text into overlapping chunks for embedding.
    Uses recursive character splitting strategy.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def fn_chunk_text(self, text: str, doc_id: int) -> List[dict]:
        """
        Split text into chunks.
        Returns list of { doc_id, chunk_text, chunk_index, metadata }
        """
        if not text or not text.strip():
            return []

        var_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        var_chunks: List[str] = []
        var_current_chunk = ""

        for var_para in var_paragraphs:
            # If paragraph alone is larger than chunk_size, split it further
            if len(var_para) > self.chunk_size:
                temp_var_words = var_para.split(" ")
                temp_var_sub = ""
                for var_word in temp_var_words:
                    if len(temp_var_sub) + len(var_word) + 1 > self.chunk_size:
                        if temp_var_sub:
                            var_chunks.append(temp_var_sub.strip())
                        temp_var_sub = var_word
                    else:
                        temp_var_sub += " " + var_word
                if temp_var_sub:
                    var_chunks.append(temp_var_sub.strip())
            elif len(var_current_chunk) + len(var_para) + 2 > self.chunk_size:
                if var_current_chunk:
                    var_chunks.append(var_current_chunk.strip())
                var_current_chunk = var_para
            else:
                var_current_chunk += "\n\n" + var_para if var_current_chunk else var_para

        if var_current_chunk:
            var_chunks.append(var_current_chunk.strip())

        # Add overlap between consecutive chunks
        var_final_chunks: List[dict] = []
        for var_idx, var_chunk in enumerate(var_chunks):
            # Add tail of previous chunk as prefix (overlap)
            if var_idx > 0 and self.chunk_overlap > 0:
                var_prev = var_chunks[var_idx - 1]
                var_overlap_text = var_prev[-self.chunk_overlap:]
                var_chunk = var_overlap_text + " " + var_chunk

            var_final_chunks.append({
                "doc_id": doc_id,
                "chunk_text": var_chunk.strip(),
                "chunk_index": var_idx,
                "metadata": {"chunk_index": var_idx},
            })

        logger.info(f"Chunked doc_id={doc_id}: {len(var_final_chunks)} chunks from {len(text)} chars")
        return var_final_chunks