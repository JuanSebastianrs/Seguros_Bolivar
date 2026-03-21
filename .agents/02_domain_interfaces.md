# 🔌 DEFINICIÓN DE INTERFACES Y CONTRATOS DE DOMINIO (02_domain_interfaces)

## 🎯 Objetivo
Establecer las Clases Base Abstractas (ABC) que definen los **Puertos de Salida** y el **Modelo de Dominio**. Esto garantiza el bajo acoplamiento de la Arquitectura Hexagonal, permitiendo que el Pipeline sea agnóstico a la infraestructura (LLMs, bases de datos, APIs externas).

## 1. El Estado del Pipeline (`app/domain/models.py`)

El pipeline necesita un objeto que mute a lo largo de los 6 pasos y que acarree la configuración leída del YAML para evitar lecturas repetitivas en disco.

Crea la clase `ProcesamientoEstado` (puede ser un Pydantic BaseModel o DataClass):
* `request_original`: `SolicitudInput` (Los datos de entrada intactos).
* `tenant_config`: `dict` (La configuración específica de la empresa extraída del YAML).
* `datos_extraidos`: `dict` (Datos extraídos en el Paso 1, ej. cédula, tipo).
* `categoria`: `str | None` (Resultado del Paso 2).
* `prioridad`: `str | None` (Resultado del Paso 3).
* `justificacion`: `str | None` (Resultado del Paso 4).
* `proximo_paso`: `str | None` (Resultado del Paso 5, ej. "GESTIÓN EXTERNA" [cite: 55-56]).
* `id_plataforma_externa`: `str | None` (Resultado del Paso 6).

## 2. Puertos de Salida (Interfaces) (`app/domain/interfaces.py`)

Usa `from abc import ABC, abstractmethod`. Todos los métodos que impliquen I/O deben ser `async`.

### A. `ILLMProvider` (Puerto para IA)
Define los métodos atómicos para interactuar con Groq/Gemini.
* `@abstractmethod async def extract_entities(text: str, schema: dict) -> dict`
* `@abstractmethod async def classify(text: str, categories: list[str]) -> str`
* `@abstractmethod async def prioritize(text: str, category: str) -> str`
* `@abstractmethod async def justify(text: str, category: str, priority: str) -> str`
*(Nota para Antigravity: En la implementación real del adaptador, podrías usar un método unificado `analyze_request` bajo el capó para reducir la latencia, pero la interfaz del dominio debe mantener la granularidad).*

### B. `IExternalPlatform` (Puerto para BPO Externo)
[cite_start]Define la interacción con la plataforma de ticketing del cliente [cite: 58-59].
* `@abstractmethod async def create_case(data: dict) -> str`: Debe retornar un ID ficticio (ej. "ID123456789").
* [cite_start]**Excepción Asociada:** El adaptador que implemente esto debe lanzar `ExternalPlatformError` si falla, para que el orquestador maneje el reintento/log .

### C. `ICompanyStrategy` (Puerto para Estrategias de Negocio)
[cite_start]Define cómo varía el comportamiento del pipeline según la empresa cliente[cite: 4, 5].
* `@abstractmethod def validate_requirements(self, estado: ProcesamientoEstado) -> bool`: Lógica del Paso 1.
* `@abstractmethod async def get_priority(self, estado: ProcesamientoEstado, llm_provider: ILLMProvider) -> str`: Lógica del Paso 3. **CRÍTICO:** Recibe el `llm_provider` inyectado. [cite_start]La estrategia normal lo usará; la estrategia de *Mensajería del Valle* lo ignorará y llamará a su adaptador externo .
* [cite_start]`@abstractmethod def get_routing(self, estado: ProcesamientoEstado) -> str`: Lógica del Paso 5 [cite: 54-57].

### D. `ICacheProvider` (Puerto para Control de Duplicados)
[cite_start]Para cumplir con el requerimiento de evitar solicitudes duplicadas.
* `@abstractmethod async def is_duplicate(solicitud_id: str) -> bool`
* `@abstractmethod async def register(solicitud_id: str) -> None`

## 3. El Puerto de Entrada (`IPipelineOrchestrator`)
[cite_start]Garantiza el patrón *Chain of Responsibility* [cite: 46-47].
* `@abstractmethod async def run(request: SolicitudInput) -> SolicitudOutput`: El método principal expuesto a FastAPI.

## 📝 Reglas Estrictas para Antigravity
1. **NO IMPLEMENTES LÓGICA DE NEGOCIO AQUÍ.** Estos archivos solo deben contener firmas (signatures), clases `ABC` y definiciones de tipos (`Type Hints`).
2. Las excepciones (ej. `ExternalPlatformError`, `DuplicateRequestError`) deben definirse en un archivo separado `app/core/exceptions.py`.