"""
LLM client abstraction.

Uses Groq's free-tier API (https://console.groq.com) when a GROQ_API_KEY
is available. If no key is configured (or the call fails for any reason,
e.g. no internet), it transparently falls back to a small deterministic
"mock LLM" so the rest of the autonomous pipeline (planning, execution,
document generation) can still be demonstrated end-to-end offline.

Swap in any other free/local model (Ollama, LM Studio, Gemini free tier,
etc.) by editing `_call_groq` / adding a new `_call_xxx` method and
wiring it up in `complete()`.
"""

import os
import json
import re
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("agent.llm")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class LLMClient:
    def __init__(self):
        self.use_groq = bool(GROQ_API_KEY)
        self._groq_client = None
        if self.use_groq:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=GROQ_API_KEY)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not init Groq client, falling back to mock LLM: %s", exc)
                self.use_groq = False

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Return raw text completion from whichever backend is active."""
        if self.use_groq:
            try:
                return self._call_groq(system_prompt, user_prompt, json_mode)
            except Exception as exc:
                logger.warning("Groq call failed (%s). Falling back to mock LLM for this call.", exc)
        return self._call_mock(system_prompt, user_prompt, json_mode)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Call the LLM and parse a JSON object out of the response robustly."""
        raw = self.complete(system_prompt, user_prompt, json_mode=True)
        return self._extract_json(raw)

    # ------------------------------------------------------------------ #
    # Backends
    # ------------------------------------------------------------------ #
    def _call_groq(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        kwargs = dict(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=3000,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self._groq_client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content

    def _call_mock(self, system_prompt: str, user_prompt: str, json_mode: bool) -> str:
        """
        Deterministic offline stand-in for an LLM. It does simple keyword
        matching on the prompts so the autonomous pipeline still produces
        sensible (if generic) plans/content without any external API.
        """
        from agent.mock_llm import mock_respond
        return mock_respond(system_prompt, user_prompt, json_mode)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(json)?", "", raw.strip(), flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw.strip()).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to locate the first {...} block
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise


llm_client = LLMClient()
