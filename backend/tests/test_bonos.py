"""
Tests de los Bonos (+4%, +6%): Funcionalidades extra.

- Mensajería del Valle (+6%): Priorización por servicio externo
- Control de Duplicados (+4%): HTTP 409 en solicitudes repetidas
- Resiliencia Plataforma Externa (+4%): Tolerancia a fallas
"""

import pytest
from unittest.mock import AsyncMock

from app.api.schemas import SolicitudInput
from app.core.exceptions import ExternalPlatformError
from app.core.state import InMemoryCache
from app.pipeline.orchestrator import PipelineOrchestrator
from app.strategies.factory import StrategyFactory


# ── Bono +6%: Estrategia Mensajería del Valle ──


@pytest.mark.asyncio
async def test_bono_mensajeria_valle_uses_external_adapter(
    mock_llm_provider,
    mock_external_platform,
    mock_mensajeria_adapter,
    mock_tenant_config,
):
    """Mensajería del Valle DEBE usar el adaptador externo, NO el LLM."""
    # Configurar el mock del adaptador de mensajería para datos específicos
    mock_mensajeria_adapter.get_priority_from_client.return_value = "Alta"

    # Ajustar extract_entities para Mensajería del Valle
    mock_llm_provider.extract_entities.return_value = {
        "tipo_documento": "CC",
        "numero_documento": "987654321",
        "tipo_solicitud": "Retraso de envío",
    }
    mock_llm_provider.classify.return_value = "Retraso de envío"

    cache = InMemoryCache()
    strategy_factory = StrategyFactory(adaptador_mensajeria=mock_mensajeria_adapter)

    orchestrator = PipelineOrchestrator(
        cache_provider=cache,
        strategy_factory=strategy_factory,
        llm_provider=mock_llm_provider,
        external_platform=mock_external_platform,
        yaml_config=mock_tenant_config,
    )

    request = SolicitudInput(
        compania="MENSAJERIA DEL VALLE",
        solicitud_id="REQ-BONO-MV-001",
        solicitud_descripcion="Paquete retrasado 5 días, CC 987654321.",
    )

    result = await orchestrator.run(request)

    # El adaptador externo DEBE haber sido llamado
    mock_mensajeria_adapter.get_priority_from_client.assert_awaited_once()

    # El LLM prioritize NUNCA debe ser llamado para esta empresa
    mock_llm_provider.prioritize.assert_not_awaited()

    assert result.solicitud_prioridad == "Alta"


# ── Bono +4%: Control de Duplicados ──


@pytest.mark.asyncio
async def test_bono_duplicate_request_raises_409(orchestrator, sample_request):
    """Enviar la misma solicitud dos veces → la segunda debe fallar."""
    from app.core.exceptions import DuplicateRequestError

    # Primera vez: OK
    result1 = await orchestrator.run(sample_request)
    assert result1.solicitud_id == "REQ-TEST-001"

    # Segunda vez: DEBE lanzar DuplicateRequestError
    with pytest.raises(DuplicateRequestError) as exc_info:
        await orchestrator.run(sample_request)

    assert "REQ-TEST-001" in str(exc_info.value)


# ── Bono +4%: Resiliencia Plataforma Externa ──


@pytest.mark.asyncio
async def test_bono_external_platform_failure_resilience(
    mock_llm_provider,
    mock_tenant_config,
    mock_mensajeria_adapter,
):
    """Si la plataforma externa falla, el pipeline NO debe romperse."""
    # Mock de plataforma que falla
    failing_platform = AsyncMock()
    failing_platform.create_case.side_effect = ExternalPlatformError(
        "Simulación de fallo de red"
    )

    cache = InMemoryCache()
    strategy_factory = StrategyFactory(adaptador_mensajeria=mock_mensajeria_adapter)

    orchestrator = PipelineOrchestrator(
        cache_provider=cache,
        strategy_factory=strategy_factory,
        llm_provider=mock_llm_provider,
        external_platform=failing_platform,
        yaml_config=mock_tenant_config,
    )

    request = SolicitudInput(
        compania="GASES DEL ORINOCO",
        solicitud_id="REQ-BONO-FAIL-001",
        solicitud_descripcion=(
            "Juana, cédula 102045678. Falla técnica en estufa urgente."
        ),
    )

    # El pipeline DEBE completarse sin lanzar excepción
    result = await orchestrator.run(request)

    # Verificar que el estado es correcto a pesar del fallo
    assert result.estado == "pendiente"  # GESTIÓN EXTERNA → pendiente
    assert result.solicitud_id_plataforma_externa is None  # No se creó el caso
    assert "Falla de red" in result.justificacion  # Debe mencionar el fallo
