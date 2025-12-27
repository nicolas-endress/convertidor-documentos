"""Script para verificar integridad de datos en la extracción de PDFs de homologación."""

import re
from pathlib import Path

import fitz  # type: ignore[import-untyped]

from app.extractors.homologacion_extractor import (
    best_effort_validation_homologacion,
    extraer_datos_homologacion,
)


def verificar_pdfs() -> None:
    """Verifica la extracción de datos de PDFs de homologación."""
    homol_dir = Path(
        r"c:\Users\nicol\OneDrive\Escritorio\Entorno de pruebas\convertidor-documentos\pdf pruebas\HOMOLOGACION"
    )
    all_pdfs = list(homol_dir.glob("*.pdf"))

    # Seleccionar PDFs con diferentes nombres (no solo copias)
    unique_pdfs: list[Path] = []
    seen_patterns: set[str] = set()
    for p in all_pdfs:
        base = re.sub(r" - copia.*", "", p.stem)
        if base not in seen_patterns:
            seen_patterns.add(base)
            unique_pdfs.append(p)
            if len(unique_pdfs) >= 15:
                break

    print("=" * 80)
    print(f"VERIFICACION DE INTEGRIDAD - {len(unique_pdfs)} PDFs UNICOS")
    print("=" * 80)

    resultados = {"ok": 0, "error": 0}

    for pdf_path in unique_pdfs:
        print(f"\n📄 {pdf_path.name[:60]}")
        print("-" * 60)

        # Extraer texto raw
        doc = fitz.open(str(pdf_path))
        text: str = ""
        for page in doc:
            page_text: str = page.get_text()  # type: ignore[assignment]
            text += page_text
        doc.close()

        # Extraer datos con el extractor
        datos = extraer_datos_homologacion(text)

        # Mostrar campos clave
        modelo = datos.get("Modelo", "")
        vin = datos.get("VIN", "")
        patente = datos.get("Patente", "")

        print(f"  Patente: {patente}")
        print(f"  VIN: {vin}")
        modelo_display = modelo[:55] + "..." if len(modelo) > 55 else modelo
        print(f"  Modelo: {modelo_display}")

        # Validar con la función oficial
        try:
            best_effort_validation_homologacion(datos, pdf_path.name)
            print("  ✅ Validación: PASÓ")
            resultados["ok"] += 1
        except ValueError as e:
            err_lines = str(e).split("\n")
            print("  ❌ Validación: FALLÓ")
            for line in err_lines[1:4]:
                print(f"     {line}")
            resultados["error"] += 1

    print("\n" + "=" * 80)
    print(f"RESUMEN: {resultados['ok']} correctos, {resultados['error']} con problemas")
    print("=" * 80)


if __name__ == "__main__":
    verificar_pdfs()
