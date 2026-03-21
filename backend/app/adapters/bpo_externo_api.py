"""
Adaptador simulado de plataforma BPO externa.

Implementa IExternalPlatform. Simula la creación de un caso
en la plataforma de atención al cliente de la empresa.

Feature Flag (Bono +4%): SIMULAR_FALLOS_BPO controla si el
adaptador lanza ExternalPlatformError para probar resiliencia.
"""

import asyncio
import logging
import uuid

from app.core.config import get_settings
from app.core.exceptions import ExternalPlatformError
from app.domain.interfaces import IExternalPlatform

logger = logging.getLogger(__name__)


class BPOExternalAdapter(IExternalPlatform):
    """Simulación de la plataforma de ticketing del cliente."""

    async def create_case(self, data: dict) -> str:
        """Crea un caso ficticio en la plataforma externa.

        Args:
            data: Diccionario con los datos del caso.

        Returns:
            ID ficticio del caso creado.

        Raises:
            ExternalPlatformError: Si SIMULAR_FALLOS_BPO está activado.
        """
        settings = get_settings()
        solicitud_id = data.get("solicitud_id", "desconocido")

        # Simular latencia de red
        await asyncio.sleep(1)

        # Feature Flag: simular fallo
        if settings.SIMULAR_FALLOS_BPO:
            logger.error(
                f"Falla simulada en plataforma externa para "
                f"solicitud_id={solicitud_id}. "
                f"Feature flag SIMULAR_FALLOS_BPO=True."
            )
            raise ExternalPlatformError(
                f"Fallo de conexión simulado para solicitud {solicitud_id}"
            )

        # Generar ID ficticio
        case_id = "ID" + str(uuid.uuid4())[:8]
        logger.info(
            f"Caso creado exitosamente en plataforma externa: "
            f"solicitud_id={solicitud_id}, case_id={case_id}"
        )
        return case_id
