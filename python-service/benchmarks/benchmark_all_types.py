#!/usr/bin/env python3
"""
Benchmark de todos los tipos de PDF con archivos REALES.

Este benchmark prueba el rendimiento del sistema con PDFs reales
de los 4 tipos soportados:
1. CRT (Certificado de Revisión Técnica)
2. HOMOLOGACIÓN (Certificado de Homologación)
3. PERMISO_CIRCULACION (Permiso de Circulación)
4. SOAP (Seguro Obligatorio de Accidentes Personales)
"""

import asyncio
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Agregar el path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import PDFFormat
from app.services.pdf_service import process_pdf_files

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Carpeta base con los PDFs de prueba
PDF_TEST_BASE = Path(__file__).parent.parent.parent / "pdf pruebas"

# Mapeo de tipos a carpetas
PDF_FOLDERS = {
    PDFFormat.CRT: PDF_TEST_BASE / "Certificado de revision tecnica",
    PDFFormat.CERTIFICADO_DE_HOMOLOGACION: PDF_TEST_BASE / "Homologacion",
    PDFFormat.PERMISO_CIRCULACION: PDF_TEST_BASE / "Permiso de Circulacion",
    PDFFormat.SOAP: PDF_TEST_BASE / "SOAP",
}

# Cuántos PDFs de cada tipo usar en el benchmark
PDFS_PER_TYPE = 100  # Total: 400 PDFs (100 x 4 tipos)


@dataclass
class TypeStats:
    """Estadísticas por tipo de PDF."""

    total: int = 0
    success: int = 0
    failed: int = 0
    time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return (self.success / self.total * 100) if self.total > 0 else 0.0

    @property
    def avg_time_per_pdf(self) -> float:
        return (self.time_ms / self.total) if self.total > 0 else 0.0


def get_pdf_files(folder: Path, limit: int) -> list[tuple[str, bytes]]:
    """Obtiene los archivos PDF de una carpeta."""
    files: list[tuple[str, bytes]] = []

    if not folder.exists():
        print(f"⚠️  Carpeta no encontrada: {folder}")
        return files

    pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))

    if len(pdf_files) == 0:
        print(f"⚠️  No se encontraron PDFs en: {folder}")
        return files

    # Seleccionar aleatoriamente si hay más archivos que el límite
    if len(pdf_files) > limit:
        pdf_files = random.sample(pdf_files, limit)

    for pdf_path in pdf_files:
        try:
            with open(pdf_path, "rb") as f:
                files.append((pdf_path.name, f.read()))
        except Exception as e:
            print(f"  ⚠️  Error leyendo {pdf_path.name}: {e}")

    return files


