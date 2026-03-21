"""
Interfaces (Puertos de Salida) del dominio.

Definen los contratos ABC que desacoplan la lógica de negocio
de las implementaciones concretas (LLMs, plataformas externas, caché).
Ninguna implementación tecnológica vive aquí.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.api.schemas import SolicitudInput, SolicitudOutput
from app.domain.models import ProcesamientoEstado


# ---------- Puerto IA ----------
class ILLMProvider(ABC):
    """Puerto para interactuar con proveedores de modelos de lenguaje."""

    @abstractmethod
    async def extract_entities(self, text: str, required_fields: list[str]) -> dict:
        """Extrae entidades del texto según los campos requeridos."""
        ...

    @abstractmethod
    async def classify(self, text: str, categories: list[str]) -> str:
        """Clasifica el texto en una de las categorías permitidas."""
        ...

    @abstractmethod
    async def prioritize(self, text: str, category: str) -> str:
        """Determina la prioridad (Alta / Media / Baja)."""
        ...

    @abstractmethod
    async def justify(self, text: str, category: str, priority: str) -> str:
        """Genera una justificación breve para la prioridad asignada."""
        ...


# ---------- Puerto Plataforma Externa ----------
class IExternalPlatform(ABC):
    """Puerto para crear casos en plataformas externas de clientes."""

    @abstractmethod
    async def create_case(self, data: dict) -> str:
        """Crea un caso en la plataforma externa.

        Returns:
            ID ficticio del caso creado.

        Raises:
            ExternalPlatformError: si falla la comunicación.
        """
        ...


# ---------- Puerto Estrategia de Negocio ----------
class ICompanyStrategy(ABC):
    """Puerto para la lógica de negocio variable por compañía cliente."""

    @abstractmethod
    def validate_requirements(self, estado: ProcesamientoEstado) -> bool:
        """Valida que la solicitud tenga la información mínima requerida."""
        ...

    @abstractmethod
    async def get_priority(
        self, estado: ProcesamientoEstado, llm_provider: ILLMProvider
    ) -> str:
        """Determina la prioridad del caso.

        La implementación default usa el LLM; estrategias personalizadas
        pueden ignorar el LLM y usar un servicio externo.
        """
        ...

    @abstractmethod
    def get_routing(self, estado: ProcesamientoEstado) -> str:
        """Determina el siguiente paso (GESTIÓN EXTERNA / RESPUESTA DIRECTA)."""
        ...


# ---------- Puerto Caché ----------
class ICacheProvider(ABC):
    """Puerto para control de solicitudes duplicadas."""

    @abstractmethod
    async def is_duplicate(self, solicitud_id: str) -> bool:
        """Verifica si la solicitud ya fue procesada."""
        ...

    @abstractmethod
    async def register(self, solicitud_id: str) -> None:
        """Registra una solicitud como procesada."""
        ...


# ---------- Puerto de Entrada (Pipeline) ----------
class IPipelineOrchestrator(ABC):
    """Puerto de entrada principal expuesto a la capa de API."""

    @abstractmethod
    async def run(self, request: SolicitudInput) -> SolicitudOutput:
        """Ejecuta el pipeline completo de procesamiento."""
        ...
