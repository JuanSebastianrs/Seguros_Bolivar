# 🔌 IMPLEMENTACIÓN DE ADAPTADORES E INFRAESTRUCTURA (06_adapters_and_llms)

## 🎯 Objetivo
Implementar las clases concretas que conectan nuestra lógica de negocio con el mundo exterior (LLMs, APIs externas y memoria). 

## 1. Adaptadores de Inteligencia Artificial (`app/adapters/`)

Crea tres clases que implementen la interfaz `ILLMProvider`. 

**CRÍTICO PARA TODOS LOS LLMs (LA TRAMPA DEL JSON):**
Los LLMs suelen envolver sus respuestas en bloques de Markdown. Debes crear una función de utilidad (o lógica interna) que limpie el output antes de parsearlo. Ejemplo: quitar ` ```json ` y ` ``` ` del inicio y fin del string antes de ejecutar `json.loads()` o validarlo con Pydantic.

### A. `GroqAdapter` (`llm_groq.py`)
* Usa `AsyncGroq`. Configura el modelo a `llama3-70b-8192`.
* **Prompting:** Instruye al modelo para devolver SOLO un JSON válido.

### B. `GeminiAdapter` (`llm_gemini.py`)
* Usa el SDK de Google GenAI de manera asíncrona. Configura a `gemini-2.5-flash`.
* Usa la configuración de JSON estructurado nativa si está disponible, o prompt estricto.

### C. `LLMManager` (`llm_manager.py`) - EL FALLBACK
* **Constructor:** Recibe una instancia de `GroqAdapter` y `GeminiAdapter`.
* **Lógica:** Intenta ejecutar Groq. Si lanza una excepción (timeout, rate limit), captura el error, emite un *warning* estructurado (ver sección de Logs) y ejecuta el `GeminiAdapter`.

## 2. Adaptadores de Plataformas Externas (Mocks)

### A. `BPOExternalAdapter` (`bpo_externo_api.py`)
* Implementa `IExternalPlatform`. [cite_start]Simula la creación del caso en la empresa .
* [cite_start]**Feature Flag (BONO +4%):** Lee la variable booleana `SIMULAR_FALLOS_BPO` desde `core.config.settings` .
* **Lógica `create_case(data: dict)`:**
  1. Haz un `await asyncio.sleep(1)`.
  2. `if settings.SIMULAR_FALLOS_BPO:` lanza la excepción personalizada `ExternalPlatformError`.
  3. Si no, retorna `"ID" + str(uuid.uuid4())[:8]`.

### B. `MensajeriaValleAdapter` (`mensajeria_api.py`)
* **IMPORTANTE - Scope Arquitectónico:** Este adaptador **NO** implementa `IExternalPlatform` ni `ILLMProvider`. [cite_start]Es un puerto/adaptador *ad-hoc* (HTTP Client aislado) que será inyectado EXCLUSIVAMENTE en la estrategia de Mensajería del Valle para obtener la prioridad [cite: 110-115].
* Método: `async def get_priority_from_client(tipo_documento: str, numero_documento: str, tipo_solicitud: str) -> str`.
* Retorna "Alta", "Media" o "Baja" (ej. "Alta" si contiene "Retraso"). Haz un `await asyncio.sleep(0.5)`.

## 3. Adaptador de Estado en Memoria (`app/core/state.py`)
* Implementa `ICacheProvider`. Crea la clase `InMemoryCache`.
* Usa un `set()` en memoria para guardar los `solicitud_id`. 
* Provee métodos `is_duplicate` y `register` para evitar procesar el mismo ID dos veces.

## 📝 Instrucciones de Calidad para Antigravity
1. **Configuración:** Agrega `SIMULAR_FALLOS_BPO: bool = False` al esquema de Pydantic Settings en `app/core/config.py`.
2. **Trazabilidad Estructurada (BONO +4%):** Cada vez que atrapes un error en el `LLMManager` o lances un error en el `BPOExternalAdapter`, DEBES incluir el `solicitud_id` en el mensaje de log.
   * *Mal:* `logging.error("La plataforma falló")`
   * *Bien:* `logging.error(f"Falla en plataforma externa para solicitud_id={solicitud_id}. Detalle: ...")`