"""
Plantillas de prompts para las llamadas al LLM.

Cada función genera el system prompt para un paso específico del
pipeline. El texto original de la solicitud se envía siempre como
user_message en la llamada a la API del LLM.
"""


def prompt_extraccion(campos_obligatorios: list[str]) -> str:
    """System prompt para el Paso 1: Extracción de entidades."""
    campos_str = ", ".join(campos_obligatorios)
    return (
        "Eres un analista BPO experto en extracción de datos. "
        "Tu tarea es analizar la solicitud del cliente y extraer "
        f"EXACTAMENTE los siguientes campos: {campos_str}. "
        "Devuelve un JSON donde las llaves sean los nombres de los campos. "
        "Si un campo no se menciona explícitamente en el texto, su valor DEBE ser null."
    )


def prompt_clasificacion(categorias: list[str]) -> str:
    """System prompt para el Paso 2: Clasificación."""
    categorias_str = ", ".join(f'"{c}"' for c in categorias)
    return (
        "Eres un clasificador de texto estricto. "
        "Lee la solicitud y clasifícala en EXACTAMENTE UNA de las "
        f"siguientes categorías permitidas: {categorias_str}. "
        "NO inventes categorías nuevas. "
        "Responde únicamente con un JSON con la llave 'categoria'."
    )


def prompt_priorizacion(categoria: str) -> str:
    """System prompt para el Paso 3: Priorización."""
    return (
        f"Evalúa la urgencia de la siguiente solicitud clasificada como '{categoria}'. "
        "Asigna un nivel de prioridad. "
        "Opciones permitidas: 'Alta', 'Media', 'Baja'. "
        "Responde únicamente con un JSON con la llave 'prioridad'."
    )


def prompt_justificacion(categoria: str, prioridad: str) -> str:
    """System prompt para el Paso 4: Justificación."""
    return (
        f"Redacta una breve justificación (máximo 2 líneas) explicando por qué "
        f"se le asignó la prioridad '{prioridad}' a esta solicitud de categoría "
        f"'{categoria}'. Debes incorporar información específica extraída del "
        "texto original de la solicitud. "
        "PROHIBIDO inventar datos, nombres o fechas que no estén en el texto original. "
        "Responde únicamente con un JSON con la llave 'justificacion'."
    )
