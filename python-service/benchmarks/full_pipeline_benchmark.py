"""
Benchmark del endpoint /convert completo.

Mide el tiempo total incluyendo:
- Upload de archivos
- Procesamiento de PDFs
- Generación de Excel
- Serialización JSON
- SSE streaming
"""

import asyncio
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import fitz

from app.models import ExcelStats, PDFFormat
from app.services.excel_service import generate_excel_from_results
from app.services.pdf_service import process_pdf_files


def create_realistic_crt_pdf() -> bytes:
    """Crea un PDF CRT más realista (tamaño típico ~50-100KB)."""
    doc: fitz.Document = fitz.open()
    page: fitz.Page = doc.new_page(width=612, height=792)  # Tamaño carta

    # Texto completo de un CRT típico
    text = (
        """
    CERTIFICADO DE REVISIÓN TÉCNICA

    PLANTA DE REVISIÓN TÉCNICA
    NOMBRE PLANTA: SOCOVESA SANTIAGO
    RUT: 76.XXX.XXX-X

    DATOS DEL VEHÍCULO

    PLACA PATENTE: ABCD12
    VIN/CHASIS: 1HGBH41JXMN109186
    N° MOTOR: 2ZR1234567
    MARCA: TOYOTA
    MODELO: COROLLA XLI 1.6
    AÑO FABRICACIÓN: 2020
    COLOR: BLANCO
    TIPO VEHÍCULO: AUTOMÓVIL
    COMBUSTIBLE: BENCINA
    TRANSMISIÓN: AUTOMÁTICA

    RESULTADO DE LA REVISIÓN

    FECHA REVISIÓN: 15-01-2025
    HORA: 10:30
    N° FOLIO: 123456789

    ESTADO: APROBADO

    VÁLIDO HASTA: 15-01-2026

    REVISIÓN TÉCNICA: APROBADO
    GASES CONTAMINANTES: APROBADO

    OBSERVACIONES:
    Sin observaciones.

    ___________________________
    FIRMA INSPECTOR

    Este documento es válido para circular.
    Cualquier adulteración invalida el certificado.

    """
        + "X" * 5000
    )  # Agregar contenido extra para simular tamaño real

    page.insert_text((50, 50), text, fontsize=10)

    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes


async def benchmark_full_pipeline(num_pdfs: int) -> dict[str, object]:
    """
    Benchmark del pipeline completo (similar al endpoint /convert).
    """
    print(f"\n{'=' * 60}")
    print(f"BENCHMARK PIPELINE COMPLETO: {num_pdfs} PDFs")
    print("=" * 60)

    # 1. Crear PDFs
    t0 = time.perf_counter()
    mock_pdf = create_realistic_crt_pdf()
    pdf_size_kb = len(mock_pdf) / 1024
    files_data = [(f"crt_{i}.pdf", mock_pdf) for i in range(num_pdfs)]
    t1 = time.perf_counter()
    print(f"[1] Crear {num_pdfs} PDFs ({pdf_size_kb:.1f}KB c/u): {(t1 - t0) * 1000:.0f}ms")

    # 2. Procesar PDFs
    events: list[dict[str, object]] = []

    def on_event(event: dict[str, object]) -> None:
        events.append(event)

    t2 = time.perf_counter()
    results = await process_pdf_files(
        files_data,
        pdf_format=PDFFormat.CRT,
        return_regex=False,
        on_event=on_event,
        concurrency=100,
    )
    t3 = time.perf_counter()
    print(
        f"[2] Procesar PDFs (asyncio, c=100): {(t3 - t2) * 1000:.0f}ms ({(t3 - t2) * 1000 / num_pdfs:.2f}ms/PDF)"
    )
    print(f"    - Eventos SSE generados: {len(events)}")

    # 3. Separar éxitos y fallos
    t4 = time.perf_counter()
    successes = [r for r in results if r["status"] == "fulfilled"]
    failures = [r for r in results if r["status"] == "rejected"]
    t5 = time.perf_counter()
    print(f"[3] Separar resultados: {(t5 - t4) * 1000:.0f}ms")
    print(f"    - Éxitos: {len(successes)}, Fallos: {len(failures)}")

    # 4. Generar Excel
    t6 = time.perf_counter()
    excel_buffer: bytes = b""
    file_name: str = ""
    excel_size_kb: float = 0.0
    if successes:
        success_values = [s["value"] for s in successes]
        stats = ExcelStats(
            totalProcesados=len(files_data),
            totalExitosos=len(successes),
            totalFallidos=len(failures),
            fallidos=[],
        )
        excel_buffer, file_name = generate_excel_from_results(
            success_values,
            PDFFormat.CRT,
            stats,
        )
        excel_size_kb = len(excel_buffer) / 1024
    t7 = time.perf_counter()
    print(f"[4] Generar Excel ({excel_size_kb:.1f}KB): {(t7 - t6) * 1000:.0f}ms")

    # 5. Serializar a JSON (simular respuesta SSE)
    import base64
    import json

    t8 = time.perf_counter()
    if successes:
        excel_base64 = base64.b64encode(excel_buffer).decode("utf-8")
        final_event = {
            "final": {
                "totalProcesados": len(files_data),
                "totalExitosos": len(successes),
                "totalFallidos": len(failures),
                "exitosos": [s["value"] for s in successes[:100]],  # Limitar para no explotar
                "excel": excel_base64,
                "fileName": file_name,
            }
        }
        json_str = json.dumps(final_event)
        json_size_kb = len(json_str) / 1024
    else:
        json_size_kb = 0
    t9 = time.perf_counter()
    print(f"[5] Serializar JSON ({json_size_kb:.1f}KB): {(t9 - t8) * 1000:.0f}ms")

    # Total
    total_time = t9 - t0
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_time * 1000:.0f}ms ({total_time:.2f}s)")
    print(f"Velocidad: {total_time * 1000 / num_pdfs:.2f}ms/PDF")
    print(f"¿Cumple <2s para 1000 PDFs?: {'✅ SÍ' if total_time < 2 else '❌ NO'}")
    print("=" * 60)

    return {
        "num_pdfs": num_pdfs,
        "total_ms": total_time * 1000,
        "ms_per_pdf": total_time * 1000 / num_pdfs,
        "success": total_time < 2,
    }


async def main():
    print("=" * 70)
    print("BENCHMARK COMPLETO DEL SISTEMA DE CONVERSIÓN DE PDFs")
    print("=" * 70)
    print(f"CPU cores: {mp.cpu_count()}")

    for num in [100, 500, 1000]:
        await benchmark_full_pipeline(num)


if __name__ == "__main__":
    asyncio.run(main())
