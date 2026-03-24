"""
Adaptador para Groq LLM (llama3-70b-8192).

Implementa ILLMProvider usando AsyncGroq con temperatura 0.0
para máxima precisión analítica.
"""

import json
import logging

from groq import AsyncGroq
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

# Nombre del proveedor para trazabilidad en errores
PROVIDER_NAME = "Groq"


from app.adapters.utils import clean_json_response as _clean_json_response


class GroqAdapter(ILLMProvider):
    """Adaptador concreto para el proveedor Groq."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=api_key or settings.GROQ_API_KEY)
        self._model = "llama-3.3-70b-versatile"

    async def _call_llm(self, system_prompt: str, user_text: str) -> str:
        """Llamada genérica al LLM con temperatura 0."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
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
