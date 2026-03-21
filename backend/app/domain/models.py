"""
Modelo de dominio del Pipeline de procesamiento.

ProcesamientoEstado es el objeto mutable que viaja a través de
los 6 pasos del pipeline, acumulando los resultados de cada paso.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.api.schemas import SolicitudInput


@dataclass
class ProcesamientoEstado:
    """Estado mutable que acarrea datos a través del pipeline.

    Cada paso del pipeline lee y/o modifica campos de este objeto.
    El tenant_config se carga una sola vez al inicio para evitar
    lecturas repetitivas del disco.
    """

    # Datos de entrada intactos
    request_original: SolicitudInput

    # Configuración específica del tenant extraída del YAML
    tenant_config: dict = field(default_factory=dict)

    # Paso 1: Datos extraídos por el LLM (ej. cédula, nombre)
    datos_extraidos: dict = field(default_factory=dict)

    # Paso 2: Categoría asignada
    categoria: str | None = None

    # Paso 3: Prioridad asignada
    prioridad: str | None = None

    # Paso 4: Justificación
    justificacion: str | None = None

    # Paso 5: Próximo paso (GESTIÓN EXTERNA / RESPUESTA DIRECTA / CIERRE_...)
    proximo_paso: str | None = None

    # Paso 6: ID de plataforma externa
    id_plataforma_externa: str | None = None
