"""
API Routers — Adaptador primario (Driving Adapter).

Define los endpoints REST y actúa como puente entre HTTP y el dominio.
Maneja la inyección de dependencias y la conversión de excepciones
de negocio a respuestas HTTP apropiadas.
"""

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException

from app.adapters.bpo_externo_api import BPOExternalAdapter
from app.adapters.llm_gemini import GeminiAdapter
from app.adapters.llm_groq import GroqAdapter
from app.adapters.llm_manager import LLMManager
from app.adapters.mensajeria_api import MensajeriaValleAdapter
from app.api.schemas import SolicitudInput, SolicitudOutput
from app.core.exceptions import CompanyNotFoundError, DuplicateRequestError
from app.core.state import InMemoryCache
from app.pipeline.orchestrator import PipelineOrchestrator
from app.strategies.factory import StrategyFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Solicitudes BPO"])

# ── Singletons de Infraestructura ──
# Se crean una sola vez y se reutilizan en cada request.
_cache = InMemoryCache()
_mensajeria_adapter = MensajeriaValleAdapter()
_external_platform = BPOExternalAdapter()

# Cargar configuración YAML una sola vez
_yaml_path = Path(__file__).resolve().parent.parent.parent / "data" / "tenants_config.yaml"
with open(_yaml_path, "r", encoding="utf-8") as f:
    _yaml_config = yaml.safe_load(f)


# Proveedores LLM — se crean una sola vez y se reutilizan en cada request.
_groq_adapter = GroqAdapter()
_gemini_adapter = GeminiAdapter()


def _get_llm_provider() -> LLMManager:
    """Crea el LLMManager con fallback Groq → Gemini."""
    return LLMManager(primary=_groq_adapter, secondary=_gemini_adapter)


def _get_orchestrator(
    llm_provider: LLMManager = Depends(_get_llm_provider),
) -> PipelineOrchestrator:
    """Crea el Orquestador con todas las dependencias inyectadas."""
    strategy_factory = StrategyFactory(
        adaptador_mensajeria=_mensajeria_adapter,
    )
    return PipelineOrchestrator(
        cache_provider=_cache,
        strategy_factory=strategy_factory,
        llm_provider=llm_provider,
        external_platform=_external_platform,
        yaml_config=_yaml_config,
    )


# ── Endpoints ──


@router.post(
    "/solicitudes",
    response_model=SolicitudOutput,
    summary="Procesar solicitud BPO",
    description=(
        "Recibe una solicitud de texto libre y ejecuta el pipeline completo: "
        "validación, clasificación, priorización, justificación, enrutamiento "
        "y gestión externa si aplica."
    ),
    responses={
        400: {"description": "Compañía no encontrada en el sistema"},
        409: {"description": "Solicitud duplicada"},
    },
)
async def procesar_solicitud(
    request: SolicitudInput,
    simular_fallos_bpo: bool = False,
    simular_duplicado: bool = False,
    orchestrator: PipelineOrchestrator = Depends(_get_orchestrator),
) -> SolicitudOutput:
    """Endpoint principal para procesar solicitudes del BPO."""
    logger.info(
        f"Solicitud recibida: compania='{request.compania}', "
        f"solicitud_id='{request.solicitud_id}'"
    )

    # Feature Flag dinámico: override del setting por query param
    if simular_fallos_bpo:
        from app.core.config import get_settings
        get_settings().SIMULAR_FALLOS_BPO = True
    else:
        from app.core.config import get_settings
        get_settings().SIMULAR_FALLOS_BPO = False

    try:
        result = await orchestrator.run(request)

        # Bono Duplicados: si el toggle está activo, re-enviar para provocar 409
        if simular_duplicado:
            try:
                await orchestrator.run(request)
            except DuplicateRequestError as e:
                logger.info(f"Simulación de duplicado exitosa: {e}")
                raise HTTPException(status_code=409, detail=str(e))

        return result
    except CompanyNotFoundError as e:
        logger.warning(f"Compañía no encontrada: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateRequestError as e:
        logger.warning(f"Solicitud duplicada: {e}")
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/health",
    summary="Health Check",
    description="Verifica que el servicio está operativo.",
)
async def health_check():
    """Health check del microservicio."""
    return {"status": "ok", "service": "BPO IA Microservice"}