def format_time(ms: float) -> str:
    """Formatea el tiempo en formato legible."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        return f"{ms / 60000:.2f}min"


def print_separator(char: str = "═", length: int = 70) -> None:
    """Imprime una línea separadora."""
    print(char * length)


async def run_benchmark() -> None:
    """Ejecuta el benchmark completo."""
    print()
    print_separator("═")
    print("🚀 BENCHMARK DE TODOS LOS TIPOS DE PDF (con archivos REALES)")
    print_separator("═")
    print()

    # Verificar que existe la carpeta base
    if not PDF_TEST_BASE.exists():
        print(f"❌ ERROR: No se encontró la carpeta de pruebas: {PDF_TEST_BASE}")
        print("   Por favor, asegúrate de que existe la carpeta 'pdf pruebas' con subcarpetas:")
        print("   - Certificado de revision tecnica/")
        print("   - Homologacion/")
        print("   - Permiso de Circulacion/")
        print("   - SOAP/")
        return

    # Cargar PDFs de cada tipo
    print("📂 Cargando archivos PDF de cada tipo...")
    print()

    all_files: list[tuple[str, bytes, PDFFormat]] = []
    stats: dict[PDFFormat, TypeStats] = {}

    for pdf_format, folder in PDF_FOLDERS.items():
        print(f"  📁 {pdf_format.value}:")
        print(f"     Carpeta: {folder.name}/")

        files = get_pdf_files(folder, PDFS_PER_TYPE)
        stats[pdf_format] = TypeStats(total=len(files))

        # Agregar el formato a cada archivo para tracking
        for name, data in files:
            all_files.append((name, data, pdf_format))

        print(f"     ✓ {len(files)} archivos cargados")
        print()

    total_files = len(all_files)
    print_separator("─")
    print(f"📊 Total de archivos a procesar: {total_files}")
    print()

    if total_files == 0:
        print("❌ No hay archivos para procesar. Verifica las carpetas.")
        return

    # Mezclar archivos para simular procesamiento real
    random.shuffle(all_files)

    # Preparar lista para procesamiento (sin el formato, que es para tracking)
    files_to_process = [(name, data) for name, data, _ in all_files]
    format_by_name = {name: fmt for name, _, fmt in all_files}

    # Callback para eventos
    events: list[dict[str, Any]] = []

    def on_event(event: dict[str, object]) -> None:
        events.append(event)

    # Ejecutar benchmark
    print("⏱️  Iniciando procesamiento...")
    print()

    start_time = time.perf_counter()

    results = await process_pdf_files(
        files=files_to_process,
        pdf_format=None,  # Detección automática
        return_regex=False,
        on_event=on_event,
        concurrency=15,
    )

    total_time_ms = (time.perf_counter() - start_time) * 1000

    # Procesar resultados por tipo
    for result in results:
        file_name = result.get("value", {}).get("fileName") or result.get("reason", {}).get(
            "fileName"
        )

        if not file_name:
            continue

        pdf_format = format_by_name.get(file_name)
        if not pdf_format:
            continue

        if result.get("status") == "fulfilled":
            stats[pdf_format].success += 1
        else:
            stats[pdf_format].failed += 1
            error = result.get("reason", {}).get("error", "Unknown error")
            # Limpiar HTML del error
            error = error.replace('<span style="background-color: yellow; font-weight: bold;">', "")
            error = error.replace("</span>", "")
            if len(error) > 100:
                error = error[:100] + "..."
            stats[pdf_format].errors.append(f"{file_name}: {error}")

    # Calcular tiempo por tipo (aproximado, basado en proporción)
    for _pdf_format, stat in stats.items():
        if stat.total > 0:
            stat.time_ms = (stat.total / total_files) * total_time_ms

    # Mostrar resultados
    print_separator("═")
    print("📈 RESULTADOS DEL BENCHMARK")
    print_separator("═")
    print()

    # Resultados generales
    total_success = sum(s.success for s in stats.values())
    total_failed = sum(s.failed for s in stats.values())
    overall_rate = (total_success / total_files * 100) if total_files > 0 else 0

    print(f"⏱️  Tiempo total: {format_time(total_time_ms)}")
    print(f"📄 PDFs procesados: {total_files}")
    print(f"   ✅ Exitosos: {total_success}")
    print(f"   ❌ Fallidos: {total_failed}")
    print(f"   📊 Tasa de éxito: {overall_rate:.1f}%")
    print(f"   ⚡ Promedio por PDF: {total_time_ms / total_files:.2f}ms")
    print()

    # Resultados por tipo
    print_separator("─")
    print("📊 RESULTADOS POR TIPO DE DOCUMENTO")
    print_separator("─")
    print()

    for pdf_format, stat in stats.items():
        emoji = "✅" if stat.success_rate >= 90 else ("⚠️" if stat.success_rate >= 70 else "❌")
        print(f"{emoji} {pdf_format.value}:")
        print(f"   Total: {stat.total} | Éxitos: {stat.success} | Fallos: {stat.failed}")
        print(f"   Tasa de éxito: {stat.success_rate:.1f}%")
        print(
            f"   Tiempo estimado: {format_time(stat.time_ms)} ({stat.avg_time_per_pdf:.2f}ms/PDF)"
        )

        if stat.errors and len(stat.errors) <= 5:
            print("   Errores:")
            for error in stat.errors[:5]:
                print(f"      • {error[:80]}")
        elif stat.errors:
            print(f"   Errores: {len(stat.errors)} (mostrando primeros 3)")
            for error in stat.errors[:3]:
                print(f"      • {error[:80]}")
        print()

    # Tabla resumen
    print_separator("═")
    print("📋 TABLA RESUMEN")
    print_separator("─")
    print(f"{'Tipo':<35} {'Total':>8} {'Éxitos':>8} {'Fallos':>8} {'Tasa':>8}")
    print_separator("─")

    for pdf_format, stat in stats.items():
        rate_str = f"{stat.success_rate:.1f}%"
        print(
            f"{pdf_format.value:<35} {stat.total:>8} {stat.success:>8} {stat.failed:>8} {rate_str:>8}"
        )

    print_separator("─")
    print(
        f"{'TOTAL':<35} {total_files:>8} {total_success:>8} {total_failed:>8} {overall_rate:.1f}%"
    )
    print_separator("═")
    print()

    # Verificación de rendimiento
    print("🎯 VERIFICACIÓN DE RENDIMIENTO")
    print_separator("─")
    pdfs_per_second = (total_files / total_time_ms) * 1000
    target_pdfs_per_second = 500  # 1000 PDFs en 2 segundos = 500/s

    if pdfs_per_second >= target_pdfs_per_second:
        print(f"✅ OBJETIVO CUMPLIDO: {pdfs_per_second:.0f} PDFs/segundo")
        print(f"   (Meta: {target_pdfs_per_second} PDFs/segundo)")
        projected_1000 = (1000 / pdfs_per_second) * 1000
        print(f"   Proyección para 1000 PDFs: {format_time(projected_1000)}")
    else:
        print(f"⚠️  Por debajo del objetivo: {pdfs_per_second:.0f} PDFs/segundo")
        print(f"   (Meta: {target_pdfs_per_second} PDFs/segundo)")

    print()
    print_separator("═")
    print("✅ Benchmark completado")
    print_separator("═")
    print()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
