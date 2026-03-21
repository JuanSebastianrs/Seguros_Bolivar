"""
Orquestador del Pipeline de procesamiento (Chain of Responsibility).

Coordina la ejecución secuencial de los 6 pasos del BPO,
moviendo el ProcesamientoEstado a través de la cadena.
Implementa control de duplicados, early exit, y manejo de errores.
"""

import logging
from datetime import datetime

from app.api.schemas import SolicitudInput, SolicitudOutput
from app.core.exceptions import (
    CompanyNotFoundError,
    DuplicateRequestError,
    ExternalPlatformError,
)
from app.domain.interfaces import (
    ICacheProvider,
    IExternalPlatform,
    ILLMProvider,
    IPipelineOrchestrator,
)
from app.domain.models import ProcesamientoEstado
from app.strategies.factory import StrategyFactory

logger = logging.getLogger(__name__)


class PipelineOrchestrator(IPipelineOrchestrator):
    """Orquestador principal del pipeline de procesamiento BPO.

    Recibe todas sus dependencias vía constructor (IoC) y coordina
    la ejecución de los 6 pasos sin conocer implementaciones concretas.
    """

    def __init__(
        self,
        cache_provider: ICacheProvider,
        strategy_factory: StrategyFactory,
        llm_provider: ILLMProvider,
        external_platform: IExternalPlatform,
        yaml_config: dict,
    ) -> None:
        self._cache = cache_provider
        self._strategy_factory = strategy_factory
        self._llm = llm_provider
        self._external = external_platform
        self._config = yaml_config

    async def run(self, request: SolicitudInput) -> SolicitudOutput:
        """Ejecuta el pipeline completo de procesamiento.

        Secuencia:
        1. Control de duplicados (Bono +4%)
        2. Resolución de contexto y estrategia
        3. Paso 1: Validar información (con Early Exit)
        4. Paso 2: Clasificar
        5. Paso 3: Priorizar
        6. Paso 4: Justificar
        7. Paso 5: Enrutamiento
        8. Paso 6: Gestión externa
        9. Cierre y mapeo

        Raises:
            DuplicateRequestError: Si la solicitud ya fue procesada.
            CompanyNotFoundError: Si la compañía no existe en el YAML.
        """
        sid = request.solicitud_id

        # ─── 1. Control de Duplicados (Bono +4%) ───
        logger.debug(f"[{sid}] Iniciando control de duplicados...")
        if await self._cache.is_duplicate(sid):
            raise DuplicateRequestError(sid)
        await self._cache.register(sid)
        logger.debug(f"[{sid}] Solicitud registrada en caché.")

        # ─── 2. Resolución de Contexto y Estrategia ───
        empresas = self._config.get("empresas", {})
        tenant_config = empresas.get(request.compania)

        if tenant_config is None:
            raise CompanyNotFoundError(request.compania)

        strategy = self._strategy_factory.get_strategy(
            request.compania, tenant_config
        )

        estado = ProcesamientoEstado(
            request_original=request,
            tenant_config=tenant_config,
        )
        logger.debug(f"[{sid}] Contexto resuelto para '{request.compania}'.")

        # ─── 3. Paso 1: Validar Información ───
        logger.debug(f"[{sid}] Paso 1: Extrayendo entidades...")
        campos = tenant_config.get("campos_obligatorios", [])
        estado.datos_extraidos = await self._llm.extract_entities(
            text=request.solicitud_descripcion,
            required_fields=campos,
        )
        logger.debug(f"[{sid}] Datos extraídos: {estado.datos_extraidos}")

        requisitos_ok = strategy.validate_requirements(estado)

        if not requisitos_ok:
            # Early Exit — información insuficiente
            logger.info(f"[{sid}] Early Exit: información insuficiente.")
            estado.proximo_paso = "CIERRE_POR_INFORMACION_INSUFICIENTE"
            estado.justificacion = "Información incompleta o faltante"
            estado.categoria = "Sin clasificar"
            estado.prioridad = "N/A"
            return self._build_output(estado, status="cerrado")

        # ─── 4. Paso 2: Clasificar ───
        logger.debug(f"[{sid}] Paso 2: Clasificando solicitud...")
        categorias = tenant_config.get("categorias", [])
        estado.categoria = await self._llm.classify(
            text=request.solicitud_descripcion,
            categories=categorias,
        )
        logger.debug(f"[{sid}] Categoría asignada: '{estado.categoria}'")

        # ─── 5. Paso 3: Priorizar ───
        logger.debug(f"[{sid}] Paso 3: Priorizando...")
        estado.prioridad = await strategy.get_priority(estado, self._llm)
        logger.debug(f"[{sid}] Prioridad asignada: '{estado.prioridad}'")

        # ─── 6. Paso 4: Justificar ───
        logger.debug(f"[{sid}] Paso 4: Generando justificación...")
        estado.justificacion = await self._llm.justify(
            text=request.solicitud_descripcion,
            category=estado.categoria,
            priority=estado.prioridad,
        )
        logger.debug(f"[{sid}] Justificación generada.")

        # ─── 7. Paso 5: Enrutamiento ───
        logger.debug(f"[{sid}] Paso 5: Determinando enrutamiento...")
        estado.proximo_paso = strategy.get_routing(estado)
        logger.debug(f"[{sid}] Próximo paso: '{estado.proximo_paso}'")

        # ─── 8. Paso 6: Gestión Externa ───
        if estado.proximo_paso == "GESTIÓN EXTERNA":
            logger.debug(f"[{sid}] Paso 6: Creando caso en plataforma externa...")
            try:
                estado.id_plataforma_externa = await self._external.create_case(
                    {
                        "solicitud_id": sid,
                        "compania": request.compania,
                        "categoria": estado.categoria,
                        "prioridad": estado.prioridad,
                    }
                )
                logger.info(
                    f"[{sid}] Caso creado en plataforma externa: "
                    f"{estado.id_plataforma_externa}"
                )
            except ExternalPlatformError as e:
                logger.error(
                    f"Falla en plataforma externa para solicitud_id={sid}. "
                    f"Detalle: {e}"
                )
                estado.id_plataforma_externa = None
                estado.justificacion = (
                    f"{estado.justificacion} "
                    f"(Advertencia: Falla de red al crear caso)"
                )

        # ─── 9. Cierre y Mapeo ───
        if estado.proximo_paso == "GESTIÓN EXTERNA":
            final_status = "pendiente"
        else:
            final_status = "cerrado"

        logger.info(f"[{sid}] Pipeline completado. Estado final: '{final_status}'")
        return self._build_output(estado, status=final_status)

    def _build_output(
        self, estado: ProcesamientoEstado, status: str
    ) -> SolicitudOutput:
        """Mapea el ProcesamientoEstado al modelo de salida."""
        datos = estado.datos_extraidos

        # Extraer tipo y número de documento del cliente
        id_cliente = self._extract_doc_number(datos)
        tipo_id_cliente = self._extract_doc_type(datos)

        return SolicitudOutput(
            compania=estado.request_original.compania,
            solicitud_id=estado.request_original.solicitud_id,
            solicitud_fecha=datetime.now().strftime("%Y-%m-%d"),
            solicitud_tipo=estado.categoria or "Sin clasificar",
            solicitud_prioridad=estado.prioridad or "N/A",
            solicitud_id_cliente=id_cliente,
            solicitud_tipo_id_cliente=tipo_id_cliente,
            solicitud_id_plataforma_externa=estado.id_plataforma_externa,
            proximo_paso=estado.proximo_paso or "CIERRE_POR_INFORMACION_INSUFICIENTE",
            justificacion=estado.justificacion or "",
            estado=status,
        )

    @staticmethod
    def _extract_doc_type(datos: dict) -> str:
        """Extrae el tipo de documento del diccionario de datos.

        Busca campos comunes como 'solicitud_tipo_id_cliente', 'tipo_documento', etc.
        """
        for campo in ["solicitud_tipo_id_cliente", "tipo_documento"]:
            if datos.get(campo):
                return str(datos[campo])
        # Intentar inferir por presencia
        if datos.get("solicitud_id_cliente") or datos.get("cedula"): return "CC"
        if datos.get("nit_empresa"): return "NIT"
        return "N/A"

    @staticmethod
    def _extract_doc_number(datos: dict) -> str:
        """Extrae el número de documento del diccionario de datos."""
        for campo in ["solicitud_id_cliente", "cedula", "numero_documento", "nit_empresa", "email_usuario", "placa_vehiculo", "numero_guia"]:
            valor = datos.get(campo)
            if valor is not None:
                return str(valor)
        return "N/A"
