"""
reprocess_all_docs.py — Reprocess all documents (or only failed ones).
Useful after updating the chunking strategy or embedding model.

Usage:
    python scripts/reprocess_all_docs.py            # Reprocess all failed docs
    python scripts/reprocess_all_docs.py --all       # Reprocess every document
    python scripts/reprocess_all_docs.py --doc-id 5  # Reprocess a single document

Change Tracker:
v1.0 — initial
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.logging_config import fn_setup_logging, logger
from database.session import fn_get_standalone_db
from database.crud_documents import fn_get_all_documents, fn_get_document_by_id
from background_tasks.reprocess_document_task import fn_reprocess_document_task


def fn_reprocess_all(reprocess_all: bool = False, doc_id: int = None) -> None:
    fn_setup_logging()

    db = fn_get_standalone_db()
    try:
        if doc_id:
            var_docs = [fn_get_document_by_id(db, doc_id)]
            if not var_docs[0]:
                print(f"[ERROR] Document with id={doc_id} not found")
                return
        else:
            var_all_docs = fn_get_all_documents(db)
            if reprocess_all:
                var_docs = var_all_docs
            else:
                var_docs = [d for d in var_all_docs if d.status == "failed"]

        if not var_docs:
            print("No documents to reprocess.")
            return

        print(f"\nReprocessing {len(var_docs)} document(s)...\n")

        for var_i, var_doc in enumerate(var_docs, 1):
            print(
                f"  [{var_i}/{len(var_docs)}] doc_id={var_doc.doc_id} "
                f"'{var_doc.title}' (status={var_doc.status})"
            )
            try:
                fn_reprocess_document_task(var_doc.doc_id)
                print(f"         → Done")
            except Exception as e:
                print(f"         → FAILED: {e}")
                logger.error(f"reprocess_all_docs: doc_id={var_doc.doc_id} failed: {e}")
            time.sleep(0.5)  # Small pause between docs to avoid overwhelming the model

        print(f"\nReprocessing complete. {len(var_docs)} document(s) processed.")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Reprocess documents")
    parser.add_argument("--all",    action="store_true", help="Reprocess all docs (not just failed)")
    parser.add_argument("--doc-id", type=int,            help="Reprocess a single document by ID")
    args = parser.parse_args()
    fn_reprocess_all(reprocess_all=args.all, doc_id=args.doc_id)


if __name__ == "__main__":
    main()