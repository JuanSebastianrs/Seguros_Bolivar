# 🧠 Microservicio IA BPO - Seguros Bolívar

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-e92063.svg)
![Pytest](https://img.shields.io/badge/Pytest-100%25-brightgreen.svg)

Microservicio basado en Inteligencia Artificial para automatizar el procesamiento de 
solicitudes de Peticiones, Quejas y Reclamos (PQR) en una empresa BPO (Business 
Process Outsourcing).

Diseñado bajo los principios de **Arquitectura Hexagonal (Puertos y Adaptadores)** y 
arquitectura Clean, implementando **Strategy Pattern** para configuración multi-cliente, 
**Chain of Responsibility** para el flujo de procesamiento, y **Fallback** para 
resiliencia en llamadas al LLM.

---

## 🚀 Características Principales

*   **Multitenant Data-Driven:** Orquestación de reglas de cliente (entidades, categorías y matrices de enrutamiento) a nivel de metadatos (YAML). Respeta 100% el principio **Open/Closed (SOLID)**. Nuevos clientes se suman sin tocar código.
*   **Pipeline con IA (Chain of Responsibility):** Flujo de 6 pasos (Validar → Clasificar → Priorizar → Justificar → Enrutar → Gestión Externa) coordinado de manera asíncrona.
*   **Resiliencia LLM (Fallback):** Integración nativa asíncrona con **Groq (llama-3.3-70b-versatile)** como IA principal y **Google Gemini (gemini-2.5-flash)** como IA de respaldo automático.
*   **Bono Mensajería del Valle (+6):** Implementación del Patrón Strategy para soportar la priorización vía servicio externo (Mocks) exclusivo para este cliente.
*   **Bono de Duplicados (+4):** Cache en memoria para descartar peticiones idempotentes ya procesadas (`HTTP 409 Conflict`).
*   **Bono Resiliencia BPO (+4):** Adaptador de plataforma cliente externo con control de fallos emulados vía Feature Flag (`SIMULAR_FALLOS_BPO`).

---

## 🏗 Arquitectura del Proyecto

```text
backend/
├── app/
│   ├── adapters/     # Hexágono Externo (Driven Adapters: Groq, Gemini, BPO Externas)
│   ├── api/          # Hexágono Externo (Driving Adapters: FastAPI Routers, Schemas Pydantic)
│   ├── core/         # Configuraciones, excepciones, manejo de estado (Cache)
│   ├── domain/       # Hexágono Interno (Entidades, Puertos/Interfaces, Prompts IA)
│   ├── pipeline/     # Orquestador del flujo BPO (Chain of Responsibility)
│   └── strategies/   # Lógica multi-cliente (Patrón Strategy + YAML data loader)
├── data/
│   └── tenants_config.yaml  # Base de datos YAML de configuración por compañía
├── tests/            # Suite profunda de pruebas unitarias/integración
├── Dockerfile        # Contenedor para despliegue aislado
├── requirements.txt  # Dependencias ancladas
└── .env.example      # Plantilla de variables de entorno
```

---

## 🛠 Instalación y Ejecución (Local y Docker)

### Pre-requisitos
* Python 3.11+
* Docker & Docker Compose (Opcional)
* API Keys válidas (Groq es obligatoria, Gemini es manejada por gcloud ADC local si se deja vacía).

### 1. Variables de Entorno

Copiar el archivo de entorno y rellenar las credenciales:

```bash
cd backend
cp .env.example .env
```
Edite `.env`:
```env
# ============================================================
# Variables de entorno para el Microservicio BPO IA
# Copie este archivo como .env y reemplace los valores
# ============================================================

# --- Proveedores de IA ---
GROQ_API_KEY=gsk_************************
GEMINI_API_KEY=  # Dejar vacío si se usa autenticación por SDK de Google

# --- Feature Flags ---
SIMULAR_FALLOS_BPO=false

# --- Servidor ---
APP_ENV=development
LOG_LEVEL=INFO
```

### 2. Forma A: Ejecución Directa (Virtual Environment)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Forma B: Ejecución vía Docker Compose
Desde la raíz del repositorio:
```bash
docker-compose up --build
```

Una vez que los contenedores estén en ejecución, puedes acceder a los siguientes enlaces de manera local:

**Frontend (Vite + React):**
* **Aplicación Web:** [http://localhost:5173](http://localhost:5173)

**Backend (FastAPI):**
* **API Base:** [http://localhost:8000](http://localhost:8000)
* **Documentación Swagger (OpenAPI) / Prueba de Endpoints:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Documentación ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Pruebas Unitarias y de Integración (Pytest)

Se diseñó una robusta suite de **24 pruebas asíncronas** que garantiza la cobertura de los requerimientos y los **bonos extra** exigidos. ¡Los tests **no realizan llamadas HTTP reales**! 

```bash
cd backend
python -m pytest tests/ -v
```

**Cubre:**
* Pipeline Happy Path & Early Exit por falta de Info.
* Mocks transaccionales en API Rest (TestClient).
* Excepciones esperadas 400 (Empresa Inexistente) & 409 (Idempotencia).
* LLM Fallback (Groq -> Gemini).
* Factory Routing de Mensajería del Mocks.

---

## 📖 Uso del Endpoint `/api/v1/solicitudes`

**URL Local:** `http://localhost:8000/api/v1/solicitudes` \
**Swagger UI:** `http://localhost:8000/docs`

**Ejemplo de Petición cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/solicitudes \
  -H "Content-Type: application/json" \
  -d '{
    "compania": "GASES DEL ORINOCO",
    "solicitud_id": "REQ-001",
    "solicitud_descripcion": "Mi nombre es Juana y mi numero de cédula es 102045678. Solicito una revision urgente porque la estufa que compre hace 2 semanas presenta fallas."
  }'
```

---

## 📄 Documentación Técnica

La memoria técnica completa del proyecto, incluyendo el análisis del caso de estudio, decisiones de arquitectura y justificación de patrones, se encuentra disponible en:

📎 [`docs/src/Seguros_bolivar.pdf`](docs/src/Seguros_bolivar.pdf)

---

*Desarrollado para el Caso de Estudio IA [Profesional Senior] de Seguros Bolívar.*  
**Por: Juan Sebastian Rodríguez Salazar**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/juan-sebastian-rs/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/JuanSebastianrs)
