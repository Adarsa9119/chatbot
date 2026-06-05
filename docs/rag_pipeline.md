# RAG Pipeline

This document describes the Retrieval-Augmented Generation (RAG) pipeline used by DocChat to answer user questions over uploaded documents.

---

## Overview

```
Upload → Extract → Chunk → Embed → Store (pgvector)
                                        ↓
Question → Embed → Retrieve → Rerank → Prompt → LLM → Answer
```

---

## 1. Document Ingestion

### 1.1 Upload & Validation
- Accepted formats: PDF, PNG, JPG, TIFF (max 50 MB)
- File saved to `uploads/documents/<uuid>.<ext>`
- `document_service` creates a DB record with `status = pending`
- A background task (`process_document_task`) is queued

### 1.2 Text Extraction
`document_service` → `pdf_utils` / `ocr_service`

| PDF type          | Strategy                                 |
|-------------------|------------------------------------------|
| Text-based PDF    | `pdfplumber` — direct text extraction    |
| Scanned / image   | `ocr_service` → Tesseract OCR per page  |
| PDF with tables   | `table_service` → pdfplumber tables → Markdown |

### 1.3 Chunking
`rag/chunking.py`

- Strategy: **recursive character splitting** with overlap
- Chunk size: `800` tokens (configurable via `settings.CHUNK_SIZE`)
- Overlap: `100` tokens (`settings.CHUNK_OVERLAP`)
- Metadata attached to each chunk: `document_id`, `page`, `chunk_index`

### 1.4 Embedding
`services/embedding_service.py`

- Model: `text-embedding-3-small` (OpenAI) or configurable via `settings.EMBEDDING_MODEL`
- Batch size: 100 chunks per API call
- Embeddings stored in `chunks` table (pgvector `vector` column)

---

## 2. Retrieval

`rag/retrieval.py` + `services/vector_service.py`

1. User's question is embedded with the same model used at ingestion time.
2. Cosine similarity search against the pgvector index:
   ```sql
   SELECT * FROM chunks
   WHERE document_id = ANY(:doc_ids)
   ORDER BY embedding <=> :query_vector
   LIMIT :top_k;
   ```
3. Default `top_k = 10` (configurable).
4. Results filtered to documents the user has access to.

---

## 3. Reranking
`rag/reranker.py`

- Cross-encoder reranker (Cohere `rerank-english-v3.0` or local model)
- Top-10 candidates → reranked → top-5 passed to prompt builder
- Falls back to cosine similarity order if reranker is unavailable

---

## 4. Prompt Construction
`rag/prompt_builder.py`

```
[System]
You are DocChat, an AI assistant that answers questions using only the
provided document excerpts. If the answer is not in the excerpts, say so.

[Context]
<chunk 1 — document: report.pdf, page 4>
...text...

<chunk 2 — document: report.pdf, page 6>
...text...

[User question]
What are the key Q3 findings?
```

- Prompt is token-counted; chunks are trimmed if context window would be exceeded.
- Source metadata is preserved for citation.

---

## 5. Response Generation
`services/llm_service.py` + `rag/response_generator.py`

- Default model: `gpt-4o-mini` (configurable via `settings.LLM_MODEL`)
- Temperature: `0.2` for factual responses
- Response streamed back to the client via SSE (optional)
- Answer + source list saved to `chat_messages` table

---

## 6. Guardrails
`rag/guardrails.py`

- **Input guardrail**: reject empty, too-short, or injection-pattern queries
- **Output guardrail**: strip PII patterns before returning response
- **Scope guardrail**: model instructed to only answer from provided context

---

## Configuration Reference

| Setting                  | Default             | Description                          |
|--------------------------|---------------------|--------------------------------------|
| `CHUNK_SIZE`             | `800`               | Target token count per chunk         |
| `CHUNK_OVERLAP`          | `100`               | Token overlap between chunks         |
| `RETRIEVAL_TOP_K`        | `10`                | Chunks retrieved before reranking    |
| `RERANK_TOP_N`           | `5`                 | Chunks passed to the LLM prompt      |
| `EMBEDDING_MODEL`        | `text-embedding-3-small` | OpenAI embedding model          |
| `LLM_MODEL`              | `gpt-4o-mini`       | Chat completion model                |
| `LLM_TEMPERATURE`        | `0.2`               | Sampling temperature                 |
| `LLM_MAX_TOKENS`         | `1024`              | Max tokens in model response         |