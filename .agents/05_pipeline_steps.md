# 🧠 PROMPTS Y LÓGICA DE IA (05_pipeline_steps)

## 🎯 Objetivo
Definir los *System Prompts* exactos, los parámetros de inferencia y los esquemas de validación interna para las llamadas al LLM. [cite_start]Esto garantiza que el Paso 1 (Extracción) [cite: 25-26][cite_start], Paso 2 (Clasificación) [cite: 27][cite_start], Paso 3 (Priorización) [cite: 28] [cite_start]y Paso 4 (Justificación) [cite: 29] sean deterministas y predecibles.

## 1. Reglas Maestras de Inferencia (Para `GroqAdapter` y `GeminiAdapter`)
* **Temperatura:** Todas las llamadas al LLM DEBEN tener `temperature=0.0`. No queremos creatividad, queremos precisión analítica.
* **Formato de Salida:** Todas las llamadas deben forzar JSON (ej. `response_format={"type": "json_object"}` si la API lo soporta).
* **Estructura del Payload (CRÍTICO):** Todos los prompts definidos abajo actúan como el `system_message`. DEBES enviar el texto original de la solicitud (`estado.request_original.solicitud_descripcion`) como el `user_message` en la llamada a la API.

## 2. Esquemas Internos de Validación (`app/domain/schemas_llm.py`)
El `ILLMProvider` debe validar el JSON del LLM usando estos modelos Pydantic V2 antes de retornarlo al Orquestador:

* `class ClasificacionResponse(BaseModel): categoria: str`
* `class PrioridadResponse(BaseModel): prioridad: Literal["Alta", "Media", "Baja"]`
* `class JustificacionResponse(BaseModel): justificacion: str`

## 3. Los Prompts Maestros (`app/domain/prompts.py`)

Crea un archivo con estas plantillas (*f-strings*).

### A. Prompt para el Paso 1 (Extracción)
* **Prompt de Sistema:** `"Eres un analista BPO experto en extracción de datos. Tu tarea es analizar la solicitud del cliente y extraer EXACTAMENTE los siguientes campos: {lista_campos_obligatorios}. Devuelve un JSON donde las llaves sean los nombres de los campos. Si un campo no se menciona explícitamente en el texto, su valor DEBE ser null."`

### B. Prompt para el Paso 2 (Clasificación)
* **Prompt de Sistema:** `"Eres un clasificador de texto estricto. Lee la solicitud y clasifícala en EXACTAMENTE UNA de las siguientes categorías permitidas: {lista_categorias_yaml}. NO inventes categorías nuevas. Responde únicamente con un JSON con la llave 'categoria'."`

### C. Prompt para el Paso 3 (Priorización)
* **Prompt de Sistema:** `"Evalúa la urgencia de la siguiente solicitud clasificada como '{categoria}'. Asigna un nivel de prioridad. Opciones permitidas: 'Alta', 'Media', 'Baja'. Responde únicamente con un JSON con la llave 'prioridad'."`

### D. Prompt para el Paso 4 (Justificación)
* **Prompt de Sistema:** `"Redacta una breve justificación (máximo 2 líneas) explicando por qué se le asignó la prioridad '{prioridad}' a esta solicitud de categoría '{categoria}'. Debes incorporar información específica extraída del texto original de la solicitud. PROHIBIDO inventar datos, nombres o fechas que no estén en el texto original. Responde únicamente con un JSON con la llave 'justificacion'."`

## 📝 Instrucciones de Calidad para Antigravity

1. **Limpieza del Output:** Implementa una función para limpiar los bloques de Markdown (` ```json ` y ` ``` `) de la respuesta del LLM antes de parsearlo.
2. **Resiliencia en la Validación (Auto-reparación):** Cuando apliques `Model.model_validate_json()`, envuélvelo en un `try/except ValidationError`. Si la IA alucina un formato inválido (ej. una prioridad "Urgente" que rompe el `Literal`), atrapa el error, registra un `logging.error` detallado y LANZA una excepción personalizada `LLMOutputError`. 
3. **El Rol del Manager:** Al lanzar `LLMOutputError`, el `LLMManager` (tu Fallback) atrapará este error emitido por Groq y automáticamente intentará la misma petición con Gemini.