"""
Utilidades compartidas para los adaptadores de LLM.

Funciones de limpieza y procesamiento de respuestas que son
comunes a todos los proveedores de IA.
"""

import re


def clean_json_response(text: str) -> str:
    """Limpia bloques de Markdown del output del LLM.

    Los LLMs suelen envolver JSON en ```json ... ```.
    Esta función los elimina para poder parsear correctamente.
    """
    text = text.strip()
    # Eliminar bloques de Markdown
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()
