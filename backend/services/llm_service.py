"""
llm_service.py — OpenAI GPT-4o-mini wrapper with retry, timeout, and error handling.
Separates LLM concerns from the RAG orchestration in rag_service.py.
Change Tracker:
  v1.0 — initial
"""

import time
from typing import Optional, List
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError
from config.settings import settings
from config.logging_config import logger


# ── Retry settings ───────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# ── Fallback message ─────────────────────────────────────────
FALLBACK_ANSWER = (
    "I'm having trouble generating a response right now. "
    "Please try again in a moment."
)


class LlmService:
    """
    Wraps OpenAI API calls with:
      - Configurable model (gpt-4o-mini)
      - Retry logic for rate limits and timeouts
      - Strict temperature=0 for deterministic document answers
      - Session title generation
      - Token usage logging
    """

    def __init__(self):
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def fn_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = None,
        temperature: float = None,
    ) -> str:
        """
        Core completion function — calls GPT-4o-mini with retry.
        Returns the assistant's response text.

        Args:
            system_prompt: the system instruction (role, rules)
            user_prompt:   the full user message (prompt with context)
            max_tokens:    override settings.LLM_MAX_TOKENS if needed
            temperature:   override settings.LLM_TEMPERATURE if needed
        """
        var_max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        var_temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE

        var_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for var_attempt in range(1, MAX_RETRIES + 1):
            try:
                var_response = self._client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=var_messages,
                    max_tokens=var_max_tokens,
                    temperature=var_temperature,
                    timeout=30,
                )

                var_answer = var_response.choices[0].message.content.strip()
                var_usage = var_response.usage

                logger.info(
                    f"LLM response: tokens_in={var_usage.prompt_tokens} "
                    f"tokens_out={var_usage.completion_tokens} "
                    f"model={settings.LLM_MODEL}"
                )
                return var_answer

            except RateLimitError as e:
                logger.warning(
                    f"LLM rate limit (attempt {var_attempt}/{MAX_RETRIES}): {e}"
                )
                if var_attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * var_attempt)
                else:
                    logger.error("LLM rate limit — max retries exceeded")
                    return FALLBACK_ANSWER

            except APITimeoutError as e:
                logger.warning(
                    f"LLM timeout (attempt {var_attempt}/{MAX_RETRIES}): {e}"
                )
                if var_attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    return FALLBACK_ANSWER

            except APIConnectionError as e:
                logger.error(f"LLM connection error: {e}")
                return FALLBACK_ANSWER

            except Exception as e:
                logger.error(f"fn_complete unexpected error: {e}")
                return FALLBACK_ANSWER

        return FALLBACK_ANSWER

    def fn_answer_from_context(
        self,
        context: str,
        question: str,
        history_text: str = "",
    ) -> str:
        """
        RAG-specific completion — strict document-only answering.
        Passes context, optional history, and the question.
        """
        var_system = (
            "You are SecureDoc, a secure document assistant. "
            "Answer ONLY from the provided document context. "
            "If the answer is not in the context, respond exactly: "
            "\"I don't know based on the selected documents.\" "
            "Never use external knowledge. Never make up information."
        )

        var_user_parts = ["=== DOCUMENT CONTEXT ===", context]
        if history_text:
            var_user_parts += ["", "=== CONVERSATION HISTORY ===", history_text]
        var_user_parts += ["", "=== QUESTION ===", question]

        var_prompt = "\n".join(var_user_parts)
        return self.fn_complete(var_system, var_prompt)

    def fn_generate_session_title(self, first_question: str) -> str:
        """
        Generate a short, descriptive title for a chat session.
        Called after the first question in a new session.
        """
        var_system = (
            "Generate a short chat session title (3-6 words) based on the user's question. "
            "Return ONLY the title. No quotes, no punctuation at the end."
        )
        var_title = self.fn_complete(
            system_prompt=var_system,
            user_prompt=first_question,
            max_tokens=20,
            temperature=0.3,
        )
        # Fallback if title generation fails
        if not var_title or len(var_title) > 80:
            return first_question[:60] + "..." if len(first_question) > 60 else first_question

        return var_title.strip()

    def fn_is_available(self) -> bool:
        """
        Lightweight check to verify the OpenAI API is reachable.
        Returns True/False — used by health check endpoint.
        """
        try:
            self._client.models.retrieve(settings.LLM_MODEL)
            return True
        except Exception as e:
            logger.warning(f"LLM availability check failed: {e}")
            return False


# ── Singleton ────────────────────────────────────────────────
llm_service = LlmService()