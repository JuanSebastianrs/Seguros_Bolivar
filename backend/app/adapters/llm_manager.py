"""
LLM Manager — Patrón Fallback (Groq → Gemini).

Implementa ILLMProvider actuando como Proxy/Decorator.
Intenta ejecutar con el adaptador primario (Groq); si falla,
redirige silenciosamente al secundario (Gemini).

Esto proporciona resiliencia ante:
- Rate limits de APIs gratuitas
- Caídas temporales de proveedores
- Outputs inválidos que no pasan validación
"""

import logging

from app.core.exceptions import LLMOutputError
from app.domain.interfaces import ILLMProvider

logger = logging.getLogger(__name__)


class LLMManager(ILLMProvider):
    """Gestor de LLMs con fallback automático.

    Implementa la misma interfaz ILLMProvider para que el Orquestador
    no sepa (ni necesite saber) que hay un fallback detrás.
    """

    def __init__(
        self, primary: ILLMProvider, secondary: ILLMProvider
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    async def _with_fallback(self, method_name: str, *args, **kwargs):
        """Ejecuta un método con fallback automático."""
        try:
            method = getattr(self._primary, method_name)
            return await method(*args, **kwargs)
        except (LLMOutputError, Exception) as e:
            logger.warning(
                f"[LLMManager] Fallo en proveedor primario para '{method_name}': "
                f"{type(e).__name__}: {e}. Intentando con proveedor secundario..."
            )
            try:
                method = getattr(self._secondary, method_name)
                return await method(*args, **kwargs)
            except Exception as e2:
                logger.error(
                    f"[LLMManager] Fallo en AMBOS proveedores para '{method_name}': "
                    f"Primario: {e} | Secundario: {e2}"
                )
                raise

    async def extract_entities(self, text: str, required_fields: list[str]) -> dict:
        """Paso 1 con fallback."""
        return await self._with_fallback("extract_entities", text, required_fields)

    async def classify(self, text: str, categories: list[str]) -> str:
        """Paso 2 con fallback."""
        return await self._with_fallback("classify", text, categories)

    async def prioritize(self, text: str, category: str) -> str:
        """Paso 3 con fallback."""
        return await self._with_fallback("prioritize", text, category)

    async def justify(self, text: str, category: str, priority: str) -> str:
        """Paso 4 con fallback."""
        return await self._with_fallback("justify", text, category, priority)
