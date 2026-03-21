# ⚙️ ORQUESTACIÓN DEL PIPELINE (04_pipeline_orchestration)

## 🎯 Objetivo
[cite_start]Implementar la capa de Aplicación coordinando la ejecución secuencial de los 6 pasos definidos en el caso de estudio [cite: 24-36]. El orquestador (`PipelineOrchestrator`) moverá el `ProcesamientoEstado` a través de los eslabones de la cadena.

## 1. El Orquestador (`app/pipeline/orchestrator.py`)

Crea la clase `PipelineOrchestrator` implementando la interfaz `IPipelineOrchestrator`.

### A. Inyección de Dependencias (Constructor)
El constructor `__init__` DEBE recibir todas las dependencias instanciadas:
* `cache_provider`: `ICacheProvider`
* `strategy_factory`: `StrategyFactory`
* `llm_provider`: `ILLMProvider`
* `external_platform`: `IExternalPlatform`
* `yaml_config`: `dict`

### B. El Método Principal: `async def run(self, request: SolicitudInput) -> SolicitudOutput`

Ejecuta la secuencia. Usa logs estructurados (`logging.info`) en cada cambio de estado, incluyendo SIEMPRE el `request.solicitud_id`.

**Secuencia estricta de ejecución:**

1.  **Control de Duplicados (Bono +4%):**
    * Verifica `await self.cache_provider.is_duplicate(request.solicitud_id)`.
    * Si existe, lanza `DuplicateRequestError`.
    * Si no, regístralo con `await self.cache_provider.register(request.solicitud_id)`.

2.  **Resolución de Contexto y Estrategia:**
    * Verifica si `request.compania` existe en `self.yaml_config["empresas"]`. Si no, lanza `CompanyNotFoundError`.
    * Extrae el `tenant_config` de esa empresa.
    * Resuelve la estrategia: `strategy = self.strategy_factory.get_strategy(request.compania, tenant_config)`.
    * Inicializa el estado: `estado = ProcesamientoEstado(request_original=request, tenant_config=tenant_config)`.

3.  [cite_start]**Paso 1: Validar Información [cite: 25-26]:**
    * Llama al `llm_provider.extract_entities` pasando el texto y `tenant_config["campos_obligatorios"]`.
    * Guarda en `estado.datos_extraidos`.
    * Ejecuta `strategy.validate_requirements(estado)`.
    * **Early Exit:** Si retorna `False`, define `estado.proximo_paso = "CIERRE_POR_INFORMACION_INSUFICIENTE"`, justificación "Información incompleta o faltante", y SALTA al paso 9 (Cierre y Mapeo).

4.  **Paso 2: Clasificar:**
    * [cite_start]Llama a `await self.llm_provider.classify(...)` pasando el texto original y las `categorias` permitidas del YAML[cite: 27].
    * Guarda en `estado.categoria`.

5.  **Paso 3: Priorizar:**
    * Ejecuta `await strategy.get_priority(estado, self.llm_provider)`.
    * [cite_start]Guarda en `estado.prioridad` ("Alta", "Media" o "Baja")[cite: 28].

6.  [cite_start]**Paso 4: Justificar:**
    * Llama a `await self.llm_provider.justify(...)` pasando el texto original, la categoría y la prioridad calculada.
    * Guarda en `estado.justificacion`.

7.  [cite_start]**Paso 5: Enrutamiento [cite: 30-31]:**
    * Ejecuta `strategy.get_routing(estado)`.
    * Guarda en `estado.proximo_paso` ("GESTIÓN EXTERNA" o "RESPUESTA DIRECTA").

8.  [cite_start]**Paso 6: Gestión Externa [cite: 32-34]:**
    * `if estado.proximo_paso == "GESTIÓN EXTERNA":`
        * Envuelve `await self.external_platform.create_case(...)` en `try/except ExternalPlatformError`.
        * Si falla, emite un `logging.error`, deja el `id_plataforma_externa` como `None` y añade a la justificación: "(Advertencia: Falla de red al crear caso)".
        * Si funciona, guarda el ID en `estado.id_plataforma_externa`.

9.  [cite_start]**Cierre y Mapeo (Reglas Estrictas de Estado)[cite: 26, 32, 35]:**
    * Construye y retorna el `SolicitudOutput` mapeando los datos. Usa `datetime.now().strftime("%Y-%m-%d")` para la fecha.
    * **Mapeo del campo `estado`:** Aplica esta lógica exacta:
        * Si `proximo_paso` es "GESTIÓN EXTERNA", el estado DEBE ser `"pendiente"`.
        * Si `proximo_paso` es "RESPUESTA DIRECTA", el estado DEBE ser `"cerrado"`.
        * Si hubo Early Exit en el Paso 1, el estado DEBE ser `"cerrado"`.

## 📝 Reglas de Calidad para Antigravity
* **Propagación de Errores Core:** NO atrapes `CompanyNotFoundError` ni `DuplicateRequestError` dentro del método `run()`. Deja que estas excepciones "burbujeen" hacia la capa de FastAPI (`api/routers.py`), donde un Exception Handler las convertirá en respuestas HTTP 400 o 409.
* **Logging Estricto:** Registra `logging.debug(f"[{request.solicitud_id}] Completado Paso X...")` en cada transición.