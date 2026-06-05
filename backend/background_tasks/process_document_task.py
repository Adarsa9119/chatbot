"""
process_document_task.py — Background task that drives the full document
processing pipeline: text extraction → OCR fallback → table extraction →
chunking → embedding → vector storage.

Change Tracker:
v1.0 — initial
"""

from config.logging_config import logger
from config.settings import settings
from database.session import fn_get_standalone_db
from database.crud_documents import fn_get_document_by_id, fn_update_document_status
from database.crud_chunks import fn_create_chunk, fn_delete_chunks_by_doc
from services.embedding_service import embedding_service


def fn_process_document_task(doc_id: int) -> None:
    """
    Full document processing pipeline.
    Called as a FastAPI BackgroundTask after upload.

    Steps:
    1. Load document record from DB
    2. Extract text (pdfplumber + OCR fallback)
    3. Extract tables and append as text
    4. Chunk extracted text
    5. Generate embeddings for each chunk
    6. Store chunks + embeddings in DB
    7. Mark document as 'ready' or 'failed'
    """
    db = fn_get_standalone_db()
    try:
        # ── Step 1: Load document record ───────────────────────────────
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            logger.error(f"fn_process_document_task: doc_id={doc_id} not found")
            return

        logger.info(f"Processing started: doc_id={doc_id} title='{var_doc.title}'")
        fn_update_document_status(db, doc_id, "processing")

        # ── Step 2: Extract text ────────────────────────────────────────
        from utils.pdf_utils import fn_extract_text_from_pdf
        from utils.ocr_utils import fn_ocr_pdf

        var_text = fn_extract_text_from_pdf(var_doc.file_path)

        if not var_text or len(var_text.strip()) < settings.MIN_TEXT_LENGTH:
            logger.info(
                f"doc_id={doc_id}: text too short ({len(var_text or '')}) chars, "
                f"attempting OCR"
            )
            if settings.OCR_ENABLED:
                var_text = fn_ocr_pdf(var_doc.file_path)
            # Mark OCR was required
            var_doc.ocr_required = True
            db.commit()

        if not var_text or not var_text.strip():
            raise ValueError("No text could be extracted from the document.")

        # ── Step 3: Extract tables and append ──────────────────────────
        from utils.table_utils import fn_extract_tables_as_text
        var_table_text = fn_extract_tables_as_text(var_doc.file_path)
        if var_table_text:
            var_text += "\n\n" + var_table_text
            logger.info(f"doc_id={doc_id}: appended table text ({len(var_table_text)} chars)")

        # ── Step 4: Chunk text ──────────────────────────────────────────
        from rag.chunking import TextChunker
        var_chunker = TextChunker()
        var_chunks = var_chunker.fn_chunk_text(var_text, doc_id)

        if not var_chunks:
            raise ValueError("Chunking produced no chunks.")

        logger.info(f"doc_id={doc_id}: {len(var_chunks)} chunks produced")

        # ── Step 5 & 6: Embed and store chunks ─────────────────────────
        var_texts = [c["chunk_text"] for c in var_chunks]
        var_embeddings = embedding_service.fn_embed_batch(var_texts)

        fn_delete_chunks_by_doc(db, doc_id)  # Clear any previous partial chunks

        for var_chunk_data, var_embedding in zip(var_chunks, var_embeddings):
            fn_create_chunk(
                db=db,
                doc_id=doc_id,
                chunk_text=var_chunk_data["chunk_text"],
                chunk_index=var_chunk_data["chunk_index"],
                embedding=var_embedding,
                metadata=var_chunk_data.get("metadata"),
            )

        # ── Step 7: Mark as ready ───────────────────────────────────────
        fn_update_document_status(db, doc_id, "ready")
        logger.info(
            f"Processing complete: doc_id={doc_id} chunks={len(var_chunks)} status=ready"
        )

    except Exception as e:
        logger.error(f"fn_process_document_task FAILED doc_id={doc_id}: {e}")
        try:
            fn_update_document_status(db, doc_id, "failed", error_message=str(e))
        except Exception as inner_e:
            logger.error(f"Could not update failed status: {inner_e}")
    finally:
        db.close()