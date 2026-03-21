"""
Tests del LLMManager (Fallback Groq → Gemini).

Verifica la recuperación automática cuando el proveedor
primario falla, sin llamadas HTTP reales.
"""

import pytest
from unittest.mock import AsyncMock

from app.adapters.llm_manager import LLMManager
from app.core.exceptions import LLMOutputError


@pytest.mark.asyncio
async def test_fallback_groq_fails_gemini_succeeds():
    """Si Groq falla, el Manager debe usar Gemini automáticamente."""
    mock_groq = AsyncMock()
    mock_gemini = AsyncMock()

    # Groq falla en classify
    mock_groq.classify.side_effect = LLMOutputError("Groq", "Rate limit")

    # Gemini responde exitosamente
    mock_gemini.classify.return_value = "Incidente técnico"

    manager = LLMManager(primary=mock_groq, secondary=mock_gemini)

    result = await manager.classify("Texto de prueba", ["Incidente técnico"])

    assert result == "Incidente técnico"
    mock_groq.classify.assert_awaited_once()
    mock_gemini.classify.assert_awaited_once()


@pytest.mark.asyncio
async def test_primary_succeeds_secondary_not_called():
    """Si Groq funciona, Gemini NO debe ser llamado."""
    mock_groq = AsyncMock()
    mock_gemini = AsyncMock()

    mock_groq.prioritize.return_value = "Alta"

    manager = LLMManager(primary=mock_groq, secondary=mock_gemini)

    result = await manager.prioritize("Texto urgente", "Incidente")

    assert result == "Alta"
    mock_groq.prioritize.assert_awaited_once()
    mock_gemini.prioritize.assert_not_awaited()


@pytest.mark.asyncio
async def test_both_providers_fail_raises():
    """Si AMBOS proveedores fallan, debe lanzar la última excepción."""
    mock_groq = AsyncMock()
    mock_gemini = AsyncMock()

    mock_groq.justify.side_effect = LLMOutputError("Groq", "Timeout")
    mock_gemini.justify.side_effect = LLMOutputError("Gemini", "Timeout")

    manager = LLMManager(primary=mock_groq, secondary=mock_gemini)

    with pytest.raises(LLMOutputError):
        await manager.justify("Texto", "Categoría", "Alta")


@pytest.mark.asyncio
async def test_fallback_on_extract_entities():
    """Verifica fallback en extract_entities."""
    mock_groq = AsyncMock()
    mock_gemini = AsyncMock()

    mock_groq.extract_entities.side_effect = Exception("Connection error")
    mock_gemini.extract_entities.return_value = {
        "cedula": "123456",
        "nombre": "Test",
    }

    manager = LLMManager(primary=mock_groq, secondary=mock_gemini)

    result = await manager.extract_entities("Texto", ["cedula", "nombre"])

    assert result["cedula"] == "123456"
    mock_groq.extract_entities.assert_awaited_once()
    mock_gemini.extract_entities.assert_awaited_once()
