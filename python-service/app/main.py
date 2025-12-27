"""
PDF Processor Service - API Principal.

FastAPI application con endpoint /convert y SSE streaming.
"""

import base64
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.formparsers import MultiPartParser
from starlette.requests import Request

from .config import settings
from .models import ConversionFailure, ExcelStats, HealthResponse, PDFFormat
from .services.excel_service import generate_excel_from_results
from .services.pdf_service import process_pdf_files
from .utils.logger import logger, setup_logging
from .utils.text_utils import safe_filename

# ============================================================================
# PARCHE CRÍTICO: Aumentar límite de archivos en Starlette (default es 1000)
# Starlette tiene el límite en __kwdefaults__ (keyword-only arguments)
# ============================================================================
MAX_UPLOAD_FILES = 15000

# Parchear MultiPartParser.__init__ keyword defaults
if hasattr(MultiPartParser.__init__, "__kwdefaults__") and MultiPartParser.__init__.__kwdefaults__:
    MultiPartParser.__init__.__kwdefaults__["max_files"] = MAX_UPLOAD_FILES

# Parchear Request._get_form keyword defaults
if hasattr(Request._get_form, "__kwdefaults__") and Request._get_form.__kwdefaults__:
    Request._get_form.__kwdefaults__["max_files"] = MAX_UPLOAD_FILES

# Parchear Request.form keyword defaults
if hasattr(Request.form, "__kwdefaults__") and Request.form.__kwdefaults__:
    Request.form.__kwdefaults__["max_files"] = MAX_UPLOAD_FILES

# Métricas globales (usando nombres en minúsculas para poder mutarlas)
start_time = time.time()
processed_total = 0
errors_total = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle del servidor."""
    setup_logging()
    logger.info("Iniciando PDF Processor Service v%s", settings.VERSION)
    yield
    logger.info("Deteniendo PDF Processor Service")


app = FastAPI(
    title="PDF Processor Service",
    description="Servicio de procesamiento de PDFs chilenos (CRT, SOAP, Homologación, Permiso)",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        uptime_seconds=time.time() - start_time,
        processed_total=processed_total,
        errors_total=errors_total,
    )


@app.post("/convert")
async def convert_pdfs(
    pdf: list[UploadFile] = File(..., description="Archivos PDF a procesar"),
    pdf_format_str: str | None = Form(None, alias="pdfFormat", description="Formato esperado"),
    return_regex: bool = Form(False, alias="returnRegex", description="Retornar regex usadas"),
    concurrency: int | None = Form(None, description="Concurrencia máxima"),
):
    """
    Procesa uno o más archivos PDF y retorna un Excel consolidado.

    Respuesta: Server-Sent Events (SSE) con progreso y resultado final.
    """
    global PROCESSED_TOTAL, ERRORS_TOTAL

    # Log de entrada
    logger.info(
        f"Recibidos {len(pdf)} archivos, formato={pdf_format_str}, concurrency={concurrency}"
    )

    # Usar concurrencia por defecto si no se especifica
    if concurrency is None:
        concurrency = settings.DEFAULT_CONCURRENCY

    # Validaciones
    if not pdf:
        raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo PDF")

    if len(pdf) > settings.MAX_FILES:
        raise HTTPException(
            status_code=400, detail=f"Se excede el límite de archivos ({settings.MAX_FILES})"
        )

    # Validar formato si se proporciona
    pdf_format: PDFFormat | None = None
    if pdf_format_str:
        try:
            pdf_format = PDFFormat(pdf_format_str)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Formato no válido: {pdf_format_str}. Valores permitidos: {[f.value for f in PDFFormat]}",
            ) from exc

    # Ajustar return_regex según formato
    should_return_regex = return_regex and pdf_format_str == "PERMISO_CIRCULACION"

    # Limitar concurrencia
    concurrency = min(concurrency, settings.MAX_CONCURRENCY)

    # Leer archivos en memoria
    files_data: list[tuple[str, bytes]] = []
    for f in pdf:
        if f.size and f.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo {f.filename} excede el tamaño máximo ({settings.MAX_FILE_SIZE_MB}MB)",
            )

        content = await f.read()
        safe_name = safe_filename(f.filename or "unnamed.pdf")
        files_data.append((safe_name, content))

    async def event_generator():
        """Generador de eventos SSE."""
        global processed_total, errors_total

        events_queue: list[dict[str, object]] = []

        def on_event(event: dict[str, object]) -> None:
            events_queue.append(event)

        # Procesar PDFs
        results = await process_pdf_files(
            files_data,
            pdf_format,
            should_return_regex,
            on_event,
            concurrency,
        )

        # Emitir eventos de progreso
        for event in events_queue:
            yield f"data: {json.dumps(event)}\n\n"

        # Separar éxitos y fallos
        successes = [r for r in results if r["status"] == "fulfilled"]
        failures = [r for r in results if r["status"] == "rejected"]

        # Actualizar métricas globales
        processed_total += len(results)
        errors_total += len(failures)

        # Mapear fallidos
        fallidos = [
            ConversionFailure(
                fileName=f["reason"]["fileName"],
                error=f["reason"]["error"],
            )
            for f in failures
        ]

        # Generar Excel
        if successes:
            success_values = [s["value"] for s in successes]
            stats = ExcelStats(
                totalProcesados=len(files_data),
                totalExitosos=len(successes),
                totalFallidos=len(failures),
                fallidos=fallidos,
            )
            excel_buffer, file_name = generate_excel_from_results(
                success_values,
                pdf_format or PDFFormat.CRT,  # Default si no se especifica
                stats,
            )
        else:
            # Sin éxitos: generar Excel solo con estadísticas
            stats = ExcelStats(
                totalProcesados=len(files_data),
                totalExitosos=0,
                totalFallidos=len(failures),
                fallidos=fallidos,
            )
            excel_buffer, file_name = generate_excel_from_results(
                [],
                pdf_format or PDFFormat.CRT,
                stats,
            )

        # Evento final
        excel_base64 = base64.b64encode(excel_buffer).decode("utf-8")

        final_event = {
            "final": {
                "totalProcesados": len(files_data),
                "totalExitosos": len(successes),
                "totalFallidos": len(failures),
                "exitosos": [s["value"] for s in successes],
                "fallidos": [{"fileName": f.file_name, "error": f.error} for f in fallidos],
                "excel": excel_base64,
                "fileName": file_name,
            }
        }

        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Para nginx
        },
    )


def run():
    """Punto de entrada para ejecutar el servidor."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.LOG_LEVEL == "DEBUG",
    )


if __name__ == "__main__":
    run()
