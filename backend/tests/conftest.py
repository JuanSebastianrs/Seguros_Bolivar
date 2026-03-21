"""
Configuración de pytest y fixtures compartidos.

Provee mocks y fakes de todas las dependencias externas
para que los tests no hagan llamadas HTTP reales.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from app.api.schemas import SolicitudInput
from app.core.state import InMemoryCache
from app.domain.interfaces import ILLMProvider, IExternalPlatform
from app.domain.models import ProcesamientoEstado
from app.strategies.factory import StrategyFactory
from app.adapters.mensajeria_api import MensajeriaValleAdapter
from app.pipeline.orchestrator import PipelineOrchestrator


# ── Configuración YAML de prueba ──

@pytest.fixture
def mock_tenant_config() -> dict:
    """Configuración YAML completa para tests."""
    return {
        "empresas": {
            "GASES DEL ORINOCO": {
                "metodo_prioridad": "ia",
                "campos_obligatorios": ["cedula", "nombre", "problema"],
                "categorias": [
                    "Incidente técnico",
                    "Reclamo de facturación",
                    "Consulta administrativa",
                ],
                "reglas_enrutamiento": {
                    "Incidente técnico": {
                        "Alta": "GESTIÓN EXTERNA",
                        "Media": "GESTIÓN EXTERNA",
                        "Baja": "RESPUESTA DIRECTA",
                    },
                    "Reclamo de facturación": {
                        "Alta": "GESTIÓN EXTERNA",
                        "Media": "RESPUESTA DIRECTA",
                        "Baja": "RESPUESTA DIRECTA",
                    },
                    "Consulta administrativa": {
                        "Alta": "RESPUESTA DIRECTA",
                        "Media": "RESPUESTA DIRECTA",
                        "Baja": "RESPUESTA DIRECTA",
                    },
                },
            },
            "MENSAJERIA DEL VALLE": {
                "metodo_prioridad": "externo",
                "campos_obligatorios": [
                    "tipo_documento",
                    "numero_documento",
                    "tipo_solicitud",
                ],
                "categorias": [
                    "Retraso de envío",
                    "Dañado en tránsito",
                ],
                "reglas_enrutamiento": {
                    "Retraso de envío": {
                        "Alta": "GESTIÓN EXTERNA",
                        "Media": "GESTIÓN EXTERNA",
                        "Baja": "RESPUESTA DIRECTA",
                    },
                    "Dañado en tránsito": {
                        "Alta": "GESTIÓN EXTERNA",
                        "Media": "GESTIÓN EXTERNA",
                        "Baja": "RESPUESTA DIRECTA",
                    },
                },
            },
        }
    }


# ── Mock del LLM Provider ──

@pytest.fixture
def mock_llm_provider() -> AsyncMock:
    """Mock de ILLMProvider con respuestas predefinidas."""
    mock = AsyncMock(spec=ILLMProvider)

    # Paso 1: Extracción
    mock.extract_entities.return_value = {
        "cedula": "102045678",
        "nombre": "Juana",
        "problema": "fallas en estufa de gas",
    }

    # Paso 2: Clasificación
    mock.classify.return_value = "Incidente técnico"

    # Paso 3: Priorización
    mock.prioritize.return_value = "Alta"

    # Paso 4: Justificación
    mock.justify.return_value = (
        "Se detecta falla técnica en estufa de gas que requiere "
        "intervención presencial."
    )

    return mock


# ── Mock de Plataforma Externa ──

@pytest.fixture
def mock_external_platform() -> AsyncMock:
    """Mock de IExternalPlatform."""
    mock = AsyncMock(spec=IExternalPlatform)
    mock.create_case.return_value = "ID-MOCK-123"
    return mock


# ── Mock del Adaptador de Mensajería ──

@pytest.fixture
def mock_mensajeria_adapter() -> AsyncMock:
    """Mock del MensajeriaValleAdapter."""
    mock = AsyncMock(spec=MensajeriaValleAdapter)
    mock.get_priority_from_client.return_value = "Alta"
    return mock


# ── Caché limpio por test ──

@pytest.fixture
def clean_cache() -> InMemoryCache:
    """InMemoryCache limpio para cada test."""
    cache = InMemoryCache()
    yield cache
    cache.clear()  # Limpieza post-test


# ── Request de ejemplo ──

@pytest.fixture
def sample_request() -> SolicitudInput:
    """Solicitud de ejemplo para Gases del Orinoco."""
    return SolicitudInput(
        compania="GASES DEL ORINOCO",
        solicitud_id="REQ-TEST-001",
        solicitud_descripcion=(
            "Mi nombre es Juana y mi numero de cédula es 102045678. "
            "Solicito una revision urgente porque la estufa que compre "
            "hace 2 semanas presenta fallas."
        ),
    )


@pytest.fixture
def sample_request_mensajeria() -> SolicitudInput:
    """Solicitud de ejemplo para Mensajería del Valle."""
    return SolicitudInput(
        compania="MENSAJERIA DEL VALLE",
        solicitud_id="REQ-TEST-MV-001",
        solicitud_descripcion=(
            "Tipo documento CC, número 987654321. "
            "Tengo un retraso de envío de mi paquete desde hace 5 días."
        ),
    )


# ── Orquestador pre-configurado ──

@pytest.fixture
def orchestrator(
    clean_cache,
    mock_llm_provider,
    mock_external_platform,
    mock_mensajeria_adapter,
    mock_tenant_config,
) -> PipelineOrchestrator:
    """Orquestador con todas las dependencias mockeadas."""
    strategy_factory = StrategyFactory(
        adaptador_mensajeria=mock_mensajeria_adapter,
    )
    return PipelineOrchestrator(
        cache_provider=clean_cache,
        strategy_factory=strategy_factory,
        llm_provider=mock_llm_provider,
        external_platform=mock_external_platform,
        yaml_config=mock_tenant_config,
    )
