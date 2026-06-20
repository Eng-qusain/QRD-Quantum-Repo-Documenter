"""
AI Documenter — Generates structured documentation for source files.
API key is fully optional. Falls back to stub documentation when not configured.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior software engineer generating structured technical documentation.
Analyze the provided source code and return ONLY valid JSON (no markdown, no explanation).

Return this exact JSON structure:
{
  "summary": "One-sentence description of what this file does",
  "purpose": "2-3 sentence explanation of the file's role in the project",
  "key_functions": ["function or class name: what it does", ...],
  "inputs": ["description of inputs/parameters/arguments", ...],
  "outputs": ["description of return values/outputs/side effects", ...],
  "dependencies": ["package or module name", ...],
  "complexity": "Low|Medium|High|Very High",
  "notes": "Any important notes about design decisions, gotchas, or patterns used"
}"""


class AIDocumenter:
    """
    Generates AI documentation for source files.

    API key is OPTIONAL:
    - With Anthropic key  → uses Claude
    - With OpenAI key     → uses GPT-4o-mini
    - Without any key     → returns clean stub documentation (no crash)
    """

    def __init__(self, settings) -> None:
        self._settings = settings
        self._client = None
        self._provider = "none"
        self._setup_client()

    def _setup_client(self) -> None:
        """Initialize AI client only if a key is available."""
        try:
            if self._settings.anthropic_api_key:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self._settings.anthropic_api_key
                )
                self._provider = "anthropic"
                logger.info("AI provider: Anthropic Claude")
                return
        except ImportError:
            logger.warning("anthropic package not installed — run: pip install anthropic")

        try:
            if self._settings.openai_api_key:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self._settings.openai_api_key
                )
                self._provider = "openai"
                logger.info("AI provider: OpenAI")
                return
        except ImportError:
            logger.warning("openai package not installed — run: pip install openai")

        # No key configured — stub mode (completely fine)
        self._provider = "none"
        logger.info("AI provider: none (no API key configured — AI docs disabled)")

    @property
    def is_available(self) -> bool:
        return self._provider != "none" and self._client is not None

    async def document_file(
        self,
        file_path: str,
        content: str,
        language: str,
        max_content_chars: int = 8000,
    ) -> dict:
        """
        Generate documentation for a source file.
        Always returns a valid dict — never raises.
        """
        if not self.is_available:
            return self._stub_documentation(file_path, language)

        truncated = content[:max_content_chars]
        if len(content) > max_content_chars:
            truncated += f"\n\n... [truncated at {max_content_chars} chars]"

        user_message = (
            f"File: {file_path}\n"
            f"Language: {language}\n\n"
            f"```{language}\n{truncated}\n```"
        )

        try:
            if self._provider == "anthropic":
                return await self._call_anthropic(user_message)
            elif self._provider == "openai":
                return await self._call_openai(user_message)
        except Exception as e:
            logger.warning(f"AI documentation failed for {file_path}: {e}")

        return self._stub_documentation(file_path, language)

    async def _call_anthropic(self, user_message: str) -> dict:
        response = await self._client.messages.create(
            model=self._settings.ai_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return self._parse_json_response(response.content[0].text)

    async def _call_openai(self, user_message: str) -> dict:
        response = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
        return self._parse_json_response(response.choices[0].message.content or "{}")

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?\n?", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "summary": "Could not parse AI response",
                "purpose": "",
                "key_functions": [],
                "inputs": [],
                "outputs": [],
                "dependencies": [],
                "complexity": "Unknown",
                "notes": raw[:300],
            }

    @staticmethod
    def _stub_documentation(file_path: str, language: str) -> dict:
        """Clean placeholder returned when no API key is configured."""
        return {
            "summary": f"{file_path.split('/')[-1]} — AI summary not available",
            "purpose": "Add ANTHROPIC_API_KEY or OPENAI_API_KEY to backend/.env to enable AI documentation.",
            "key_functions": [],
            "inputs": [],
            "outputs": [],
            "dependencies": [],
            "complexity": "Unknown",
            "notes": f"Language detected: {language}. AI features are optional — all PDF export features work without an API key.",
        }
