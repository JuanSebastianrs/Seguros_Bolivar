# ♟️ PATRÓN STRATEGY Y FACTORY (03_strategies)

## 🎯 Objetivo
[cite_start]Implementar la lógica de negocio variable por cliente mediante el Patrón Strategy, cumpliendo con el principio Open/Closed[cite: 103]. [cite_start]El sistema debe soportar nuevas compañías modificando solo el YAML, a menos que el cliente requiera integraciones ad-hoc (como Mensajería del Valle) [cite: 110-115].

## 1. La Estrategia Base (`app/strategies/default_rules.py`)

Crea la clase `DefaultStrategy` que implemente la interfaz `ICompanyStrategy`. Esta estrategia es agnóstica y funciona basándose puramente en el `tenant_config` inyectado en el estado.

* **`validate_requirements(self, estado: ProcesamientoEstado) -> bool`:**
    Extrae la lista `campos_obligatorios` del `estado.tenant_config`. [cite_start]Revisa si el `estado.datos_extraidos` contiene llaves no nulas para todos esos campos [cite: 25-26].
* **`async def get_priority(self, estado: ProcesamientoEstado, llm_provider: ILLMProvider) -> str`:**
    Usa el `llm_provider.prioritize(...)` pasándole el texto y la categoría para que la IA determine "Alta", "Media" o "Baja".
* **`def get_routing(self, estado: ProcesamientoEstado) -> str`:**
    Busca en `estado.tenant_config["reglas_enrutamiento"]`. Usa `estado.categoria` y `estado.prioridad` como llaves para retornar el valor final.
    * **CRÍTICO - Defensa contra KeyErrors:** Si la combinación exacta de categoría y prioridad devuelta por el LLM no existe en el YAML (alucinación de IA), atrapa el `KeyError`, registra un `logging.error(...)` con el ID de la solicitud y retorna `"GESTION_EXTERNA"` por defecto para no romper la ejecución de la API y asegurar atención humana.

## 2. La Estrategia Personalizada (BONO +6%) (`app/strategies/mensajeria_valle.py`)

Crea la clase `MensajeriaValleStrategy` que herede de `DefaultStrategy`. [cite_start]Esta compañía no usa IA para la prioridad [cite: 113-115].

* **Inyección de Dependencia Estricta:** ESTÁ PROHIBIDO que `MensajeriaValleStrategy` instancie su propio adaptador. El `MensajeriaValleAdapter` DEBE ser inyectado a través del constructor `__init__(self, adaptador_mensajeria)`.
* **Sobreescritura (`override`) de `get_priority`:** IGNORA el `llm_provider`.
    * Extrae `tipo_documento` y `numero_documento` de `estado.datos_extraidos` (Paso 1).
    * **CRÍTICO:** El argumento `tipo_solicitud` que pide el adaptador externo DEBE ser el valor guardado en `estado.categoria` (generado en el Paso 2). NO lo busques en los datos extraídos.
    * [cite_start]Retorna el resultado de `await self.adaptador_mensajeria.get_priority_from_client(...)` [cite: 114-115].
* Los métodos `validate_requirements` y `get_routing` se heredan intactos.

## 3. El Factory (`app/strategies/factory.py`)

Crea la clase `StrategyFactory` para instanciar la estrategia correcta en tiempo de ejecución.

* **Constructor:** Recibe las dependencias necesarias (ej. `adaptador_mensajeria`) para poder inyectarlas en las estrategias que lo requieran.
* **Método `def get_strategy(compania: str, tenant_config: dict) -> ICompanyStrategy`:**
    * [cite_start]Si la compañía no existe en el YAML de configuración, **DEBE lanzar** la excepción personalizada `CompanyNotFoundError`[cite: 109].
    * Si `compania == "MENSAJERIA DEL VALLE"`, retorna una instancia de `MensajeriaValleStrategy` inyectándole el adaptador.
    * Para cualquier otra compañía válida, retorna `DefaultStrategy`.
    * Emite un `logging.info` indicando qué estrategia se resolvió.