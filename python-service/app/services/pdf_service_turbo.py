"""
PDF Service TURBO - Procesamiento ultra-rápido con multiprocessing.

Meta: 1000 PDFs en < 2 segundos usando ProcessPoolExecutor.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing import cpu_count
from typing import Any

from ..models import PDFFormat

logger = logging.getLogger(__name__)

# Pool global para reutilizar workers (variable mutable, no constante)
_process_pool: ProcessPoolExecutor | None = None
_MAX_WORKERS: int = min(cpu_count(), 16)  # Máximo 16 workers


def get_process_pool() -> ProcessPoolExecutor:
    """Obtiene o crea el pool de procesos global."""
    global _process_pool
    if _process_pool is None:
        _process_pool = ProcessPoolExecutor(max_workers=_MAX_WORKERS)
    return _process_pool


def shutdown_process_pool() -> None:
    """Cierra el pool de procesos global."""
    global _process_pool
    if _process_pool is not None:
        _process_pool.shutdown(wait=False)
        _process_pool = None


def _extract_text_sync(file_bytes: bytes) -> str:
    """Extrae texto de PDF de forma síncrona (para multiprocessing)."""
    import fitz

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts: list[str] = []

    for page in doc:
        page_text = page.get_text("text")
        if page_text and isinstance(page_text, str):
            text_parts.append(page_text)

    doc.close()
    return " ".join(text_parts)


def _detectar_formato_sync(texto: str) -> PDFFormat | None:
    """Detecta el formato del PDF de forma síncrona."""
    upper_text = texto.upper()

    if "CERTIFICADO DE HOMOLOGACIÓN" in upper_text:
        return PDFFormat.CERTIFICADO_DE_HOMOLOGACION
    if "CERTIFICADO DE REVISIÓN TÉCNICA" in upper_text or "FECHA REVISIÓN" in upper_text:
        return PDFFormat.CRT
    if "SEGURO OBLIGATORIO" in upper_text or "SOAP" in upper_text:
        return PDFFormat.SOAP
    if "PERMISO DE CIRCULACIÓN" in upper_text or "PLACA ÚNICA" in upper_text:
        return PDFFormat.PERMISO_CIRCULACION
    return None


def _process_single_pdf_sync(
    file_data: tuple[str, bytes],
    pdf_format: PDFFormat | None = None,
    return_regex: bool = False,
) -> dict[str, Any]:
    """
    Procesa un PDF de forma completamente síncrona (para ProcessPoolExecutor).

    Esta función se ejecuta en un proceso separado, por lo que todas las
    importaciones deben ser locales para evitar problemas de serialización.
    """
    # Importaciones locales para evitar problemas de pickle
    from ..extractors import (
        best_effort_validation_crt,
        best_effort_validation_homologacion,
        best_effort_validation_permiso_circulacion,
        best_effort_validation_soap,
        extraer_datos_crt,
        extraer_datos_homologacion,
        extraer_datos_permiso_circulacion,
        extraer_datos_soap_simplificado,
    )

    file_name, file_bytes = file_data

    try:
        # 1. Extraer texto
        all_text = _extract_text_sync(file_bytes)

        if not all_text.strip():
            raise ValueError("El PDF no contiene texto extraíble")

        # 2. Detectar formato
        formato_detectado = _detectar_formato_sync(all_text)

        # 3. Validar formato si se especificó
        if pdf_format and formato_detectado != pdf_format:
            formato_nombre = formato_detectado.value if formato_detectado else "Formato Desconocido"
            raise ValueError(
                f"El archivo {file_name} no corresponde al formato esperado ({pdf_format.value}). "
                f"Se detectó que pertenece a: {formato_nombre}."
            )

        # 4. Extraer datos según formato
        datos: dict[str, str] = {}
        titulo: str | None = None
        regexes: dict[str, str] | None = None

        if formato_detectado == PDFFormat.CERTIFICADO_DE_HOMOLOGACION:
            datos = extraer_datos_homologacion(all_text)
            best_effort_validation_homologacion(datos, file_name)
            titulo_match = re.search(
                r"CERTIFICADO DE HOMOLOGACIÓN\s+(.*?)\s+REEMPLAZA", all_text, re.IGNORECASE
            )
            titulo = titulo_match.group(1).strip() if titulo_match else None

        elif formato_detectado == PDFFormat.CRT:
            datos = extraer_datos_crt(all_text)
            best_effort_validation_crt(datos, file_name)

        elif formato_detectado == PDFFormat.SOAP:
            datos = extraer_datos_soap_simplificado(all_text)
            best_effort_validation_soap(datos, file_name)

        elif formato_detectado == PDFFormat.PERMISO_CIRCULACION:
            result = extraer_datos_permiso_circulacion(all_text, return_regex)
            datos = result["data"]
            regexes = result.get("regexes") if return_regex else None
            best_effort_validation_permiso_circulacion(datos, file_name)

        else:
            raise ValueError(
                f"El archivo {file_name} no pudo ser identificado como un formato válido."
            )

        return {
            "status": "fulfilled",
            "value": {
                "fileName": file_name,
                "datos": datos,
                "titulo": titulo,
                "regexes": regexes,
            },
        }

    except Exception as e:
        error_msg = str(e)

        # Resaltar formato detectado
        if "Se detectó que pertenece a:" in error_msg:
            error_msg = re.sub(
                r"Se detectó que pertenece a:\s*(.*)",
                r'<span style="background-color: yellow; font-weight: bold;">Se detectó que pertenece a: \1</span>',
                error_msg,
            )

        return {
            "status": "rejected",
            "reason": {
                "fileName": file_name,
                "error": error_msg,
            },
        }


async def process_pdf_files_turbo(
    files: list[tuple[str, bytes]],
    pdf_format: PDFFormat | None,
    return_regex: bool,
    on_event: Callable[[dict[str, object]], None],
    batch_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Procesa PDFs usando ProcessPoolExecutor para máximo rendimiento.

    Esta versión es ~5x más rápida que la versión asyncio para grandes volúmenes.

    Args:
        files: Lista de tuplas (nombre, bytes)
        pdf_format: Formato esperado (opcional)
        return_regex: Si True, retorna regex usadas
        on_event: Callback para eventos de progreso
        batch_size: Tamaño del batch para emitir eventos (default: 50)

    Returns:
        Lista de resultados
    """
    total_files = len(files)
    if total_files == 0:
        return []

    start_time = time.time()
    results: list[dict[str, Any]] = []
    successes_count = 0
    failures_count = 0

    # Usar ProcessPoolExecutor para procesamiento paralelo real
    loop = asyncio.get_event_loop()
    pool = get_process_pool()

    # Crear función parcial con parámetros fijos
    process_fn = partial(
        _process_single_pdf_sync,
        pdf_format=pdf_format,
        return_regex=return_regex,
    )

    # Procesar en batches para emitir eventos de progreso
    for batch_start in range(0, total_files, batch_size):
        batch_end = min(batch_start + batch_size, total_files)
        batch = files[batch_start:batch_end]

        # Ejecutar batch en paralelo
        futures = [loop.run_in_executor(pool, process_fn, file_data) for file_data in batch]
        batch_results = await asyncio.gather(*futures)

        # Procesar resultados del batch
        for i, result in enumerate(batch_results):
            _file_name = batch[i][0]  # Prefijo _ para indicar variable intencionalmente no usada
            results.append(result)

            if result["status"] == "fulfilled":
                successes_count += 1
            else:
                failures_count += 1

        # Emitir evento de progreso por batch (no por archivo individual)
        processed_count = batch_end
        elapsed_ms = int((time.time() - start_time) * 1000)
        avg_time_per_file = elapsed_ms / processed_count if processed_count > 0 else 0
        remaining = total_files - processed_count
        estimated_ms_left = int(avg_time_per_file * remaining)

        on_event({
            "progress": processed_count,
            "total": total_files,
            "file": f"Batch {batch_start // batch_size + 1} completado",
            "status": "batch_complete",
            "estimatedMsLeft": estimated_ms_left,
            "elapsedMsSoFar": elapsed_ms,
            "successes": successes_count,
            "failures": failures_count,
        })

        # Ceder control al event loop
        await asyncio.sleep(0)

    return results


async def process_pdf_files_hybrid(
    files: list[tuple[str, bytes]],
    pdf_format: PDFFormat | None,
    return_regex: bool,
    on_event: Callable[[dict[str, object]], None],
    turbo_threshold: int = 100,
) -> list[dict[str, Any]]:
    """
    Versión híbrida que usa turbo para grandes volúmenes y asyncio para pequeños.

    Args:
        files: Lista de archivos
        pdf_format: Formato esperado
        return_regex: Si retornar regex
        on_event: Callback de eventos
        turbo_threshold: Umbral para activar modo turbo (default: 100 archivos)

    Returns:
        Lista de resultados
    """
    from .pdf_service import process_pdf_files

    if len(files) >= turbo_threshold:
        logger.info(f"Usando modo TURBO para {len(files)} archivos ({_MAX_WORKERS} workers)")
        return await process_pdf_files_turbo(files, pdf_format, return_regex, on_event)
    else:
        logger.info(f"Usando modo asyncio para {len(files)} archivos")
        return await process_pdf_files(files, pdf_format, return_regex, on_event)
