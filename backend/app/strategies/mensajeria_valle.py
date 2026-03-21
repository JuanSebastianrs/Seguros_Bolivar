"""
Estrategia personalizada para Mensajería del Valle (Bono +6%).

Mensajería del Valle utiliza un servicio externo (proporcionado por
el propio cliente) para determinar la prioridad, en vez del LLM.
Esta subclase sobreescribe exclusivamente get_priority().

Cualquier cliente futuro que proporcione servicios ad-hoc puede
seguir este mismo patrón: heredar de DefaultStrategy y sobrescribir
solo el método diferenciador.
"""

import logging

from app.domain.interfaces import ILLMProvider
from app.domain.models import ProcesamientoEstado
from app.strategies.base import DefaultStrategy

logger = logging.getLogger(__name__)


class MensajeriaValleStrategy(DefaultStrategy):
    """Estrategia para 'MENSAJERIA DEL VALLE'.

    Usa adaptador externo inyectado para prioridad en vez del LLM.
    Los métodos validate_requirements y get_routing se heredan intactos.
    """

    def __init__(self, adaptador_mensajeria) -> None:
        """Inyección de dependencia estricta.

        PROHIBIDO instanciar el adaptador aquí. Debe ser inyectado
        por la capa superior (StrategyFactory).

        Args:
            adaptador_mensajeria: Instancia de MensajeriaValleAdapter.
        """
        self._adaptador = adaptador_mensajeria

    async def get_priority(
        self, estado: ProcesamientoEstado, llm_provider: ILLMProvider
    ) -> str:
        """Obtiene la prioridad del servicio externo del cliente.

        IGNORA el llm_provider. Usa el adaptador externo inyectado.

        CRÍTICO: tipo_solicitud debe ser estado.categoria (generado
        en el Paso 2), NO un dato extraído.
        """
        datos = estado.datos_extraidos

        tipo_documento = datos.get("tipo_documento", "")
        numero_documento = datos.get("numero_documento", "")
        tipo_solicitud = estado.categoria  # Paso 2, NO datos extraídos

        logger.info(
            f"[{estado.request_original.solicitud_id}] "
            f"Consultando servicio externo de Mensajería del Valle "
            f"para prioridad. tipo_solicitud='{tipo_solicitud}'"
        )

        prioridad = await self._adaptador.get_priority_from_client(
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            tipo_solicitud=tipo_solicitud,
        )

        return prioridad
