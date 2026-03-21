"""
Tests de integración HTTP con FastAPI TestClient.

Prueban los endpoints REST completos incluyendo el manejo
de errores HTTP y la serialización del output.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


# Patch de los LLM adapters antes de importar app
@pytest.fixture
def app_client(mock_llm_provider, mock_external_platform, mock_tenant_config):
    """TestClient de FastAPI con dependencias mockeadas."""
    # Importar la app y el router
    from app.main import app
    from app.api import routers

    # Override singletons del router
    from app.core.state import InMemoryCache

    routers._cache = InMemoryCache()
    routers._yaml_config = mock_tenant_config

    # Override del LLM provider y plataforma externa
    def mock_get_llm():
        return mock_llm_provider

    def mock_get_orchestrator(llm_provider=None):
        from app.pipeline.orchestrator import PipelineOrchestrator
        from app.strategies.factory import StrategyFactory

        strategy_factory = StrategyFactory(
            adaptador_mensajeria=AsyncMock(),
        )
        return PipelineOrchestrator(
            cache_provider=routers._cache,
            strategy_factory=strategy_factory,
            llm_provider=mock_llm_provider,
            external_platform=mock_external_platform,
            yaml_config=mock_tenant_config,
        )

    app.dependency_overrides[routers._get_llm_provider] = mock_get_llm
    app.dependency_overrides[routers._get_orchestrator] = mock_get_orchestrator

    client = TestClient(app)
    yield client

    # Limpiar overrides
    app.dependency_overrides.clear()


# ── Test Happy Path ──


def test_api_happy_path(app_client):
    """POST /api/v1/solicitudes con datos válidos → 200 OK."""
    payload = {
        "compania": "GASES DEL ORINOCO",
        "solicitud_id": "REQ-API-001",
        "solicitud_descripcion": (
            "Mi nombre es Juana y mi cédula es 102045678. "
            "La estufa presenta fallas técnicas."
        ),
    }

    response = app_client.post("/api/v1/solicitudes", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["compania"] == "GASES DEL ORINOCO"
    assert data["solicitud_id"] == "REQ-API-001"
    assert data["solicitud_tipo"] == "Incidente técnico"
    assert data["solicitud_prioridad"] == "Alta"
    assert data["estado"] == "pendiente"
    assert data["solicitud_id_plataforma_externa"] is not None
    # Verificar alias Solicitud_fecha (S mayúscula)
    assert "Solicitud_fecha" in data


# ── Test Compañía No Encontrada ──


def test_api_company_not_found(app_client):
    """POST con compañía inexistente → 400 Bad Request."""
    payload = {
        "compania": "EMPRESA_FAKE",
        "solicitud_id": "REQ-API-ERR-001",
        "solicitud_descripcion": "Test",
    }

    response = app_client.post("/api/v1/solicitudes", json=payload)

    assert response.status_code == 400
    assert "no se encuentra" in response.json()["detail"].lower()


# ── Test Health Check ──


def test_api_health_check(app_client):
    """GET /api/v1/health → 200 OK."""
    response = app_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
