"""
Excel Service - Generación de archivos Excel.

Equivalente a excelUtils.ts usando XlsxWriter.
"""

import io
import logging
from typing import Any

import xlsxwriter

from ..models import ExcelStats, PDFFormat
from ..utils.pdf_utils import get_format_display_name
from ..utils.text_utils import normalize_plate_with_check, sanitizar_nombre, strip_html_tags

logger = logging.getLogger(__name__)


def _transform_records(
    registros: list[dict[str, str]],
    pdf_format: PDFFormat | None,
) -> list[dict[str, str]]:
    """
    Transforma los registros según el formato de PDF.

    Equivalente a la lógica de transformación en generateExcel() de excelUtils.ts
    """
    for registro in registros:
        if pdf_format == PDFFormat.CERTIFICADO_DE_HOMOLOGACION:
            # Para Homologación: procesar "Patente" eliminando guiones
            if "Patente" in registro:
                registro["Patente"] = registro["Patente"].replace("-", "").strip()
            # No se asigna dígito verificador
            registro.pop("digito verificador", None)

        elif pdf_format == PDFFormat.PERMISO_CIRCULACION:
            # Para Permiso de Circulación: procesar "Placa Única"
            if "Placa Única" in registro:
                plate, check_digit = normalize_plate_with_check(registro["Placa Única"])
                registro["Placa Única"] = plate
                if check_digit:
                    registro["digito verificador"] = check_digit
                else:
                    registro.pop("digito verificador", None)

        elif pdf_format == PDFFormat.SOAP:
            # Para SOAP: procesar "INSCRIPCION R.V.M"
            if "INSCRIPCION R.V.M" in registro:
                plate, check_digit = normalize_plate_with_check(registro["INSCRIPCION R.V.M"])
                registro["INSCRIPCION R.V.M"] = plate
                if check_digit:
                    registro["digito verificador"] = check_digit
                else:
                    registro.pop("digito verificador", None)

        else:
            # Para otros formatos: procesar campos de placa
            for key in ["Patente", "Placa Única", "INSCRIPCION R.V.M"]:
                if key in registro and "-" in registro[key]:
                    parts = registro[key].split("-")
                    if len(parts) > 1:
                        combined = "".join(parts).strip()
                        registro[key] = combined[:6]
                        if len(combined) > 6:
                            registro["digito verificador"] = combined[6:]

    return registros


def _order_registro(
    registro: dict[str, Any],
    pdf_format: PDFFormat | None,
) -> dict[str, Any]:
    """
    Reordena las claves del registro para el Excel.

    Equivalente a orderRegistro() en excelUtils.ts
    """
    ordered: dict[str, Any] = {}

    # Siempre primero "Nombre PDF"
    if "Nombre PDF" in registro:
        ordered["Nombre PDF"] = registro["Nombre PDF"]

    # Luego el campo de placa según el formato
    if pdf_format == PDFFormat.CERTIFICADO_DE_HOMOLOGACION:
        if "Patente" in registro:
            ordered["Patente"] = registro["Patente"]

    elif pdf_format == PDFFormat.PERMISO_CIRCULACION:
        if "Placa Única" in registro:
            ordered["Placa Única"] = registro["Placa Única"]
            if "digito verificador" in registro:
                ordered["digito verificador"] = registro["digito verificador"]

    elif pdf_format == PDFFormat.SOAP:
        if "INSCRIPCION R.V.M" in registro:
            ordered["INSCRIPCION R.V.M"] = registro["INSCRIPCION R.V.M"]
            if "digito verificador" in registro:
                ordered["digito verificador"] = registro["digito verificador"]

    else:
        # Para otros formatos
        for key in ["Patente", "Placa Única", "INSCRIPCION R.V.M"]:
            if key in registro:
                ordered[key] = registro[key]
                if "digito verificador" in registro:
                    ordered["digito verificador"] = registro["digito verificador"]
                break

    # Agregar el resto de campos
    skip_keys = {"Nombre PDF", "Patente", "Placa Única", "INSCRIPCION R.V.M", "digito verificador"}
    for key, value in registro.items():
        if key not in skip_keys:
            ordered[key] = value

    return ordered


