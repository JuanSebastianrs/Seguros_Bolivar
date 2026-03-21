"""
Estrategia base (DefaultStrategy) basada en datos YAML.

Implementa ICompanyStrategy usando exclusivamente la configuración
del tenant cargada del YAML. Cumple con el principio Open/Closed:
nuevas empresas se agregan modificando solo el YAML sin tocar código.

Decisión Arquitectónica:
En lugar de crear una subclase Strategy por cada empresa (lo cual
violaría Open/Closed al requerir código nuevo para cada cliente),
se usa una única DefaultStrategy alimentada por datos del YAML.
Solo se crean subclases para integraciones ad-hoc (ej. Mensajería
del Valle con su servicio externo de priorización).
"""

import logging

from app.domain.interfaces import ICompanyStrategy, ILLMProvider
from app.domain.models import ProcesamientoEstado

logger = logging.getLogger(__name__)


class DefaultStrategy(ICompanyStrategy):
    """Estrategia genérica basada en configuración YAML.

    Funciona para cualquier empresa cuyo comportamiento se defina
    enteramente en el archivo tenants_config.yaml.
    """

    def validate_requirements(self, estado: ProcesamientoEstado) -> bool:
        """Verifica que todos los campos obligatorios tengan valor no nulo."""
        campos_requeridos = estado.tenant_config.get("campos_obligatorios", [])
        datos = estado.datos_extraidos

        for campo in campos_requeridos:
            valor = datos.get(campo)
            if valor is None:
                logger.info(
                    f"[{estado.request_original.solicitud_id}] "
                    f"Campo obligatorio faltante: '{campo}'"
                )
                return False

        return True

    async def get_priority(
        self, estado: ProcesamientoEstado, llm_provider: ILLMProvider
    ) -> str:
        """Obtiene la prioridad usando el proveedor de IA."""
        prioridad = await llm_provider.prioritize(
            text=estado.request_original.solicitud_descripcion,
            category=estado.categoria,  # type: ignore[arg-type]
        )
        return prioridad

    def get_routing(self, estado: ProcesamientoEstado) -> str:
        """Determina el siguiente paso según las reglas del YAML.

        Defensa contra KeyErrors: si la combinación de categoría y
        prioridad no existe en el YAML (posible alucinación del LLM),
        retorna GESTIÓN EXTERNA por defecto para asegurar atención humana.
        """
        reglas = estado.tenant_config.get("reglas_enrutamiento", {})

        try:
            return reglas[estado.categoria][estado.prioridad]
        except KeyError:
            logger.error(
                f"[{estado.request_original.solicitud_id}] "
                f"Combinación no encontrada en YAML: "
                f"categoría='{estado.categoria}', prioridad='{estado.prioridad}'. "
                f"Retornando GESTIÓN EXTERNA por defecto."
            )
            return "GESTIÓN EXTERNA"
