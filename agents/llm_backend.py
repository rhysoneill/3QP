"""
llm_backend.py — OpenAI backend for Phase C narrative rendering.

Usage:
    from agents.llm_backend import OpenAIBackend
    backend = OpenAIBackend()          # reads OPENAI_API_KEY from environment
    backend = OpenAIBackend(model="gpt-4o")  # override model

The NarrativeRenderer accepts any backend with a .complete(prompt) method,
so this can be swapped for another LLM provider without changing the renderer.

API key is NEVER stored in code. Set it as an environment variable:
    Windows:  set OPENAI_API_KEY=sk-...
    macOS/Linux: export OPENAI_API_KEY=sk-...
    Or place it in a .env file at the repo root (see .env.example).
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Load .env file from repo root if python-dotenv is installed
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # dotenv not installed — rely on environment variable being set manually

logger = logging.getLogger(__name__)

# Default model — gpt-4o-mini is cost-effective and sufficient for narrative rendering.
# Override with model="gpt-4o" for higher quality prose.
DEFAULT_MODEL = "gpt-4o-mini"

# System prompt enforcing the non-causal, read-only constraint.
_SYSTEM_PROMPT = (
    "You are a narrative renderer for a behavioral simulation. "
    "Your only job is to translate pre-selected actions and state summaries "
    "into human-readable text. "
    "Output ONLY the requested text — no labels, no prefixes, no extra commentary. "
    "Never suggest different actions. Never modify state. Never speculate beyond "
    "what the provided state and action describe."
)


class OpenAIBackend:
    """
    Thin wrapper around the OpenAI chat completions API.

    Used by NarrativeRenderer as the LLM backend for Phase C output.
    Falls back gracefully (returns None) on any API error so the
    renderer can fall through to its rule-based templates.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 2,
    ):
        """
        Initialise the backend.

        Args:
            model:       OpenAI model name (default: gpt-4o-mini).
            api_key:     API key. If None, reads OPENAI_API_KEY from environment.
            temperature: Sampling temperature (0 = deterministic, 1 = creative).
            max_retries: Number of retry attempts on transient errors.
        """
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "No OpenAI API key found. "
                "Set the OPENAI_API_KEY environment variable or pass api_key= directly."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )

        self._client = OpenAI(api_key=key)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

    def complete(self, prompt: str, max_tokens: int = 120) -> Optional[str]:
        """
        Send a prompt to the model and return the response text.

        Returns None on any error (allows NarrativeRenderer to fall back
        to rule-based templates transparently).

        Args:
            prompt:     The user prompt (already formatted by NarrativePrompts).
            max_tokens: Maximum response length.

        Returns:
            Response string, or None if the call failed.
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=self.temperature,
                )
                text = response.choices[0].message.content
                return text.strip() if text else None

            except Exception as exc:
                if attempt < self.max_retries:
                    logger.warning("OpenAI call failed (attempt %d): %s", attempt + 1, exc)
                else:
                    logger.error(
                        "OpenAI call failed after %d attempts: %s — "
                        "falling back to rule-based narrative.",
                        self.max_retries + 1, exc
                    )
                    return None

        return None  # unreachable, but satisfies type checkers
