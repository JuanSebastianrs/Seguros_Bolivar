"""
Microservicio BPO IA — Entry Point.

Aplicación FastAPI que automatiza el procesamiento de solicitudes
para una empresa BPO multitenant usando Inteligencia Artificial.

Arquitectura: Hexagonal (Puertos y Adaptadores)
Patrones: Strategy, Chain of Responsibility, Fallback
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import router
from app.core.config import get_settings

# ── Configuración de Logging ──
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── Aplicación FastAPI ──
app = FastAPI(
    title="BPO IA Microservice",
    description=(
        "Microservicio de Inteligencia Artificial para automatizar el "
        "procesamiento de solicitudes en una empresa BPO multitenant. "
        "Implementa validación, clasificación, priorización, justificación, "
        "enrutamiento y gestión externa."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(router)

logger.info(
    f"BPO IA Microservice iniciado. "
    f"Entorno: {settings.APP_ENV} | Log: {settings.LOG_LEVEL}"
)
