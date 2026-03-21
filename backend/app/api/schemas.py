"""
Contratos Pydantic V2 de la API.

Define los modelos de entrada (SolicitudInput) y salida (SolicitudOutput)
que garantizan la validación y serialización estricta de datos en el
endpoint REST.
"""

from pydantic import BaseModel, Field


class SolicitudInput(BaseModel):
    """Payload de entrada para procesar una solicitud del BPO."""

    compania: str = Field(
        ...,
        description="Nombre de la compañía cliente (ej. 'GASES DEL ORINOCO')",
        examples=["GASES DEL ORINOCO"],
    )
    solicitud_id: str = Field(
        ...,
        description="Identificador único de la solicitud",
        examples=["REQ-001"],
    )
    solicitud_descripcion: str = Field(
        ...,
        description="Texto libre de la solicitud del usuario",
        examples=[
            "Mi nombre es Juana y mi numero de cédula es 102045678. "
            "Solicito una revision urgente porque la estufa que compre "
            "hace 2 semanas presenta fallas."
        ],
    )


class SolicitudOutput(BaseModel):
    """Respuesta del microservicio con el resultado del procesamiento."""

    compania: str
    solicitud_id: str
    solicitud_fecha: str = Field(
        ...,
        serialization_alias="Solicitud_fecha",
        description="Fecha de procesamiento (YYYY-MM-DD). Nota: S mayúscula en output.",
    )
    solicitud_tipo: str = Field(
        ...,
        description="Categoría asignada a la solicitud",
    )
    solicitud_prioridad: str = Field(
        ...,
        description="Nivel de prioridad: Alta, Media o Baja",
    )
    solicitud_id_cliente: str = Field(
        ...,
        description="Número de documento del cliente",
    )
    solicitud_tipo_id_cliente: str = Field(
        ...,
        description="Tipo de documento del cliente (ej. 'CC', 'NIT')",
    )
    solicitud_id_plataforma_externa: str | None = Field(
        default=None,
        description="ID del caso en plataforma externa (solo en GESTIÓN EXTERNA)",
    )
    proximo_paso: str = Field(
        ...,
        description="Siguiente paso: GESTIÓN EXTERNA, RESPUESTA DIRECTA o CIERRE_POR_INFORMACION_INSUFICIENTE",
    )
    justificacion: str = Field(
        ...,
        description="Justificación de la prioridad asignada",
    )
    estado: str = Field(
        ...,
        description="Estado final: 'pendiente' o 'cerrado'",
    )

    model_config = {
        "populate_by_name": True,
    }
