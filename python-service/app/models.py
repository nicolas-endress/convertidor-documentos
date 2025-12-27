"""PDF Processor Service - Modelos de datos."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PDFFormat(str, Enum):
    """Formatos de PDF soportados."""

    CERTIFICADO_DE_HOMOLOGACION = "CERTIFICADO_DE_HOMOLOGACION"
    CRT = "CRT"
    SOAP = "SOAP"
    PERMISO_CIRCULACION = "PERMISO_CIRCULACION"


class ProgressEvent(BaseModel):
    """Evento de progreso emitido via SSE."""

    progress: int = Field(..., description="Archivos procesados hasta ahora")
    total: int = Field(..., description="Total de archivos a procesar")
    file: str = Field(..., description="Nombre del archivo actual")
    status: str = Field(..., description="fulfilled o rejected")
    successes: int = Field(..., description="Cantidad de éxitos")
    failures: int = Field(..., description="Cantidad de fallos")
    elapsed_ms_so_far: int = Field(
        ..., alias="elapsedMsSoFar", description="Tiempo transcurrido en ms"
    )
    estimated_ms_left: int = Field(
        ..., alias="estimatedMsLeft", description="Tiempo estimado restante en ms"
    )
    error: str | None = Field(None, description="Mensaje de error si rejected")

    model_config = {"populate_by_name": True}


class ConversionSuccess(BaseModel):
    """Resultado exitoso de conversión."""

    file_name: str = Field(..., alias="fileName")
    datos: dict[str, str]
    titulo: str | None = None
    regexes: dict[str, str] | None = None  # Patrón como string para serialización

    model_config = {"populate_by_name": True}


class ConversionFailure(BaseModel):
    """Resultado fallido de conversión."""

    file_name: str = Field(..., alias="fileName")
    error: str

    model_config = {"populate_by_name": True}


class FinalResult(BaseModel):
    """Resultado final del procesamiento."""

    total_procesados: int = Field(..., alias="totalProcesados")
    total_exitosos: int = Field(..., alias="totalExitosos")
    total_fallidos: int = Field(..., alias="totalFallidos")
    exitosos: list[dict[str, Any]]
    fallidos: list[ConversionFailure]
    excel: str  # Base64 encoded
    file_name: str = Field(..., alias="fileName")

    model_config = {"populate_by_name": True}


class FinalEvent(BaseModel):
    """Evento final emitido via SSE."""

    final: FinalResult


class ExcelStats(BaseModel):
    """Estadísticas para la hoja de Excel."""

    total_procesados: int = Field(..., alias="totalProcesados")
    total_exitosos: int = Field(..., alias="totalExitosos")
    total_fallidos: int = Field(..., alias="totalFallidos")
    fallidos: list[ConversionFailure]

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    """Respuesta del health check."""

    status: str = "ok"
    version: str
    uptime_seconds: float
    processed_total: int = 0
    errors_total: int = 0
