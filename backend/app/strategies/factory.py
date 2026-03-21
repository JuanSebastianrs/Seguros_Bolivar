"""
Factory para resolver la estrategia de negocio por compañía.

Encapsula la lógica de decisión sobre cuál ICompanyStrategy instanciar,
manteniendo las dependencias inyectadas de manera limpia.
"""

import logging

from app.core.exceptions import CompanyNotFoundError
from app.domain.interfaces import ICompanyStrategy
from app.strategies.base import DefaultStrategy
from app.strategies.mensajeria_valle import MensajeriaValleStrategy

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Fábrica de estrategias de negocio por compañía."""

    def __init__(self, adaptador_mensajeria=None) -> None:
        """Recibe las dependencias necesarias para las estrategias.

        Args:
            adaptador_mensajeria: Instancia de MensajeriaValleAdapter.
                Solo necesaria si se opera con Mensajería del Valle.
        """
        self._adaptador_mensajeria = adaptador_mensajeria

    def get_strategy(
        self, compania: str, tenant_config: dict
    ) -> ICompanyStrategy:
        """Resuelve la estrategia correcta para la compañía.

        Args:
            compania: Nombre de la compañía (ej. "GASES DEL ORINOCO").
            tenant_config: Configuración del tenant extraída del YAML.

        Returns:
            ICompanyStrategy: Estrategia apropiada para la compañía.

        Raises:
            CompanyNotFoundError: Si la compañía no existe en el YAML.
        """
        if not tenant_config:
            raise CompanyNotFoundError(compania)

        if compania == "MENSAJERIA DEL VALLE":
            logger.info(
                f"Estrategia resuelta: MensajeriaValleStrategy para '{compania}'"
            )
            return MensajeriaValleStrategy(
                adaptador_mensajeria=self._adaptador_mensajeria
            )

        logger.info(f"Estrategia resuelta: DefaultStrategy para '{compania}'")
        return DefaultStrategy()
