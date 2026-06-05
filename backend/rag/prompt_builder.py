"""
prompt_builder.py — Builds strict RAG prompts with conversation history.
FIXED: Original spec didn't include conversation history — multi-turn chat was broken.
Change Tracker:
  v1.0 — initial
"""

from typing import List


def fn_build_prompt(
    context_chunks: List[dict],
    question: str,
    history: List[dict],
) -> str:
    """
    Build the RAG prompt for the LLM.
    FIXED: Includes last 6 messages from conversation history.

    Args:
        context_chunks: list of { chunk_text, doc_title, ... } from vector search
        question: current user question
        history: list of { role: 'user'|'assistant', content: str }

    Returns:
        Formatted prompt string.
    """
    # ── Build context section ────────────────────────────────
    var_context_parts = []
    for var_i, var_chunk in enumerate(context_chunks, 1):
        var_doc_label = f"[Source {var_i}: {var_chunk.get('doc_title', 'Document')}]"
        var_context_parts.append(f"{var_doc_label}\n{var_chunk['chunk_text']}")

    var_context = "\n\n---\n\n".join(var_context_parts) if var_context_parts else "No documents selected."

    # ── Build history section (last 6 messages = 3 exchanges) ─
    var_history_lines = []
    for var_msg in history[-6:]:  # FIXED: last 6 messages
        var_role_label = "USER" if var_msg["role"] == "user" else "ASSISTANT"
        var_history_lines.append(f"{var_role_label}: {var_msg['content']}")

    var_history_text = "\n".join(var_history_lines) if var_history_lines else ""

    # ── Final strict RAG prompt ──────────────────────────────
    var_prompt_parts = [
        "You are a secure document assistant.",
        "Answer ONLY from the context provided below.",
        "If the answer is not present in the context, respond EXACTLY with:",
        '  "I don\'t know based on the selected documents."',
        "Do NOT use external knowledge. Do NOT make up information.",
        "",
        "=== CONTEXT (from uploaded documents) ===",
        var_context,
    ]

    if var_history_text:
        var_prompt_parts += [
            "",
            "=== CONVERSATION HISTORY ===",
            var_history_text,
        ]

    var_prompt_parts += [
        "",
        "=== CURRENT QUESTION ===",
        f"USER: {question}",
        "",
        "ASSISTANT:",
    ]

    return "\n".join(var_prompt_parts)


def fn_build_session_title_prompt(first_question: str) -> str:
    """
    Generate a short title for a chat session from the first question.
    """
    return (
        f"Generate a short title (3-6 words) for a chat session "
        f"that starts with this question: '{first_question}'. "
        f"Return only the title, no quotes or punctuation."
    )