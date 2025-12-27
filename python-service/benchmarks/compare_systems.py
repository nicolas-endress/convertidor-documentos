"""
Script de benchmark para comparar Python Service vs TypeScript.
Ejecuta pruebas de rendimiento y genera reportes.

Uso:
    python benchmarks/compare_systems.py --pdfs-dir ./test_pdfs --format CRT
"""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark individual."""

    system: str
    format: str
    total_files: int
    successful: int
    failed: int
    total_time_ms: float
    avg_time_per_file_ms: float
    min_time_ms: float = 0.0
    max_time_ms: float = 0.0
    std_dev_ms: float = 0.0
    files_per_second: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ComparisonReport:
    """Reporte de comparación entre sistemas."""

    python_result: BenchmarkResult
    typescript_result: BenchmarkResult | None
    speedup_factor: float
    summary: str


async def benchmark_python_service(
    pdfs_dir: Path,
    pdf_format: str,
    endpoint: str = "http://localhost:8000/convert",
) -> BenchmarkResult:
    """
    Benchmark del servicio Python.

    Args:
        pdfs_dir: Directorio con PDFs de prueba.
        pdf_format: Formato de PDF (CRT, SOAP, etc.).
        endpoint: URL del endpoint de conversión.

    Returns:
        Resultado del benchmark.
    """
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No se encontraron PDFs en {pdfs_dir}")

    logger.info("Iniciando benchmark Python", total_files=len(pdf_files))

    # Preparar FormData
    data = aiohttp.FormData()
    data.add_field("pdfFormat", pdf_format)

    for pdf_file in pdf_files:
        data.add_field(
            "files",
            open(pdf_file, "rb"),
            filename=pdf_file.name,
            content_type="application/pdf",
        )

    successful = 0
    failed = 0

    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, data=data) as response:
            if response.status != 200:
                raise Exception(f"Error HTTP: {response.status}")

            # Procesar eventos SSE
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue

                try:
                    event = json.loads(line[5:].strip())
                    event_type = event.get("event")

                    if event_type == "status":
                        if event.get("data", {}).get("ok"):
                            successful += 1
                        else:
                            failed += 1

                    elif event_type == "elapsedMsSoFar":
                        # Estimación de tiempo por archivo
                        pass

                except json.JSONDecodeError:
                    continue

    end_time = time.perf_counter()
    total_time_ms = (end_time - start_time) * 1000

    # Cerrar archivos abiertos
    data._fields.clear()

    avg_time = total_time_ms / len(pdf_files) if pdf_files else 0

    return BenchmarkResult(
        system="Python",
        format=pdf_format,
        total_files=len(pdf_files),
        successful=successful,
        failed=failed,
        total_time_ms=total_time_ms,
        avg_time_per_file_ms=avg_time,
        files_per_second=len(pdf_files) / (total_time_ms / 1000) if total_time_ms > 0 else 0,
    )


async def benchmark_typescript_service(
    pdfs_dir: Path,
    pdf_format: str,
    endpoint: str = "http://localhost:3000/api/convert",
) -> BenchmarkResult | None:
    """
    Benchmark del servicio TypeScript (Next.js).

    Args:
        pdfs_dir: Directorio con PDFs de prueba.
        pdf_format: Formato de PDF.
        endpoint: URL del endpoint de conversión.

    Returns:
        Resultado del benchmark o None si no está disponible.
    """
    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No se encontraron PDFs en {pdfs_dir}")

    # Verificar si el servicio está disponible
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint.replace("/convert", ""), timeout=aiohttp.ClientTimeout(total=2)
            ):
                pass
    except Exception:
        logger.warning("Servicio TypeScript no disponible, omitiendo benchmark")
        return None

    logger.info("Iniciando benchmark TypeScript", total_files=len(pdf_files))

    # Similar al benchmark de Python pero con endpoint TypeScript
    data = aiohttp.FormData()
    data.add_field("pdfFormat", pdf_format)

    for pdf_file in pdf_files:
        data.add_field(
            "files",
            open(pdf_file, "rb"),
            filename=pdf_file.name,
            content_type="application/pdf",
        )

    successful = 0
    failed = 0

    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, data=data) as response:
            if response.status != 200:
                logger.error("Error en TypeScript service", status=response.status)
                return None

            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue

                try:
                    event = json.loads(line[5:].strip())
                    event_type = event.get("event")

                    if event_type == "status":
                        if event.get("data", {}).get("ok"):
                            successful += 1
                        else:
                            failed += 1

                except json.JSONDecodeError:
                    continue

    end_time = time.perf_counter()
    total_time_ms = (end_time - start_time) * 1000
    avg_time = total_time_ms / len(pdf_files) if pdf_files else 0

    return BenchmarkResult(
        system="TypeScript",
        format=pdf_format,
        total_files=len(pdf_files),
        successful=successful,
        failed=failed,
        total_time_ms=total_time_ms,
        avg_time_per_file_ms=avg_time,
        files_per_second=len(pdf_files) / (total_time_ms / 1000) if total_time_ms > 0 else 0,
    )


def generate_comparison_report(
    python_result: BenchmarkResult,
    typescript_result: BenchmarkResult | None,
) -> ComparisonReport:
    """Genera reporte de comparación entre sistemas."""
    if typescript_result:
        speedup = typescript_result.total_time_ms / python_result.total_time_ms

        if speedup >= 2:
            summary = f"✅ Python es {speedup:.2f}x más rápido (objetivo ≥2x cumplido)"
        elif speedup > 1:
            summary = f"⚠️ Python es {speedup:.2f}x más rápido (objetivo ≥2x NO cumplido)"
        else:
            summary = f"❌ Python es {1 / speedup:.2f}x más lento"
    else:
        speedup = 0.0
        summary = "⚠️ Solo se ejecutó benchmark de Python (TypeScript no disponible)"

    return ComparisonReport(
        python_result=python_result,
        typescript_result=typescript_result,
        speedup_factor=speedup,
        summary=summary,
    )


def print_report(report: ComparisonReport) -> None:
    """Imprime el reporte de comparación."""
    print("\n" + "=" * 70)
    print("BENCHMARK PDF CONVERTER - REPORTE DE COMPARACIÓN")
    print("=" * 70)

    py = report.python_result
    print("\n📊 Python Service:")
    print(f"   - Archivos procesados: {py.successful}/{py.total_files}")
    print(f"   - Tiempo total: {py.total_time_ms:.2f} ms")
    print(f"   - Tiempo promedio/archivo: {py.avg_time_per_file_ms:.2f} ms")
    print(f"   - Rendimiento: {py.files_per_second:.2f} archivos/segundo")

    if report.typescript_result:
        ts = report.typescript_result
        print("\n📊 TypeScript Service:")
        print(f"   - Archivos procesados: {ts.successful}/{ts.total_files}")
        print(f"   - Tiempo total: {ts.total_time_ms:.2f} ms")
        print(f"   - Tiempo promedio/archivo: {ts.avg_time_per_file_ms:.2f} ms")
        print(f"   - Rendimiento: {ts.files_per_second:.2f} archivos/segundo")

    print(f"\n🏆 Resultado: {report.summary}")

    if report.speedup_factor > 0:
        print(f"   Factor de mejora: {report.speedup_factor:.2f}x")

    print("\n" + "=" * 70)


async def run_benchmark(
    pdfs_dir: Path,
    pdf_format: str,
    python_endpoint: str,
    typescript_endpoint: str | None,
    runs: int = 3,
) -> None:
    """
    Ejecuta benchmarks múltiples veces y promedia resultados.

    Args:
        pdfs_dir: Directorio con PDFs de prueba.
        pdf_format: Formato de PDF.
        python_endpoint: URL del servicio Python.
        typescript_endpoint: URL del servicio TypeScript (opcional).
        runs: Número de ejecuciones para promediar.
    """
    logger.info(
        "Iniciando benchmark",
        pdfs_dir=str(pdfs_dir),
        format=pdf_format,
        runs=runs,
    )

    python_times: list[float] = []
    typescript_times: list[float] = []
    py_result: BenchmarkResult | None = None
    ts_result: BenchmarkResult | None = None

    for i in range(runs):
        print(f"\n🔄 Ejecución {i + 1}/{runs}...")

        # Benchmark Python
        py_result = await benchmark_python_service(pdfs_dir, pdf_format, python_endpoint)
        python_times.append(py_result.total_time_ms)

        # Benchmark TypeScript (si está disponible)
        if typescript_endpoint:
            ts_result = await benchmark_typescript_service(
                pdfs_dir, pdf_format, typescript_endpoint
            )
            if ts_result:
                typescript_times.append(ts_result.total_time_ms)

    # Calcular promedios
    if not python_times or py_result is None:
        logger.error("No se ejecutaron benchmarks de Python")
        return

    avg_python = statistics.mean(python_times)
    final_python = BenchmarkResult(
        system="Python",
        format=pdf_format,
        total_files=py_result.total_files,
        successful=py_result.successful,
        failed=py_result.failed,
        total_time_ms=avg_python,
        avg_time_per_file_ms=avg_python / py_result.total_files,
        min_time_ms=min(python_times),
        max_time_ms=max(python_times),
        std_dev_ms=statistics.stdev(python_times) if len(python_times) > 1 else 0,
        files_per_second=py_result.total_files / (avg_python / 1000),
    )

    final_typescript = None
    if typescript_times:
        avg_ts = statistics.mean(typescript_times)
        final_typescript = BenchmarkResult(
            system="TypeScript",
            format=pdf_format,
            total_files=ts_result.total_files,  # type: ignore
            successful=ts_result.successful,  # type: ignore
            failed=ts_result.failed,  # type: ignore
            total_time_ms=avg_ts,
            avg_time_per_file_ms=avg_ts / ts_result.total_files,  # type: ignore
            min_time_ms=min(typescript_times),
            max_time_ms=max(typescript_times),
            std_dev_ms=statistics.stdev(typescript_times) if len(typescript_times) > 1 else 0,
            files_per_second=ts_result.total_files / (avg_ts / 1000),  # type: ignore
        )

    report = generate_comparison_report(final_python, final_typescript)
    print_report(report)

    # Guardar resultados en JSON
    output_file = (
        pdfs_dir / f"benchmark_results_{pdf_format}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "python": final_python.__dict__,
                "typescript": final_typescript.__dict__ if final_typescript else None,
                "speedup_factor": report.speedup_factor,
                "summary": report.summary,
                "runs": runs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n📁 Resultados guardados en: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark de comparación Python vs TypeScript PDF Converter"
    )
    parser.add_argument(
        "--pdfs-dir",
        type=Path,
        required=True,
        help="Directorio con PDFs de prueba",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["CRT", "CERTIFICADO_DE_HOMOLOGACION", "SOAP", "PERMISO_CIRCULACION"],
        required=True,
        help="Formato de PDF a procesar",
    )
    parser.add_argument(
        "--python-endpoint",
        type=str,
        default="http://localhost:8000/convert",
        help="URL del endpoint Python",
    )
    parser.add_argument(
        "--typescript-endpoint",
        type=str,
        default="http://localhost:3000/api/convert",
        help="URL del endpoint TypeScript (omitir para solo Python)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Número de ejecuciones para promediar",
    )
    parser.add_argument(
        "--no-typescript",
        action="store_true",
        help="Omitir benchmark de TypeScript",
    )

    args = parser.parse_args()

    ts_endpoint = None if args.no_typescript else args.typescript_endpoint

    asyncio.run(
        run_benchmark(
            pdfs_dir=args.pdfs_dir,
            pdf_format=args.format,
            python_endpoint=args.python_endpoint,
            typescript_endpoint=ts_endpoint,
            runs=args.runs,
        )
    )


if __name__ == "__main__":
    main()
