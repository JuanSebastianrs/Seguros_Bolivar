# 🏛️ ARQUITECTURA DEL SISTEMA: HEXAGONAL PRAGMÁTICA (01_arquitectura)

## 🎯 Objetivo y Contexto del Problema
El sistema resuelve el reto de una empresa BPO que procesa solicitudes de texto libre para múltiples compañías clientes (multitenant). El flujo incluye validación, clasificación, priorización con IA, justificación y enrutamiento hacia plataformas externas o respuestas directas. 
Para garantizar escalabilidad, bajo acoplamiento y facilidad de pruebas, el código se estructura bajo los principios de la **Arquitectura Hexagonal (Puertos y Adaptadores)** combinada con patrones de diseño estratégicos.

## 1. El Paradigma Hexagonal (Puertos y Adaptadores)

Siguiendo la teoría de puertos y adaptadores, el sistema separa estrictamente la lógica de negocio pura (el qué) de las tecnologías externas (el cómo). 

### A. El Dominio (El Hexágono Central)
Directorio: `app/domain/`, `app/pipeline/`, `app/strategies/`
Es el núcleo del sistema. No sabe que existe FastAPI, ni Groq, ni Gemini, ni bases de datos. 
* Contiene el estado inmutable (`ProcesamientoEstado`).
* Define los **Puertos** (Interfaces/Clases Base Abstractas) que dictan cómo el dominio quiere comunicarse con el mundo exterior.
* Contiene la lógica de orquestación (Chain of Responsibility) y las reglas por cliente (Strategy).

### B. Adaptadores Primarios (Driving Adapters - Entrada)
Directorio: `app/api/`
Son los que invocan al dominio desde el exterior. 
* **FastAPI (`routers.py`)**: Actúa como el adaptador de entrada. Recibe la petición HTTP POST, la convierte en un objeto Pydantic (`SolicitudInput`) y llama al Puerto de Entrada del dominio (el método `run` del `PipelineOrchestrator`).

### C. Adaptadores Secundarios (Driven Adapters - Salida)
Directorio: `app/adapters/`, `app/core/state.py`
Son las implementaciones tecnológicas concretas que el dominio utiliza a través de sus puertos.
* **Mocks Externos (`bpo_externo_api.py`, `mensajeria_api.py`)**: Implementan la comunicación simulada con plataformas de clientes (BPO y Mensajería del Valle).
* **Proveedores de IA (`llm_groq.py`, `llm_gemini.py`, `llm_manager.py`)**: Implementan el puerto `ILLMProvider` para interactuar con los modelos generativos.
* **Memoria/Caché (`state.py`)**: Implementa el puerto `ICacheProvider` para controlar los casos duplicados.

## 2. Patrones de Diseño Complementarios

La Arquitectura Hexagonal establece los límites, pero dentro del dominio usamos patrones específicos para resolver la complejidad del BPO:

### A. Patrón Strategy (Multitenant)
* **El Problema:** El BPO maneja múltiples clientes con reglas distintas. Si usamos bloques `if/elif` gigantes, el código violará el principio *Open/Closed*.
* **La Solución:** `ICompanyStrategy`. Cada cliente ("Gases del Orinoco", etc.) utiliza una estrategia `DefaultStrategy` alimentada por el YAML. Si un cliente tiene integraciones únicas (como "Mensajería del Valle" que usa un servicio externo en vez de IA para la prioridad), se crea una subclase `MensajeriaValleStrategy` inyectándole su adaptador específico. Un `StrategyFactory` decide cuál usar en tiempo de ejecución.

### B. Patrón Chain of Responsibility (El Pipeline)
* **El Problema:** El procesamiento de la solicitud tiene 6 pasos secuenciales que pueden abortarse prematuramente (Early Exit si falta información).
* **La Solución:** `PipelineOrchestrator`. Coordina el paso del objeto `ProcesamientoEstado` a través de los eslabones: Validar -> Clasificar -> Priorizar -> Justificar -> Enrutar -> Gestionar. Si el eslabón 1 falla, corta la cadena y retorna el resultado inmediatamente.

### C. Patrón Fallback (Resiliencia de IA)
* **El Problema:** Las APIs de LLM (especialmente en tiers gratuitos) sufren de rate limits y caídas.
* **La Solución:** El `LLMManager` actúa como un adaptador inteligente (patrón Proxy/Decorator). Implementa el mismo puerto `ILLMProvider`. Intenta ejecutar la acción con el adaptador primario (Groq); si falla, atrapa el error y redirige silenciosamente la petición al adaptador secundario (Gemini).

## 3. Principio de Inversión de Dependencia (Inyección)
Para que el hexágono se mantenga puro, **ninguna clase del dominio puede instanciar a sus adaptadores**. 
La capa de FastAPI (`api/routers.py` a través de `Depends()`) será la encargada de instanciar la caché, el gestor de LLMs, la fábrica de estrategias y pasarlos como argumentos al constructor del Orquestador.

## 📝 Reglas Mentales para Antigravity
Al momento de programar, hazte estas preguntas:
1. *"¿Estoy importando `httpx`, `groq` o `google.generativeai` dentro de la carpeta `pipeline` o `strategies`?"* -> Si la respuesta es sí, estás rompiendo la arquitectura. Esos imports solo viven en `adapters/`.
2. *"¿Estoy instanciando una clase concreta dentro de otra clase de negocio?"* -> Prohibido. Pídela por el constructor (Inyección de dependencias).