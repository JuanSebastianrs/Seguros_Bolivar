"""
Adaptador para Google Gemini (gemini-2.5-flash).

Implementa ILLMProvider usando el SDK de Google GenAI.
Autenticación vía SDK (Application Default Credentials) o API key.
"""

import json
import logging
import re

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import LLMOutputError
from app.domain.interfaces import ILLMProvider
from app.domain.prompts import (
    prompt_clasificacion,
    prompt_extraccion,
    prompt_justificacion,
    prompt_priorizacion,
)
from app.domain.schemas_llm import (
    ClasificacionResponse,
    JustificacionResponse,
    PrioridadResponse,
)

logger = logging.getLogger(__name__)

PROVIDER_NAME = "Gemini"


def _clean_json_response(text: str) -> str:
    """Limpia bloques de Markdown del output del LLM."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


class GeminiAdapter(ILLMProvider):
    """Adaptador concreto para Google Gemini."""

    def __init__(self, api_key: str | None = None) -> None:
        import google.generativeai as genai

        settings = get_settings()
        key = api_key or settings.GEMINI_API_KEY

        if key:
            genai.configure(api_key=key)
        # Si no hay key, usa Application Default Credentials del SDK

        self._model = genai.GenerativeModel("gemini-2.5-flash")

    async def _call_llm(self, system_prompt: str, user_text: str) -> str:
        """Llamada al modelo Gemini."""
        import asyncio

        # google-generativeai no tiene API async nativa, usamos run_in_executor
        full_prompt = f"{system_prompt}\n\n---\n\nSolicitud del cliente:\n{user_text}"

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.0,
                    "response_mime_type": "application/json",
                },
            ),
        )

        raw = response.text or ""
        return _clean_json_response(raw)

    async def extract_entities(self, text: str, required_fields: list[str]) -> dict:
        """Paso 1: Extracción de entidades."""
        system_prompt = prompt_extraccion(required_fields)
        raw_json = await self._call_llm(system_prompt, text)

        try:
            data = json.loads(raw_json)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[{PROVIDER_NAME}] JSON inválido en extracción: {e}")
            raise LLMOutputError(PROVIDER_NAME, f"JSON inválido: {raw_json[:200]}")

    async def classify(self, text: str, categories: list[str]) -> str:
        """Paso 2: Clasificación."""
        system_prompt = prompt_clasificacion(categories)
        raw_json = await self._call_llm(system_prompt, text)

        try:
            result = ClasificacionResponse.model_validate_json(raw_json)
            return result.categoria
        except (ValidationError, Exception) as e:
            logger.error(f"[{PROVIDER_NAME}] Validación fallida en clasificación: {e}")
            raise LLMOutputError(PROVIDER_NAME, f"Clasificación inválida: {raw_json[:200]}")

    async def prioritize(self, text: str, category: str) -> str:
        """Paso 3: Priorización."""
        system_prompt = prompt_priorizacion(category)
        raw_json = await self._call_llm(system_prompt, text)

        try:
            result = PrioridadResponse.model_validate_json(raw_json)
            return result.prioridad
        except (ValidationError, Exception) as e:
            logger.error(f"[{PROVIDER_NAME}] Validación fallida en priorización: {e}")
            raise LLMOutputError(PROVIDER_NAME, f"Prioridad inválida: {raw_json[:200]}")

    async def justify(self, text: str, category: str, priority: str) -> str:
        """Paso 4: Justificación."""
        system_prompt = prompt_justificacion(category, priority)
        raw_json = await self._call_llm(system_prompt, text)

        try:
            result = JustificacionResponse.model_validate_json(raw_json)
            return result.justificacion
        except (ValidationError, Exception) as e:
            logger.error(f"[{PROVIDER_NAME}] Validación fallida en justificación: {e}")
            raise LLMOutputError(PROVIDER_NAME, f"Justificación inválida: {raw_json[:200]}")
