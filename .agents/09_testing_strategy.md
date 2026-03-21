# 🧪 ESTRATEGIA DE PRUEBAS AUTOMATIZADAS (09_testing_strategy)

## 🎯 Objetivo
Desarrollar una suite de pruebas robusta usando `pytest` y `pytest-asyncio`. El objetivo principal es garantizar la cobertura de la lógica de negocio aislando el dominio (pruebas unitarias puras) y probando la capa de entrega (pruebas de integración API), **SIN realizar ni una sola petición de red real** a las APIs de LLM o plataformas externas.

## 1. Configuración y Fixtures (`tests/conftest.py`)

Debes crear un archivo de configuración de pruebas que provea las dependencias "falsas" (mocks).
* **`mock_tenant_config`:** Un fixture que retorne un diccionario con el YAML de configuración de "GASES DEL ORINOCO" y "MENSAJERIA DEL VALLE".
* **`mock_llm_provider`:** Un `AsyncMock` de la interfaz `ILLMProvider` que retorne JSONs predefinidos para los pasos del 1 al 4.
* **`mock_external_platform`:** Un `AsyncMock` de `IExternalPlatform` que retorne `"ID-MOCK-123"`.
* **`app_client`:** Un fixture que configure el `TestClient` de FastAPI, haciendo un *override* de las dependencias (`app.dependency_overrides`) para inyectar los mocks en los endpoints.

## 2. Pruebas Unitarias Puras (El Hexágono Central)

Aprovechando la Arquitectura Hexagonal, DEBES escribir tests que aíslen la lógica de negocio sin usar FastAPI ni `TestClient`.

* **Test de las Estrategias (`tests/test_strategies.py`):**
  Instancia `DefaultStrategy` pasándole un `ProcesamientoEstado` simulado. [cite_start]Verifica que `validate_requirements` retorne `False` si falta un campo obligatorio, y `True` si están todos [cite: 25-26]. [cite_start]Verifica que `get_routing` retorne el valor correcto del YAML sin necesidad de HTTP [cite: 30-31, 54-56].
* **Test del Orquestador Aislado (`tests/test_orchestrator.py`):**
  Instancia `PipelineOrchestrator` inyectándole directamente los mocks de dependencias en su constructor. Llama a `await orchestrator.run(request)` y verifica las transiciones de estado del objeto interno.

## 3. Pruebas de Integración de la API (`tests/test_api.py`)

Usa el `app_client` (FastAPI `TestClient`) para probar los endpoints expuestos y el manejo de errores HTTP.

* **Test Happy Path (Gases del Orinoco):**
  Envía un payload válido al endpoint `POST /api/v1/solicitudes`. Verifica que la respuesta HTTP sea 200 OK, el `estado` final sea `"pendiente"`, y `solicitud_id_plataforma_externa` no sea nulo.
* **Test Early Exit (Información Faltante):**
  Envía un payload y configura el mock del LLM para extraer un campo como `null`. Verifica que la respuesta HTTP sea 200 OK, pero el JSON de salida tenga estado `"cerrado"` y justificación "Información incompleta".
* **Test de Excepciones HTTP:**
  Envía un request con una compañía que no existe en el YAML. Verifica que la API atrape el `CompanyNotFoundError` y devuelva un error HTTP estructurado (ej. 400 Bad Request o 404 Not Found).

## 4. Pruebas de los Bonos (+10% Extra) (`tests/test_bonos.py`)

* [cite_start]**Test Estrategia Mensajería del Valle (+6%):** [cite: 110-115]
  Inyecta un payload de esta compañía en el Orquestador aislado. Verifica mediante `mock.assert_called_once()` que el mock del `MensajeriaValleAdapter` fue llamado, y que `mock_llm_provider.prioritize` NUNCA fue llamado.
* **Test Control de Duplicados (+4%):**
  Usa el `app_client` para enviar exactamente el mismo JSON dos veces seguidas. Verifica que la primera llamada retorne 200 OK y la segunda retorne HTTP 409 Conflict.
* **Test Resiliencia Plataforma Externa (+4%):** [cite: 106-107]
  Configura el `mock_external_platform.create_case` para que lance `ExternalPlatformError`. Verifica que el request finalice con 200 OK, el `estado` sea `"pendiente"`, el ID externo sea `None`, y la justificación mencione la falla.

## 5. Pruebas del Fallback de IA (`tests/test_llm_manager.py`)

* **Test Recuperación Automática:**
  Instancia el `LLMManager` inyectándole un `mock_groq` y un `mock_gemini`. Configura `mock_groq.classify` para que lance `LLMOutputError`. Verifica que el manager atrape el error, llame a `mock_gemini.classify`, y retorne el resultado exitoso.

## 📝 Instrucciones de Calidad para Antigravity
1. **Cero Red Real:** ESTÁ ESTRICTAMENTE PROHIBIDO dejar llamadas HTTP reales hacia Groq o Gemini en los tests.
2. **Limpieza de Estado:** Asegúrate de limpiar el `InMemoryCache` (`cache.clear()`) en un fixture de `yield` para que los tests de duplicados no interfieran con el resto de la suite.