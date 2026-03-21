"""
Configuración centralizada de la aplicación usando Pydantic Settings.

Lee las variables de entorno desde un archivo .env ubicado en el
directorio raíz del backend.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación con validación automática."""

    # --- Proveedores de IA ---
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # --- Feature Flags ---
    SIMULAR_FALLOS_BPO: bool = False

    # --- Servidor ---
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración cacheado."""
    return Settings()
