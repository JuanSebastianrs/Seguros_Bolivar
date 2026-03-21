"""
Esquemas internos de validación para respuestas de LLMs.

Estos modelos Pydantic V2 garantizan que la salida del LLM
sea determinista y estructurada antes de llegar al Orquestador.
"""

from typing import Literal

from pydantic import BaseModel


class ExtraccionResponse(BaseModel):
    """Respuesta de extracción de entidades (Paso 1).

    Los campos pueden ser dinámicos dependiendo de la empresa,
    por lo que usamos un dict en el adaptador y validamos
    la presencia de campos en la estrategia.
    """

    # Se valida como dict libre en el adaptador


class ClasificacionResponse(BaseModel):
    """Respuesta de clasificación (Paso 2)."""

    categoria: str


class PrioridadResponse(BaseModel):
    """Respuesta de priorización (Paso 3)."""

    prioridad: Literal["Alta", "Media", "Baja"]


class JustificacionResponse(BaseModel):
    """Respuesta de justificación (Paso 4)."""

    justificacion: str
