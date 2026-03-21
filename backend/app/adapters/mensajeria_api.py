"""
Adaptador simulado del servicio externo de Mensajería del Valle (Bono +6%).

Este adaptador NO implementa IExternalPlatform ni ILLMProvider.
Es un HTTP Client aislado ad-hoc que será inyectado EXCLUSIVAMENTE
en la MensajeriaValleStrategy para obtener la prioridad del caso.

En producción, este adaptador haría una llamada HTTP real al
microservicio proporcionado por el cliente.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class MensajeriaValleAdapter:
    """Simulación del microservicio de priorización de Mensajería del Valle."""

    async def get_priority_from_client(
        self,
        tipo_documento: str,
        numero_documento: str,
        tipo_solicitud: str,
    ) -> str:
        """Consulta la prioridad al servicio externo del cliente.

        Lógica simulada: retorna 'Alta' si el tipo_solicitud contiene
        'Retraso', de lo contrario 'Media'.

        En producción, esta función haría una petición HTTP real al
        microservicio del cliente, enviando tipo_documento,
        numero_documento y tipo_solicitud como parámetros.

        Args:
            tipo_documento: Tipo de documento (ej. 'CC', 'NIT').
            numero_documento: Número del documento.
            tipo_solicitud: Categoría de la solicitud (viene del Paso 2).

        Returns:
            Prioridad asignada: 'Alta', 'Media' o 'Baja'.
        """
        # Simular latencia de red
        await asyncio.sleep(0.5)

        # Lógica simulada de priorización
        if tipo_solicitud and "Retraso" in tipo_solicitud:
            prioridad = "Alta"
        else:
            prioridad = "Media"

        logger.info(
            f"[MensajeríaValle] Servicio externo respondió: "
            f"tipo_doc={tipo_documento}, num_doc={numero_documento}, "
            f"tipo_solicitud={tipo_solicitud} → prioridad={prioridad}"
        )

        return prioridad
