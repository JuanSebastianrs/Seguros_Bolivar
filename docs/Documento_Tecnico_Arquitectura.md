# Microservicio Inteligencia Artificial BPO
**Documento Técnico de Arquitectura y Escalabilidad**

*Elaborado para Seguros Bolívar - Caso de Estudio IA [Profesional Senior]*

---

## 1. Diseño de Arquitectura: Hexagonal y Patrones de Diseño

El microservicio Backend fue diseñado aplicando rigurosamente los lineamientos de la **Arquitectura Hexagonal (Puertos y Adaptadores)**. Su principal objetivo es promover el principio de **Inversión de Dependencias**, dejando al dominio en el centro, ajeno al framework de la API o los LLMs puntuales, e interactuando únicamente a través de "Puertos" (Interfaces/ABCs abstractas en Python).

### Componentes de la Arquitectura

1.  **Dominio (Centro del Hexágono):**
    *   **Puertos Salientes (_Driven Ports_):** `ILLMProvider`, `IExternalPlatform`, `ICompanyStrategy`, `ICacheProvider`.
    *   **Contratos / Modelos:** `ProcesamientoEstado` (Estado mutado asíncronamente en el Pipeline), `schemas_llm.py` (Definición estricta Pydantic para la IA), Prompts puros f-strings sin dependencias HTTP.
2.  **Driving Adapters (Lado Izquierdo - Entrada):**
    *   **Pydantic API Schemas (`api/schemas.py`):** Serialización y mitigación de inputs. Se agregó configuración especial para el cumplimiento de la salida `Solicitud_fecha`.
    *   **FastAPI Routers (`api/routers.py`):** Inyectan explícitamente las dependencias de los Adaptadores (_Bottom-Up_) hacia el Orquestador del Dominio por medio de `Depends()`.
3.  **Driven Adapters (Lado Derecho - Salida):**
    *   **Lógica Concreta Externa:** `GroqAdapter` (REST HTTP con cliente nativo), `GeminiAdapter` (Google GenAI API), `BPOExternalAdapter` Mock y memoria del Caché.

### Patrones de Diseño Implementados

*   **Strategy Pattern & Factory:** Se mitigó la violación al principio *Open/Closed (SOLID)* para soportar la naturaleza Multi-Tenant. Se introdujo `tenants_config.yaml` que contiene los metadatos de campos requeridos, categorización, y la matriz de enrutamiento por cruce de prioridades de cada cliente. La Fábrica `StrategyFactory` despacha al vuelo una instancia genérica `DefaultStrategy` en el 90% de los casos o una especializada `MensajeriaValleStrategy` que puentea a las APIS del cliente, logrando así evitar llenar la base de código de `if/elif`.
*   **Chain of Responsibility:** Patrón central residente en `PipelineOrchestrator`, encargado de recibir un contrato y mutar de paso 1 al paso 6 (`ProcesamientoEstado`). Admite una salida anticipada (_Early Return_) si la extracción del LLM detecta ausencia de datos requeridos por el YAML.
*   **Proxy / Fallback Decorator (`LLMManager`):** Envolver los LLMs en un Manager unificado implementando la misma Interfaz `ILLMProvider`. Si un Rate Limit salta en Groq, la llamada se intercepta, emitirá Warning en Log, e instanciará *Gemini flash* para recuperar la PQR sin romper al usuario.

---

## 2. Decisiones Técnicas: Stack y Tolerancia a Fallas

1.  **FastAPI + Pydantic V2:** Permite concurrencia natural Asíncrona (`asyncio`), necesaria ya que el 90% del tiempo de ejecución consiste en una latencia E/S contra LLMs. Pydantic impone estrictas mallas frente a alucinaciones (JSON mode).
2.  **El Problema de Alucinación (Deterministic Prompts):**
    Se emplean respuestas forzadas de JSON (`response_format={"type": "json_object"}`). Temperatura estriñida a `0.0` para un LLM analítico estricto. El Orquestador captura si el LLM miente sobre Prioridad o un Keyword no listado. El sistema incluye una contingencia por omisión si arroja algo errático (`KeyError` evitada devolviendo una prioridad "GESTIÓN EXTERNA"). 
