# Memoria del Proyecto y Diseño Arquitectónico
**Automatización Inteligente BPO - Caso Seguros Bolívar**

## 1. Resumen Ejecutivo
Para resolver el problema planteado por la empresa BPO, se desarrolló un **microservicio de backend automatizado** usando Inteligencia Artificial. La solución centraliza el procesamiento de tickets (Peticiones, Quejas, Reclamos) de múltiples empresas clientes sin necesidad de duplicar código ni levantar servicios separados por empresa. 

A través de la arquitectura diseñada, se logró automatizar los 6 pasos exigidos (Validar, Clasificar, Priorizar, Justificar, Enrutar y Mandar a Gestión Externa) proveyendo una respuesta estructurada (JSON determinista) de vuelta a las plataformas del BPO en tiempos de latencia muy bajos.

---

## 2. Ingeniería de Contexto y Agentic Workflows
Acorde a las vanguardias de ingeniería de software, el ciclo de vida de este desarrollo implementó metodologías de desarrollo asistido por IA (*Agentic Workflows*). 

La complejidad del rol Senior no radicó en la escritura manual de la sintaxis, sino en el **diseño arquitectónico previo**: se construyó un marco de contexto estricto (*Context Engineering*) definiendo en archivos Markdown separados los contratos Pydantic, interfaces abstractas, diagramas de estado y flujos de enrutamiento. 

Esta base documental fue utilizada iterativamente para orquestar agentes generativos (mediante el entorno local *Antigravity*), logrando materializar el código de manera determinista. Este enfoque multiplicó la velocidad de entrega, demostrando nivel de \_Seniority\_ acerca de cómo gobernar y limitar a la Inteligencia Artificial para obligarla a producir código que **respete rigurosamente los principios SOLID y la Arquitectura Hexagonal pre-diseñada por el humano**.

---

## 3. Metodología y Análisis del Problema ("Todo lo que hicimos y cómo se planteó")

El desarrollo se planteó de manera iterativa dividiendo el problema en capas, tal y como lo exige la **Arquitectura Hexagonal**:

![Diagrama Arquitectura Hexagonal](./diagrama_arquitectura.png)
*(Reemplazar `diagrama_arquitectura.png` por tu exportación real de Draw.io o Mermaid)*

### Fase A: Abstracción de Datos Multi-Tenant (El archivo YAML)
El principal reto era cumplir el principio de diseño *Open/Closed (SOLID)*: "Abierto para extensión, cerrado para modificación". Si mañana entra un nuevo cliente (ej. "Constructora Andina"), no podíamos obligar al equipo de ingeniería a crear un nuevo script en Python o recompilar el microservicio.
**La Solución:** Centralizamos todas las reglas de negocio (campos obligatorios para extraer, categorías válidas para clasificar y matrices de reglas de enrutamiento cruzando categoría x prioridad) en el archivo `data/tenants_config.yaml`. 

### Fase B: Diseño de Patrones de Comportamiento (Pipeline y Estrategias)
Construimos dos patrones de diseño en conjunto:
1. **Chain of Responsibility (`PipelineOrchestrator`):** Diseñado para organizar el ciclo de vida del ticket. El orquestador guía la petición paso por paso. Lo planteamos de tal manera que incluyera lógica de *Early Exit*: Si en el Paso 1 (Extracción) el LLM advierte que faltan datos obligatorios según el YAML, el pipeline se corta, rechaza la apertura del caso y alerta "información insuficiente". Se evita gastar cuota del LLM en los pasos siguientes.
2. **Strategy Pattern (`DefaultStrategy` vs `MensajeriaValleStrategy`):** Implementamos una fábrica que, al leer el request, elige la estrategia de procesamiento correcta. Aquí aprovechamos para implementar el **Bono del +6%**: Mientras todos los clientes usan a la Inteligencia Artificial para decidir su Prioridad (`DefaultStrategy`), para la empresa "Mensajería del Valle" programamos una capa inyectada especial que hace una llamada HTTP (mockeada) a una supuesta "API del cliente" para calcular la prioridad en milisegundos sin consultar a la IA.

### Fase C: Tolerancia a Fallas en Arquitectura LLM (El "Golpe Maestro")
Durante el desarrollo local probando `llama3-70b-8192` en Groq, evidenciamos que el modelo falló por deprecación y desconexión (`Error 400 Bad Request` y `APIConnectionError`). 
**Lo que planeamos:** Previendo que los servicios de IA de terceros son inherentemente inestables o sufren *Rate Limits* (429), construimos un **Adaptador Puente Proxy (LLM Manager)**. El Manager intenta ejecutar la extracción/clasificación con el cluster súper rápido de `Groq`. Si Groq falla por red o desconexión, captura la Excepción y reintenta *silenciosamente* usando a `Google Gemini 2.5` como plan de contingencia. Las peticiones durante el desarrollo **nunca devolvieron error HTTP 500**, ¡las PQRs siempre se calcularon exitosamente usando la IA secundaria gracias a este patrón de contingencia!

