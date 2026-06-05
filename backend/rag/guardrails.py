"""
guardrails.py — Input and output guardrails for the RAG pipeline.

Input guardrails:  validate / sanitize user questions before processing.
Output guardrails: detect and flag LLM responses that may be unsafe or
                   out-of-scope.

Change Tracker:
v1.0 — initial
"""

import re
from typing import Optional
from config.logging_config import logger

# ── Configurable limits ────────────────────────────────────────────────
MAX_QUESTION_LENGTH = 2000   # Characters
MIN_QUESTION_LENGTH = 3      # Characters

# Patterns that suggest prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore (all |previous |above |prior )?instructions",
    r"disregard (all |previous |above )?",
    r"you are now",
    r"pretend (you are|to be)",
    r"forget (everything|all|your|the)",
    r"act as (an? )?(unrestricted|unfiltered|jailbreak)",
    r"do anything now",
    r"(system|admin) (prompt|override|access)",
    r"<\s*script\s*>",         # XSS attempt
    r"--\s*(drop|delete|select|insert|update)",  # SQL injection pattern
]
_COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

# Patterns in LLM output that suggest the model went off-context
_OFF_CONTEXT_PHRASES = [
    "as a language model",
    "as an ai",
    "i cannot access the internet",
    "i don't have access to real-time",
    "based on my training data",
    "according to my knowledge cutoff",
]


def fn_apply_guardrails(question: str) -> tuple[bool, Optional[str]]:
    """
    Apply input guardrails to a user question.

    Returns:
        (True, None)          — question is safe to process
        (False, reason_str)   — question was blocked, reason given

    Checks:
    1. Length bounds
    2. Empty / whitespace-only
    3. Prompt injection patterns
    """
    # ── Length check ───────────────────────────────────────────────────
    if not question or not question.strip():
        return False, "Question cannot be empty."

    if len(question.strip()) < MIN_QUESTION_LENGTH:
        return False, f"Question is too short (minimum {MIN_QUESTION_LENGTH} characters)."

    if len(question) > MAX_QUESTION_LENGTH:
        return (
            False,
            f"Question is too long (maximum {MAX_QUESTION_LENGTH} characters). "
            f"Please be more concise.",
        )

    # ── Injection detection ────────────────────────────────────────────
    for var_pattern in _COMPILED_INJECTION:
        if var_pattern.search(question):
            logger.warning(
                f"fn_apply_guardrails: injection pattern detected "
                f"in question (len={len(question)})"
            )
            return (
                False,
                "Your question contains patterns that are not allowed. "
                "Please rephrase your question.",
            )

    return True, None


def fn_check_output_guardrails(answer: str, question: str) -> tuple[str, bool]:
    """
    Apply output guardrails to the LLM response.

    Returns:
        (final_answer, was_modified)

    Checks:
    1. Detects off-context phrasing (model went beyond document scope)
    2. Trims excessively long responses
    3. Ensures the refusal phrase is consistent when documents have no answer
    """
    var_modified = False
    var_answer = answer.strip()

    # ── Refusal normalisation ──────────────────────────────────────────
    # If the model says it doesn't know in some other way, normalize it
    _REFUSAL_VARIANTS = [
        "i don't know",
        "i do not know",
        "i cannot answer",
        "no information available",
        "not mentioned in the document",
        "not found in the context",
        "not present in the provided",
    ]
    for var_phrase in _REFUSAL_VARIANTS:
        if var_phrase in var_answer.lower() and len(var_answer) < 200:
            # Normalize to canonical refusal
            if var_phrase not in var_answer.lower()[:60]:
                var_answer = "I don't know based on the selected documents."
                var_modified = True
                break

    # ── Off-context detection ──────────────────────────────────────────
    for var_phrase in _OFF_CONTEXT_PHRASES:
        if var_phrase in var_answer.lower():
            logger.warning(
                f"fn_check_output_guardrails: off-context phrase detected: '{var_phrase}'"
            )
            # Replace with standard refusal rather than leaking model meta-info
            var_answer = "I don't know based on the selected documents."
            var_modified = True
            break

    # ── Max response length cap ────────────────────────────────────────
    MAX_ANSWER_CHARS = 8000
    if len(var_answer) > MAX_ANSWER_CHARS:
        var_answer = var_answer[:MAX_ANSWER_CHARS] + "...\n\n[Response truncated]"
        var_modified = True
        logger.warning("fn_check_output_guardrails: answer truncated (exceeded max length)")

    return var_answer, var_modified


def fn_sanitize_question(question: str) -> str:
    """
    Light sanitization of question text before processing:
    - Strip leading/trailing whitespace
    - Collapse multiple consecutive spaces
    - Remove null bytes
    """
    var_q = question.strip()
    var_q = var_q.replace("\x00", "")
    var_q = re.sub(r"[ \t]{2,}", " ", var_q)
    return var_q