"""
reprocess_document_task.py — Reprocess an existing document.
Clears old chunks, resets status, then delegates to the main pipeline.

Change Tracker:
v1.0 — initial
"""

from config.logging_config import logger
from database.session import fn_get_standalone_db
from database.crud_documents import fn_get_document_by_id, fn_update_document_status
from database.crud_chunks import fn_delete_chunks_by_doc
from background_tasks.process_document_task import fn_process_document_task


def fn_reprocess_document_task(doc_id: int) -> None:
    """
    Reprocess a document that previously failed or needs refresh.

    Steps:
    1. Verify document exists
    2. Delete all existing chunks
    3. Reset status to 'processing'
    4. Re-run the main process_document_task pipeline

    Called by: admin_router reprocess endpoint, reprocess_all_docs script.
    """
    db = fn_get_standalone_db()
    try:
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            logger.error(f"fn_reprocess_document_task: doc_id={doc_id} not found")
            return

        logger.info(f"Reprocessing started: doc_id={doc_id} title='{var_doc.title}'")

        # Clear previous chunks and reset status
        fn_delete_chunks_by_doc(db, doc_id)
        fn_update_document_status(db, doc_id, "processing", error_message=None)

    except Exception as e:
        logger.error(f"fn_reprocess_document_task setup failed doc_id={doc_id}: {e}")
        return
    finally:
        db.close()

    # Delegate to the main pipeline
    fn_process_document_task(doc_id)