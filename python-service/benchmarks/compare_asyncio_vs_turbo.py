"""
Benchmark COMPARATIVO: ASYNCIO vs TURBO.

Compara las dos implementaciones de procesamiento de PDFs:
1. ASYNCIO - Implementación actual con asyncio.Semaphore
2. TURBO - Nueva implementación con ProcessPoolExecutor

Meta: 1000 PDFs en < 2 segundos
"""

import asyncio
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF

from app.models import PDFFormat
from app.services.pdf_service import process_pdf_files
from app.services.pdf_service_turbo import process_pdf_files_turbo


def crear_pdf_crt_valido(index: int) -> bytes:
    """Crea un PDF CRT con datos que PASAN la validación."""
    doc: fitz.Document = fitz.open()
    page: fitz.Page = doc.new_page()

    # Texto que simula un CRT real - DEBE coincidir con las regex del extractor
    # Ver crt_extractor.py para los patrones exactos
    mes_nombres = [
        "ENERO",
        "FEBRERO",
        "MARZO",
        "ABRIL",
        "MAYO",
        "JUNIO",
        "JULIO",
        "AGOSTO",
        "SEPTIEMBRE",
        "OCTUBRE",
        "NOVIEMBRE",
        "DICIEMBRE",
    ]
    mes = mes_nombres[index % 12]
    dia = (index % 28) + 1

    texto = f"""
    CERTIFICADO DE REVISIÓN TÉCNICA

    PLANTA: PRT-{(index % 99) + 1:03d}

    FECHA REVISIÓN: {dia} {mes} 2024

    PLACA PATENTE AB{index:04d}

    N°B{100000 + index}

    VÁLIDO HASTA {mes} 2025

    VIN: 9BW{index:010d}1234567

    Resultado: APROBADO
    """

    page.insert_text((72, 100), texto, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


async def benchmark_asyncio(
    pdf_files: list[tuple[str, bytes]],
) -> tuple[list[dict[str, object]], float, int]:
    """Benchmark de la versión asyncio (actual)."""
    sse_events: list[dict[str, object]] = []

    def on_event(event: dict[str, object]) -> None:
        sse_events.append(event)

    start = time.perf_counter()
    results = await process_pdf_files(
        files=pdf_files,
        pdf_format=PDFFormat.CRT,
        return_regex=False,
        on_event=on_event,
        concurrency=100,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    return results, elapsed_ms, len(sse_events)


async def benchmark_turbo(
    pdf_files: list[tuple[str, bytes]],
) -> tuple[list[dict[str, object]], float, int]:
    """Benchmark de la versión TURBO (ProcessPoolExecutor)."""
    sse_events: list[dict[str, object]] = []

    def on_event(event: dict[str, object]) -> None:
        sse_events.append(event)

    start = time.perf_counter()
    results = await process_pdf_files_turbo(
        files=pdf_files,
        pdf_format=PDFFormat.CRT,
        return_regex=False,
        on_event=on_event,
        batch_size=50,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    return results, elapsed_ms, len(sse_events)


async def main() -> None:
    num_pdfs = 1000

    print(f"\n{'=' * 60}")
    print(f"BENCHMARK COMPARATIVO - {num_pdfs} PDFs")
    print("ASYNCIO vs TURBO (ProcessPoolExecutor)")
    print(f"{'=' * 60}\n")

    # [1] Crear PDFs de prueba válidos
    print("[1] Creando PDFs de prueba válidos...")
    start = time.perf_counter()
    pdf_files = [(f"crt_{i}.pdf", crear_pdf_crt_valido(i)) for i in range(num_pdfs)]
    crear_ms = (time.perf_counter() - start) * 1000
    print(f"    Creados {num_pdfs} PDFs en {crear_ms:.0f}ms")

    # [2] Benchmark ASYNCIO
    print("\n[2] Benchmark ASYNCIO (actual)...")
    results_async, ms_async, events_async = await benchmark_asyncio(pdf_files)
    successes_async = len([r for r in results_async if r["status"] == "fulfilled"])
    failures_async = len([r for r in results_async if r["status"] == "rejected"])
    print(f"    Tiempo: {ms_async:.0f}ms ({ms_async / num_pdfs:.2f}ms/PDF)")
    print(f"    Eventos SSE: {events_async}")
    print(f"    Éxitos: {successes_async}, Fallos: {failures_async}")
    print(f"    ¿Cumple <2s?: {'✅ SÍ' if ms_async < 2000 else '❌ NO'}")

    # [3] Benchmark TURBO
    print("\n[3] Benchmark TURBO (ProcessPoolExecutor)...")
    results_turbo, ms_turbo, events_turbo = await benchmark_turbo(pdf_files)
    successes_turbo = len([r for r in results_turbo if r["status"] == "fulfilled"])
    failures_turbo = len([r for r in results_turbo if r["status"] == "rejected"])
    print(f"    Tiempo: {ms_turbo:.0f}ms ({ms_turbo / num_pdfs:.2f}ms/PDF)")
    print(f"    Eventos SSE: {events_turbo}")
    print(f"    Éxitos: {successes_turbo}, Fallos: {failures_turbo}")
    print(f"    ¿Cumple <2s?: {'✅ SÍ' if ms_turbo < 2000 else '❌ NO'}")

    # [4] Comparación
    speedup = ms_async / ms_turbo if ms_turbo > 0 else 0
    print(f"\n{'=' * 60}")
    print("COMPARACIÓN:")
    print(f"  ASYNCIO: {ms_async:.0f}ms ({ms_async / num_pdfs:.2f}ms/PDF)")
    print(f"  TURBO:   {ms_turbo:.0f}ms ({ms_turbo / num_pdfs:.2f}ms/PDF)")
    print(f"  Speedup: {speedup:.2f}x {'más rápido' if speedup > 1 else 'más lento'}")
    print(f"{'=' * 60}")

    # Imprimir primeros errores si hay
    if failures_async > 0:
        print("\n[!] Primeros 3 errores ASYNCIO:")
        rejected_async = [r for r in results_async if r["status"] == "rejected"][:3]
        for r in rejected_async:
            reason = r.get("reason", {})
            if isinstance(reason, dict):
                print(
                    f"    - {reason.get('fileName', 'unknown')}: {str(reason.get('error', ''))[:80]}..."
                )

    if failures_turbo > 0:
        print("\n[!] Primeros 3 errores TURBO:")
        rejected_turbo = [r for r in results_turbo if r["status"] == "rejected"][:3]
        for r in rejected_turbo:
            reason = r.get("reason", {})
            if isinstance(reason, dict):
                print(
                    f"    - {reason.get('fileName', 'unknown')}: {str(reason.get('error', ''))[:80]}..."
                )


if __name__ == "__main__":
    asyncio.run(main())
