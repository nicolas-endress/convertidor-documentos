"""
PDF Processor Service - Configuración centralizada.
"""

import os
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del servicio con valores por defecto y variables de entorno."""

    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1  # Para Windows, usar 1 worker con uvicorn
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Procesamiento
    DEFAULT_CONCURRENCY: int = 15
    MAX_CONCURRENCY: int = 50
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILES: int = 15000  # Aumentado para procesamiento masivo
    FILE_TIMEOUT_SECONDS: int = 30
    REQUEST_TIMEOUT_SECONDS: int = 1800  # 30 minutos para procesamiento masivo

    # Archivos temporales
    TEMP_DIR: str = os.path.join(os.environ.get("TEMP", "/tmp"), "pdf-processor")
    TEMP_FILE_TTL_HOURS: int = 1

    # Seguridad
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf"]
    MAX_FILENAME_LENGTH: int = 255

    # Versión
    VERSION: str = "1.0.0"

    class Config:
        env_prefix = "PDF_PROCESSOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instancia global de configuración
settings = Settings()
