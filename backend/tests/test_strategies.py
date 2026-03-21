"""
Tests unitarios puros de las Estrategias (Hexágono Central).

Prueban DefaultStrategy y MensajeriaValleStrategy aisladas
del framework HTTP, usando solo mocks de las interfaces.
"""

import pytest
from unittest.mock import AsyncMock

from app.api.schemas import SolicitudInput
from app.domain.interfaces import ILLMProvider
from app.domain.models import ProcesamientoEstado
from app.strategies.base import DefaultStrategy
from app.strategies.mensajeria_valle import MensajeriaValleStrategy


# ── Tests de DefaultStrategy ──


class TestDefaultStrategy:
    """Tests para la estrategia genérica basada en YAML."""

    def _make_estado(self, datos_extraidos: dict, tenant_config: dict) -> ProcesamientoEstado:
        """Helper para crear un ProcesamientoEstado de prueba."""
        return ProcesamientoEstado(
            request_original=SolicitudInput(
                compania="TEST",
                solicitud_id="REQ-S-001",
                solicitud_descripcion="Test solicitud",
            ),
            tenant_config=tenant_config,
            datos_extraidos=datos_extraidos,
        )

    def test_validate_requirements_all_present(self):
        """validate_requirements retorna True cuando todos los campos están presentes."""
        strategy = DefaultStrategy()
        config = {"campos_obligatorios": ["cedula", "nombre", "problema"]}
        estado = self._make_estado(
            {"cedula": "123", "nombre": "Juan", "problema": "falla"},
            config,
        )
        assert strategy.validate_requirements(estado) is True

    def test_validate_requirements_missing_field(self):
        """validate_requirements retorna False cuando falta un campo."""
        strategy = DefaultStrategy()
        config = {"campos_obligatorios": ["cedula", "nombre", "problema"]}
        estado = self._make_estado(
            {"cedula": "123", "nombre": "Juan", "problema": None},
            config,
        )
        assert strategy.validate_requirements(estado) is False

    def test_validate_requirements_empty_config(self):
        """validate_requirements retorna True si no hay campos obligatorios."""
        strategy = DefaultStrategy()
        config = {"campos_obligatorios": []}
        estado = self._make_estado({}, config)
        assert strategy.validate_requirements(estado) is True

    @pytest.mark.asyncio
    async def test_get_priority_calls_llm(self):
        """get_priority debe llamar al llm_provider.prioritize."""
        strategy = DefaultStrategy()
        mock_llm = AsyncMock(spec=ILLMProvider)
        mock_llm.prioritize.return_value = "Alta"

        estado = self._make_estado({}, {})
        estado.categoria = "Incidente técnico"

        result = await strategy.get_priority(estado, mock_llm)

        assert result == "Alta"
        mock_llm.prioritize.assert_awaited_once()

    def test_get_routing_valid_combination(self):
        """get_routing retorna el valor correcto del YAML."""
        strategy = DefaultStrategy()
        config = {
            "reglas_enrutamiento": {
                "Incidente técnico": {
                    "Alta": "GESTIÓN EXTERNA",
                    "Baja": "RESPUESTA DIRECTA",
                }
            }
        }
        estado = self._make_estado({}, config)
        estado.categoria = "Incidente técnico"
        estado.prioridad = "Alta"

        assert strategy.get_routing(estado) == "GESTIÓN EXTERNA"

    def test_get_routing_invalid_combination_defaults_to_external(self):
        """get_routing retorna GESTIÓN EXTERNA si la combinación no existe."""
        strategy = DefaultStrategy()
        config = {"reglas_enrutamiento": {}}
        estado = self._make_estado({}, config)
        estado.categoria = "Categoría Inventada"
        estado.prioridad = "Urgentísima"

        # Debe hacer fallback sin lanzar excepción
        assert strategy.get_routing(estado) == "GESTIÓN EXTERNA"


# ── Tests de MensajeriaValleStrategy ──


class TestMensajeriaValleStrategy:
    """Tests para la estrategia de Mensajería del Valle."""

    @pytest.mark.asyncio
    async def test_get_priority_uses_external_adapter(self):
        """get_priority debe usar el adaptador externo, NO el LLM."""
        mock_adapter = AsyncMock()
        mock_adapter.get_priority_from_client.return_value = "Alta"
        mock_llm = AsyncMock(spec=ILLMProvider)

        strategy = MensajeriaValleStrategy(adaptador_mensajeria=mock_adapter)

        estado = ProcesamientoEstado(
            request_original=SolicitudInput(
                compania="MENSAJERIA DEL VALLE",
                solicitud_id="REQ-MV-001",
                solicitud_descripcion="Retraso de paquete",
            ),
            tenant_config={
                "campos_obligatorios": ["tipo_documento", "numero_documento", "tipo_solicitud"],
            },
            datos_extraidos={
                "tipo_documento": "CC",
                "numero_documento": "987654321",
            },
            categoria="Retraso de envío",
        )

        result = await strategy.get_priority(estado, mock_llm)

        assert result == "Alta"
        mock_adapter.get_priority_from_client.assert_awaited_once()
        # Verificar que el LLM NUNCA fue llamado
        mock_llm.prioritize.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_priority_sends_categoria_as_tipo_solicitud(self):
        """El campo tipo_solicitud debe ser estado.categoria, NO datos extraídos."""
        mock_adapter = AsyncMock()
        mock_adapter.get_priority_from_client.return_value = "Media"
        mock_llm = AsyncMock(spec=ILLMProvider)

        strategy = MensajeriaValleStrategy(adaptador_mensajeria=mock_adapter)

        estado = ProcesamientoEstado(
            request_original=SolicitudInput(
                compania="MENSAJERIA DEL VALLE",
                solicitud_id="REQ-MV-002",
                solicitud_descripcion="Paquete dañado",
            ),
            tenant_config={},
            datos_extraidos={
                "tipo_documento": "CC",
                "numero_documento": "111111",
                "tipo_solicitud": "ESTE NO DEBE USARSE",
            },
            categoria="Dañado en tránsito",  # Este sí debe usarse
        )

        await strategy.get_priority(estado, mock_llm)

        # Verificar que envió la categoría, no el dato extraído
        call_kwargs = mock_adapter.get_priority_from_client.call_args
        assert call_kwargs.kwargs.get("tipo_solicitud") == "Dañado en tránsito"