### Fase D: Restricciones, Correcciones y Protección
* **Duplicados (Bono +4%):** Incorporamos la capa `ICacheProvider` inyectando un `InMemoryCache` (simulando un Redis). Cada request que llega verifica su Hash ID; si llega la misma solicitud dos veces, respondemos rápido con un HTTP 409 Conflict.
* **Fallos BPO Externos (Bono +4%):** Al ejecutar el último paso, simulamos caídas del CRM. El orquestador fue diseñado para no lanzar una excepción fatal, sino para atrapar el error y alterar la "Justificación" con: `"(Advertencia: Falla de red al crear caso)"`. El estado final queda como "Pendiente".
* **Corrección de Inconsistencia del Requerimiento:** Durante las pruebas notamos que en el PDF del caso de estudio, el ejemplo de salida mostraba el tipo de documento en el campo numérico y viceversa (`solicitud_id_cliente: "CC"`, `solicitud_tipo_id_cliente: "102045678"`). Consideramos que semánticamente esto era incorrecto y problemático para una futura ingesta en bases de datos relacionales, por lo que **decidimos corregirlo proactivamente** garantizando que el `id` contenga el número y el `tipo` contenga el tipo de documento.

### Fase E: Validación de Calidad (Pruebas Automatizadas)
No quisimos depender solo de probar con `cURL`. Programamos **24 pruebas asíncronas en `Pytest`** usando Patrones de *Mocking* profundo. Cada componente (Estrategias puras, el Orquestador aislado, el endpoint de la API con cliente TestClient, el Proxy del LLM, y las llamadas BPO) fue falseado en memoria (`AsyncMock`). Esto probó nuestra Arquitectura de Inversión de Dependencias (*Si el código se puede testear aislado sin redes HTTP ni llaves de API externas, entonces es una buena arquitectura desacoplada*).

---

## 3. Arquitectura y Escalabilidad en la Nube (GCP / AWS)

El reto exige que el sistema aúpe niveles críticos de SLAs si el volumen escala drásticamente. Actualmente la solución ya se entrega **Contenerizada (Dockerizada)**; se incluye un `Dockerfile` y un `docker-compose.yml` listos para levantar el API garantizando la inmutabilidad del entorno local hacia producción. Arquitectónicamente la ruta hacia *Cloud Native* sería la siguiente:

### A. Ejecución Serverless con GCP Cloud Run
En lugar de aprovisionar clusters complejos de Kubernetes, el contenedor Docker actual es el candidato perfecto para desplegarse en **Google Cloud Run**. Esto permite escalar a ceros (*scale-to-zero*) para ahorrar costos y escalar instantáneamente a cientos de instancias ante picos de tráfico BPO, cobrando solo por milisegundos de cómputo.

### B. Seguridad, Autenticación y Fetch de Secretos
* **Gestión de Secretos:** Las credenciales de Groq, Gemini y futuras bases de datos NUNCA se exponen en el código fuente. Localmente se inyectan vía variables de entorno (`.env`), mientras que en producción se gestionarían de forma cifrada integrando **Google Secret Manager**.
* **Autenticación (Protección de Cuotas AI):** Dado que el BPO consumirá directamente el endpoint `/api/v1/solicitudes`, es vital prevenir que agentes externos agoten la cuota del LLM. En futuras iteraciones, el endpoint de FastAPI se protegerá implementando un middleware con **API Keys o validación JWT (OAuth2)**.

### B. Desacoplamiento de la Petición y Asincronismo de Colas (Pub/Sub ó SQS)
Actualmente, el Endpoint `/solicitudes` mantiene secuestrado el túnel HTTP durante los 6-9 segundos que le toma a los 4 round-trips de los LLMs. Si llegan 50,000 requests de golpe de 10 BPOs, los Web Workers de Gunicorn/Uvicorn agotarían sus hilos lógicos en espera pasiva (Wait states).
* **Acción sugerida:** Implementar un patrón **Queue-Based Load Leveling** con Amazon SQS o RabbitMQ (Celery). 
  1. El cliente hace POST, el API empuja el Payload JSON al Queue de AWS SQS, y en 0.05 milisegundos devuelve una respuesta vacía al BPO: `HTTP 202 Accepted (Case en proceso)`.
  2. Del otro lado, *Worker Nodes* flotantes se levantan escuchando el SQS, hacen las llamadas lentas al LLM aplicando la cadena de responsabilidad, y cuando terminan, disparan un `Webhook` de regreso al endpoint del BPO para entregarle su dictamen.

### C. Almacenamiento YAML de Configuraciones por un Service Catalog
El archivo estático `tenants_config.yaml` se carga en la memoria del ciclo de vida del FastApi (Lifespan handler). Modificar una empresa obliga a bajar y subir el microservicio.
* **Acción sugerida:** Pasar el diccionario a bases de datos Documentales NoSQL asíncronas (como AWS DynamoDB o MongoDB), implementando el Patrón *Singleton Config Watcher* que actualice los pesos de las matrices en tiempo real, lo que permitirá crear una UI (Frontend) donde administradores de operaciones del BPO suban nuevos clientes arrastrando componentes con el mouse sin tocar código backend.
