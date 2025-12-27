"""
PDF Service - Orquestación del procesamiento de PDFs.

Equivalente a pdfService.ts
"""

import asyncio
import logging
import re
import time
from collections.abc import Callable
from typing import Any

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
from ..models import PDFFormat
from ..utils.pdf_utils import detectar_formato, extract_text_from_pdf

logger = logging.getLogger(__name__)


async def procesar_pdf(
    file_bytes: bytes,
    file_name: str,
    pdf_format: PDFFormat | None = None,
    return_regex: bool = False,
) -> dict[str, Any]:
    """
    Procesa un archivo PDF para extraer y validar los datos.

    Equivalente a procesarPDF() en pdfUtils.ts

    Args:
        file_bytes: Contenido del archivo PDF
        file_name: Nombre del archivo
        pdf_format: Formato esperado (opcional)
        return_regex: Si True, retorna las regex usadas (solo para PERMISO_CIRCULACION)

    Returns:
        Diccionario con datos extraídos, título y regexes (si aplica)

    Raises:
        ValueError: Si el formato no coincide o hay errores de extracción/validación
    """
    # 1. Extraer texto del PDF
    all_text = extract_text_from_pdf(file_bytes)

    # 2. Detectar el formato real del PDF
    formato_detectado = detectar_formato(all_text)

    # Si se especifica un formato esperado y no coincide, lanzar error
    if pdf_format and formato_detectado != pdf_format:
        formato_nombre = formato_detectado.value if formato_detectado else "Formato Desconocido"
        raise ValueError(
            f"El archivo {file_name} no corresponde al formato esperado ({pdf_format.value}). "
            f"Se detectó que pertenece a: {formato_nombre}."
        )

    # 3. Extraer datos y aplicar validaciones según el formato detectado
    datos: dict[str, str] = {}
    titulo: str | None = None
    regexes: dict[str, str] | None = None

    if formato_detectado == PDFFormat.CERTIFICADO_DE_HOMOLOGACION:
        datos = extraer_datos_homologacion(all_text)
        best_effort_validation_homologacion(datos, file_name)
        # Extraer título del certificado
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
        raise ValueError(f"El archivo {file_name} no pudo ser identificado como un formato válido.")

    return {
        "datos": datos,
        "titulo": titulo,
        "regexes": regexes,
    }


async def process_pdf_files(
    files: list[tuple[str, bytes]],
    pdf_format: PDFFormat | None,
    return_regex: bool,
    on_event: Callable[[dict[str, object]], None],
    concurrency: int = 15,
) -> list[dict[str, Any]]:
    """
    Procesa un arreglo de archivos PDF con concurrencia controlada.

    Equivalente a processPDFFiles() en pdfService.ts

    Args:
        files: Lista de tuplas (nombre, bytes) de archivos PDF
        pdf_format: Formato esperado (opcional)
        return_regex: Si True, retorna las regex usadas
        on_event: Callback para emitir eventos de progreso
        concurrency: Límite de concurrencia

    Returns:
        Lista de resultados (fulfilled o rejected)
    """
    semaphore = asyncio.Semaphore(concurrency)
    total_files = len(files)
    processed_count = 0
    successes_count = 0
    failures_count = 0
    start_time = time.time()
    results: list[dict[str, Any]] = []
    lock = asyncio.Lock()

    async def process_single(file_name: str, file_bytes: bytes) -> dict[str, Any]:
        nonlocal processed_count, successes_count, failures_count

        async with semaphore:
            try:
                result = await procesar_pdf(file_bytes, file_name, pdf_format, return_regex)

                async with lock:
                    processed_count += 1
                    successes_count += 1
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    avg_time_per_file = elapsed_ms / processed_count
                    remaining = total_files - processed_count
                    estimated_ms_left = int(avg_time_per_file * remaining)

                    on_event({
                        "progress": processed_count,
                        "total": total_files,
                        "file": file_name,
                        "status": "fulfilled",
                        "estimatedMsLeft": estimated_ms_left,
                        "elapsedMsSoFar": elapsed_ms,
                        "successes": successes_count,
                        "failures": failures_count,
                    })

                return {
                    "status": "fulfilled",
                    "value": {
                        "fileName": file_name,
                        **result,
                    },
                }

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error procesando {file_name}: {error_msg}")

                # Resaltar el formato detectado (como en TypeScript)
                if "Se detectó que pertenece a:" in error_msg:
                    error_msg = re.sub(
                        r"Se detectó que pertenece a:\s*(.*)",
                        r'<span style="background-color: yellow; font-weight: bold;">Se detectó que pertenece a: \1</span>',
                        error_msg,
                    )

                async with lock:
                    processed_count += 1
                    failures_count += 1
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    avg_time_per_file = elapsed_ms / processed_count
                    remaining = total_files - processed_count
                    estimated_ms_left = int(avg_time_per_file * remaining)

                    on_event({
                        "progress": processed_count,
                        "total": total_files,
                        "file": file_name,
                        "status": "rejected",
                        "error": error_msg,
                        "estimatedMsLeft": estimated_ms_left,
                        "elapsedMsSoFar": elapsed_ms,
                        "successes": successes_count,
                        "failures": failures_count,
                    })

                return {
                    "status": "rejected",
                    "reason": {
                        "fileName": file_name,
                        "error": error_msg,
                    },
                }

    # Procesar en batches para evitar bloquear el event loop
    batch_size = 100
    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        tasks = [process_single(name, data) for name, data in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

        # Ceder control al event loop
        await asyncio.sleep(0)

    return results
