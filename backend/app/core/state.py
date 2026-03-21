"""
Adaptador de caché en memoria para control de duplicados.

Implementa ICacheProvider usando un set() en memoria. Para un entorno
de producción, se reemplazaría por Redis u otro almacén persistente
sin modificar la lógica del dominio (Arquitectura Hexagonal).
"""

from app.domain.interfaces import ICacheProvider


class InMemoryCache(ICacheProvider):
    """Caché en memoria para detectar solicitudes duplicadas."""

    def __init__(self) -> None:
        self._processed: set[str] = set()

    async def is_duplicate(self, solicitud_id: str) -> bool:
        """Verifica si la solicitud ya fue procesada."""
        return solicitud_id in self._processed

    async def register(self, solicitud_id: str) -> None:
        """Registra la solicitud como procesada."""
        self._processed.add(solicitud_id)

    def clear(self) -> None:
        """Limpia el caché. Útil para tests."""
        self._processed.clear()
