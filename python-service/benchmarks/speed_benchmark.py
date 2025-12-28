"""
Benchmark de velocidad para procesamiento de PDFs.

Objetivo: Medir cuánto tarda procesar 1000 PDFs y optimizar para <2 segundos.
"""

import asyncio
import multiprocessing as mp

# Agregar el path del proyecto
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF

from app.extractors.crt_extractor import extraer_datos_crt
from app.extractors.homologacion_extractor import extraer_datos_homologacion
from app.extractors.permiso_circulacion_extractor import extraer_datos_permiso_circulacion
from app.extractors.soap_extractor import extraer_datos_soap_simplificado
from app.models import PDFFormat
from app.utils.pdf_utils import detectar_formato, extract_text_from_pdf

# ============================================================================
# FUNCIONES DE PROCESAMIENTO SÍNCRONAS (para ProcessPoolExecutor)
# ============================================================================


def process_single_pdf_sync(
    file_bytes: bytes, file_name: str, pdf_format: PDFFormat | None = None
) -> dict[str, Any]:
    """
    Procesa un PDF de forma síncrona (para uso en multiprocessing).
    Versión optimizada sin overhead de async.
    """
    # Extraer texto
    all_text = extract_text_from_pdf(file_bytes)

    # Detectar formato
    formato_detectado = detectar_formato(all_text)

    if pdf_format and formato_detectado != pdf_format:
        raise ValueError(
            f"Formato incorrecto: esperado {pdf_format.value}, detectado {formato_detectado}"
        )

    # Extraer datos según formato
    if formato_detectado == PDFFormat.CRT:
        datos = extraer_datos_crt(all_text)
    elif formato_detectado == PDFFormat.SOAP:
        datos = extraer_datos_soap_simplificado(all_text)
    elif formato_detectado == PDFFormat.CERTIFICADO_DE_HOMOLOGACION:
        datos = extraer_datos_homologacion(all_text)
    elif formato_detectado == PDFFormat.PERMISO_CIRCULACION:
        result = extraer_datos_permiso_circulacion(all_text, False)
        datos = result["data"]
    else:
        raise ValueError(f"Formato no reconocido para {file_name}")

    return {"fileName": file_name, "datos": datos}


def process_batch_sync(
    batch: list[tuple[str, bytes]], pdf_format: PDFFormat | None = None
) -> list[dict[str, Any]]:
    """
    Procesa un batch de PDFs de forma síncrona.
    Diseñado para ejecutarse en un proceso separado.
    """
    results: list[dict[str, Any]] = []
    for file_name, file_bytes in batch:
        try:
            result = process_single_pdf_sync(file_bytes, file_name, pdf_format)
            results.append({"status": "fulfilled", "value": result})
        except Exception as e:
            results.append({
                "status": "rejected",
                "reason": {"fileName": file_name, "error": str(e)},
            })
    return results


# ============================================================================
# BENCHMARKS
# ============================================================================


def create_mock_pdf() -> bytes:
    """Crea un PDF de prueba mínimo con texto CRT."""
    doc: fitz.Document = fitz.open()
    page: fitz.Page = doc.new_page()

    # Texto mínimo que simula un CRT
    text = """
    CERTIFICADO DE REVISIÓN TÉCNICA

    FECHA REVISIÓN: 15-01-2025
    VÁLIDO HASTA: 15-01-2026
    PLACA PATENTE: ABCD12
    N° FOLIO: 123456789
    PLANTA: SOCOVESA
    VIN: 1HGBH41JXMN109186
    MARCA: TOYOTA
    MODELO: COROLLA
    AÑO: 2020
    COLOR: BLANCO
    TIPO VEHÍCULO: AUTOMÓVIL
    """

    # Insertar texto en la página
    page.insert_text((50, 100), text, fontsize=10)

    # Convertir a bytes
    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes


