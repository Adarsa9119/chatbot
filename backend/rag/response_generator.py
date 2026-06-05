"""
response_generator.py — LLM response generation for the RAG pipeline.
Calls the OpenAI API with the built prompt and returns a structured response.

Change Tracker:
v1.0 — initial
"""

from typing import List, Optional
from openai import OpenAI

from config.settings import settings
from config.logging_config import logger
from rag.prompt_builder import fn_build_prompt, fn_build_session_title_prompt
from rag.guardrails import fn_check_output_guardrails

# ── OpenAI client (singleton) ──────────────────────────────────────────
_openai_client: Optional[OpenAI] = None


def _fn_get_client() -> OpenAI:
    """Lazily create and cache the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"OpenAI client initialized — model={settings.LLM_MODEL}")
    return _openai_client


def fn_generate_rag_response(
    context_chunks: List[dict],
    question: str,
    history: List[dict],
    system_override: Optional[str] = None,
) -> dict:
    """
    Generate an LLM answer from retrieved context chunks.

    Args:
        context_chunks:  List of chunk dicts (from vector search / reranker).
                         Each must have 'chunk_text' and optionally 'doc_title'.
        question:        User's current question.
        history:         Previous messages: [{"role": "user"|"assistant", "content": str}]
        system_override: Optional system prompt override (for testing).

    Returns:
        {
            "answer":         str,
            "was_modified":   bool,   # True if guardrails changed the answer
            "prompt_tokens":  int,
            "completion_tokens": int,
        }
    """
    var_client = _fn_get_client()

    # ── Build strict RAG prompt ─────────────────────────────────────────
    var_prompt = fn_build_prompt(
        context_chunks=context_chunks,
        question=question,
        history=history,
    )

    var_system = system_override or (
        "You are a secure document assistant. "
        "Answer ONLY from the context provided. "
        "If the answer is not in the context, respond with: "
        "'I don't know based on the selected documents.' "
        "Do NOT use external knowledge."
    )

    # ── LLM call ───────────────────────────────────────────────────────
    try:
        var_response = var_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": var_system},
                {"role": "user", "content": var_prompt},
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )

        var_raw_answer = var_response.choices[0].message.content.strip()
        var_prompt_tokens = var_response.usage.prompt_tokens
        var_completion_tokens = var_response.usage.completion_tokens

    except Exception as e:
        logger.error(f"fn_generate_rag_response LLM call failed: {e}")
        return {
            "answer": "I encountered an error generating a response. Please try again.",
            "was_modified": False,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }

    # ── Output guardrails ──────────────────────────────────────────────
    var_final_answer, var_was_modified = fn_check_output_guardrails(
        var_raw_answer, question
    )

    logger.info(
        f"fn_generate_rag_response: "
        f"prompt_tokens={var_prompt_tokens} "
        f"completion_tokens={var_completion_tokens} "
        f"modified={var_was_modified}"
    )

    return {
        "answer": var_final_answer,
        "was_modified": var_was_modified,
        "prompt_tokens": var_prompt_tokens,
        "completion_tokens": var_completion_tokens,
    }


def fn_generate_session_title(question: str) -> str:
    """
    Generate a short 3–6 word session title from the first question.
    Falls back to a truncated version of the question if LLM call fails.
    """
    var_client = _fn_get_client()
    var_prompt = fn_build_session_title_prompt(question)

    try:
        var_response = var_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": var_prompt}],
            max_tokens=20,
            temperature=0.3,
        )
        var_title = var_response.choices[0].message.content.strip().strip('"\'')
        # Cap at 60 chars to prevent overly long titles
        return var_title[:60] if var_title else question[:40]

    except Exception as e:
        logger.warning(f"fn_generate_session_title failed ({e}), using fallback")
        return question[:40].rstrip() + ("..." if len(question) > 40 else "")