def generate_excel(
    registros: list[dict[str, str]],
    file_name: str,
    pdf_format: PDFFormat | None = None,
    stats: ExcelStats | None = None,
) -> tuple[bytes, str]:
    """
    Genera un archivo Excel con dos hojas: "Datos" y "Estadisticas".

    Equivalente a generateExcel() en excelUtils.ts usando XlsxWriter.

    Args:
        registros: Datos a incluir en la hoja "Datos"
        file_name: Nombre base del archivo
        pdf_format: Formato de PDF (opcional)
        stats: Estadísticas de conversión (opcional)

    Returns:
        Tupla (buffer_bytes, encoded_name)
    """
    # Transformar registros según el formato
    registros = _transform_records(registros, pdf_format)

    # Ordenar registros
    ordered_registros = [_order_registro(r, pdf_format) for r in registros]

    # Forzar inclusión de "digito verificador" si algún registro lo tiene
    has_check_digit = any("digito verificador" in r for r in ordered_registros)
    if has_check_digit:
        for record in ordered_registros:
            if "digito verificador" not in record:
                record["digito verificador"] = ""

    # Obtener headers únicos manteniendo orden
    headers: list[str] = []
    seen: set[str] = set()
    for record in ordered_registros:
        for key in record.keys():
            if key not in seen:
                headers.append(key)
                seen.add(key)

    # Crear workbook en memoria
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # Formatos
    header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9E1F2",
            "border": 1,
        }
    )
    cell_format = workbook.add_format({"border": 1})
    success_format = workbook.add_format({"bg_color": "#C6EFCE"})
    error_format = workbook.add_format({"bg_color": "#FFC7CE"})

    # Hoja "Datos"
    data_sheet = workbook.add_worksheet("Datos")

    if not ordered_registros:
        data_sheet.write(0, 0, "No se encontraron datos para generar el Excel.")
    else:
        # Escribir headers
        for col_idx, header in enumerate(headers):
            data_sheet.write(0, col_idx, header, header_format)

        # Escribir datos
        for row_idx, registro in enumerate(ordered_registros):
            for col_idx, header in enumerate(headers):
                value = registro.get(header, "")
                data_sheet.write(row_idx + 1, col_idx, value, cell_format)

        # Ajustar anchos de columna
        for col_idx, header in enumerate(headers):
            max_len = len(header)
            for registro in ordered_registros:
                val = str(registro.get(header, ""))
                if len(val) > max_len:
                    max_len = len(val)
            data_sheet.set_column(col_idx, col_idx, min(max_len + 2, 50))

    # Hoja "Estadisticas" (si hay stats)
    if stats:
        stats_sheet = workbook.add_worksheet("Estadisticas")

        title_format = workbook.add_format({"bold": True, "font_size": 14})
        stats_sheet.write(0, 0, "Estadísticas de Conversión", title_format)

        stats_sheet.write(2, 0, "Total Procesados:")
        stats_sheet.write(2, 1, stats.total_procesados)

        stats_sheet.write(3, 0, "Total Exitosos:")
        stats_sheet.write(3, 1, stats.total_exitosos, success_format)

        stats_sheet.write(4, 0, "Total Fallidos:")
        stats_sheet.write(4, 1, stats.total_fallidos, error_format)
        if stats.fallidos:
            stats_sheet.write(6, 0, "Archivos Fallidos", title_format)
            stats_sheet.write(7, 0, "Nombre Archivo", header_format)
            stats_sheet.write(7, 1, "Error", header_format)

            row = 8
            for fallo in stats.fallidos:
                clean_error = strip_html_tags(fallo.error)
                stats_sheet.write(row, 0, fallo.file_name)
                stats_sheet.write(row, 1, clean_error)
                row += 1

            # Ajustar anchos
            stats_sheet.set_column(0, 0, 40)
            stats_sheet.set_column(1, 1, 80)

    workbook.close()

    # Generar nombre de archivo
    final_file_name = sanitizar_nombre(file_name)
    if not final_file_name.endswith(".xlsx"):
        final_file_name += ".xlsx"

    # URL encode
    import urllib.parse

    encoded_name = urllib.parse.quote(final_file_name)

    return output.getvalue(), encoded_name


def generate_excel_from_results(
    successes: list[dict[str, Any]],
    pdf_format: PDFFormat,
    stats: ExcelStats | None = None,
) -> tuple[bytes, str]:
    """
    Genera un Excel a partir de los resultados exitosos.

    Equivalente a generateExcelFromResults() en pdfService.ts

    Args:
        successes: Lista de resultados exitosos
        pdf_format: Formato de PDF
        stats: Estadísticas de conversión

    Returns:
        Tupla (excel_buffer, file_name)
    """
    base_file_name = get_format_display_name(pdf_format)

    # Construir registros
    registros = []
    for r in successes:
        registro = {"Nombre PDF": r["fileName"]}
        registro.update(r.get("datos", {}))
        registros.append(registro)

    return generate_excel(registros, base_file_name, pdf_format, stats)