def benchmark_sequential(pdfs: list[tuple[str, bytes]], label: str = "Sequential") -> float:
    """Benchmark: procesamiento secuencial (baseline)."""
    start = time.perf_counter()

    results: list[dict[str, Any]] = []
    for name, data in pdfs:
        try:
            result = process_single_pdf_sync(data, name, None)
            results.append(result)
        except Exception:
            pass

    elapsed = time.perf_counter() - start
    print(f"[{label}] {len(pdfs)} PDFs en {elapsed:.3f}s ({elapsed * 1000 / len(pdfs):.2f}ms/PDF)")
    return elapsed


def benchmark_multiprocessing(
    pdfs: list[tuple[str, bytes]], max_workers: int | None = None, label: str = "Multiprocessing"
) -> float:
    """Benchmark: ProcessPoolExecutor con paralelismo real."""
    max_workers = max_workers or mp.cpu_count()
    chunk_size = max(1, len(pdfs) // max_workers)

    # Dividir en chunks
    chunks: list[list[tuple[str, bytes]]] = []
    for i in range(0, len(pdfs), chunk_size):
        chunks.append(pdfs[i : i + chunk_size])

    start = time.perf_counter()

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch_sync, chunk, None) for chunk in chunks]

        for future in as_completed(futures):
            batch_results = future.result()
            results.extend(batch_results)

    elapsed = time.perf_counter() - start
    print(
        f"[{label}] {len(pdfs)} PDFs en {elapsed:.3f}s ({elapsed * 1000 / len(pdfs):.2f}ms/PDF) - {max_workers} workers"
    )
    return elapsed


async def benchmark_asyncio(
    pdfs: list[tuple[str, bytes]], concurrency: int = 100, label: str = "Asyncio"
) -> float:
    """Benchmark: asyncio con semaphore (método actual)."""
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(name: str, data: bytes) -> dict[str, Any]:
        async with semaphore:
            # Simular async (aunque PyMuPDF es sync)
            return process_single_pdf_sync(data, name, None)

    start = time.perf_counter()

    tasks = [process_one(name, data) for name, data in pdfs]
    _ = await asyncio.gather(*tasks, return_exceptions=True)  # Resultados no usados directamente

    elapsed = time.perf_counter() - start
    print(f"[{label}] {len(pdfs)} PDFs en {elapsed:.3f}s ({elapsed * 1000 / len(pdfs):.2f}ms/PDF)")
    return elapsed


def run_benchmarks():
    """Ejecuta todos los benchmarks."""
    print("=" * 70)
    print("BENCHMARK DE VELOCIDAD DE PROCESAMIENTO DE PDFs")
    print("=" * 70)
    print(f"CPU cores disponibles: {mp.cpu_count()}")
    print()

    # Crear PDFs de prueba
    print("Creando PDFs de prueba...")
    mock_pdf = create_mock_pdf()
    print(f"Tamaño PDF mock: {len(mock_pdf)} bytes")

    # Tests con diferentes cantidades
    for num_pdfs in [100, 500, 1000]:
        print(f"\n{'=' * 70}")
        print(f"TEST: {num_pdfs} PDFs")
        print("=" * 70)

        pdfs = [(f"test_{i}.pdf", mock_pdf) for i in range(num_pdfs)]

        # 1. Baseline secuencial (solo para 100)
        if num_pdfs <= 100:
            benchmark_sequential(pdfs, "Sequential (baseline)")

        # 2. Asyncio (método actual)
        asyncio.run(benchmark_asyncio(pdfs, concurrency=100, label="Asyncio (actual)"))

        # 3. Multiprocessing con diferentes workers
        for workers in [4, 8, mp.cpu_count()]:
            if workers <= mp.cpu_count():
                benchmark_multiprocessing(
                    pdfs, max_workers=workers, label=f"ProcessPool ({workers}w)"
                )

    print("\n" + "=" * 70)
    print("CONCLUSIÓN")
    print("=" * 70)
    print("El método más rápido debería ser ProcessPoolExecutor con todos los cores.")
    print("Para 1000 PDFs en <2s necesitamos ~2ms/PDF.")


if __name__ == "__main__":
    run_benchmarks()