3.  **LLMs Seleccionados:**
    *   *Groq (llama-3.3-70b-versatile):* Como servicio Primario. Capacidad reflexiva fuerte y altísima velocidad.
    *   *Google Gemini (Gemini 2.5 flash):* LLM secundario usado como Fallback ante indisponibilidad, con coste casi nulo.
4.  **Inclusión de Bonos y Correcciones de Lógica:**
    *   **Corrección de Esquemas:** Se corrigió un error semántico presente en el PDF de requerimientos donde `solicitud_tipo_id_cliente` tenía un ID y viceversa. Mapeamos las llaves rigurosamente para garantizar la consistencia en una futura Base de Datos relacional.
    *   **+4% Duplicados:** Mediante Hasheo/Set de `InMemoryCache`.
    *   **+4% Plataforma Externa Falla:** Se captura `ExternalPlatformError` sin romper el flujo, agregando una Advertencia en la justificación.
    *   **+6% Mensajería Valle:** Herencia de Estrategia inyectando Mock con Sleep HTTP.

---

## 3. Estrategia de Escalabilidad a Futuro (GCP & Nube)

### Contenerización Inmutable (Lograda) y Serverless
El entregable actual ya se encuentra contenerizado (`Dockerfile` y `docker-compose.yml` listos), garantizando la inmutabilidad local. Para producción, el contenedor es el candidato ideal para desplegarse mediante **GCP Cloud Run**, permitiendo escalar de cero a miles de instancias automáticamente sin aprovisionar infraestructura manual, cobrando exclusivamente por uso real.

### Seguridad y Gestión de Secretos (Google Secret Manager)
Las API Keys (Groq, Gemini) no se exponen jamás en el código fuente (se orquestan vía `.env` local y `.gitignore`). En producción, se inyectarían dinámicamente utilizando **Google Secret Manager** para asegurar la bóveda de credenciales.

### Autenticación Cero-Trust del BPO
Puesto que nuestro endpoint REST será consumido por clientes externos, en la Fase 2 debe prevenirse el agotamiento de cuotas del API del LLM. Se sugiere añadir un middleware global mediante validación **JWT (OAuth 2.0)** o rotación de API Keys dedicadas por cliente en el header HTTP.

### De Memoria Volátil a Cloud Redis
Actualmente el `InMemoryCache` evita duplicados en un mismo proceso. La modularización del `ICacheProvider` se acoplaría a **GCP Memorystore (Redis)** para compartir el estado de rechazo simultáneo a través de las cientos de instancias levantadas por Cloud Run.


### Workers Asíncronos Desacoplados (Celery / RabbitMQ / SQS)
Actualmente, el Request aísla el Thread HTTP hasta resolver 4 LLM round-trips (Paso 1 -> Paso 4). Una mejor solución a largo plazo (si se esperan >5,000 requests / min):
*   FastAPI acepta Request BPO -> Manda JSON a un Topic Pub/Sub / SQS Queue. Da HTTP 202 Accepted de inmediato.
*   Servicios Worker asíncronos en Background se dedican exclusivamente a orquestar el `PipelineOrchestrator`. 
*   Si los Rate limits son persistentes o caen Groq y Gemini a la vez (por ejemplo, fallo regional Cloud), los mensajes en la Queue tienen Retry Behavior + Dead Letter Queue y se intentan más tarde sin perder métricas del PQR.

### DB Multitenant YAML
Migrar las reglas de `data/tenants_config.yaml` a una BD NoSQL / Parameter Store donde un administrador agregue Empresas Dinámicas vía Front End sin necesidad de hacer Push de un repo, consumiéndolas dinámicamente con TTL Cachés locales.
