"""
Tests del PipelineOrchestrator aislado (sin HTTP).

Instancia el orquestador inyectándole mocks y verifica las
transiciones de estado y el flujo completo del pipeline.
"""

import pytest
from unittest.mock import AsyncMock

from app.api.schemas import SolicitudInput
from app.core.exceptions import CompanyNotFoundError, DuplicateRequestError


# ── Tests Happy Path ──


@pytest.mark.asyncio
async def test_pipeline_happy_path_gestion_externa(orchestrator, sample_request):
    """Pipeline completo para un caso que requiere gestión externa."""
    result = await orchestrator.run(sample_request)

    assert result.compania == "GASES DEL ORINOCO"
    assert result.solicitud_id == "REQ-TEST-001"
    assert result.solicitud_tipo == "Incidente técnico"
    assert result.solicitud_prioridad == "Alta"
    assert result.proximo_paso == "GESTIÓN EXTERNA"
    assert result.estado == "pendiente"
    assert result.solicitud_id_plataforma_externa == "ID-MOCK-123"
    assert result.solicitud_id_cliente == "CC"
    assert result.solicitud_tipo_id_cliente == "102045678"
    assert len(result.justificacion) > 0


@pytest.mark.asyncio
async def test_pipeline_happy_path_respuesta_directa(
    orchestrator, mock_llm_provider
):
    """Pipeline para un caso de baja prioridad → RESPUESTA DIRECTA."""
    # Configurar mock para prioridad Baja
    mock_llm_provider.prioritize.return_value = "Baja"

    request = SolicitudInput(
        compania="GASES DEL ORINOCO",
        solicitud_id="REQ-TEST-002",
        solicitud_descripcion="Consulta sobre factura del mes pasado.",
    )

    result = await orchestrator.run(request)

    assert result.proximo_paso == "RESPUESTA DIRECTA"
    assert result.estado == "cerrado"
    assert result.solicitud_id_plataforma_externa is None


# ── Tests Early Exit ──


@pytest.mark.asyncio
async def test_pipeline_early_exit_missing_info(
    orchestrator, mock_llm_provider
):
    """Early exit cuando falta información obligatoria."""
    # Simular que la extracción retorna un campo como null
    mock_llm_provider.extract_entities.return_value = {
        "cedula": "102045678",
        "nombre": "Juana",
        "problema": None,  # Falta el campo "problema"
    }

    request = SolicitudInput(
        compania="GASES DEL ORINOCO",
        solicitud_id="REQ-TEST-003",
        solicitud_descripcion="Solicitud sin detalle del problema.",
    )

    result = await orchestrator.run(request)

    assert result.proximo_paso == "CIERRE_POR_INFORMACION_INSUFICIENTE"
    assert result.estado == "cerrado"
    assert "Información incompleta" in result.justificacion


# ── Tests de Errores ──


@pytest.mark.asyncio
async def test_pipeline_company_not_found(orchestrator):
    """CompanyNotFoundError si la compañía no existe en YAML."""
    request = SolicitudInput(
        compania="EMPRESA_INEXISTENTE",
        solicitud_id="REQ-TEST-ERR-001",
        solicitud_descripcion="Test",
    )

    with pytest.raises(CompanyNotFoundError):
        await orchestrator.run(request)


@pytest.mark.asyncio
async def test_pipeline_duplicate_request(orchestrator, sample_request):
    """DuplicateRequestError al enviar la misma solicitud dos veces."""
    # Primera vez: OK
    await orchestrator.run(sample_request)

    # Segunda vez: debe fallar
    with pytest.raises(DuplicateRequestError):
        await orchestrator.run(sample_request)


# ── Test Fecha y Mapeo ──


@pytest.mark.asyncio
async def test_pipeline_output_has_date(orchestrator, sample_request):
    """El output debe incluir fecha en formato YYYY-MM-DD."""
    result = await orchestrator.run(sample_request)

    # Validar formato de fecha
    assert len(result.solicitud_fecha) == 10
    assert result.solicitud_fecha[4] == "-"
    assert result.solicitud_fecha[7] == "-"
