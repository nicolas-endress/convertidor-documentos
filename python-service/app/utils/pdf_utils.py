"""
PDF Processor Service - Utilidades de PDF.

Extracción de texto usando PyMuPDF (fitz) y detección de formato.
"""

from typing import TYPE_CHECKING

from ..models import PDFFormat

if TYPE_CHECKING:
    import fitz
else:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None  # type: ignore[assignment]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extrae el texto completo de un PDF usando PyMuPDF.

    Esta implementación es más rápida que pdf2json y mantiene
    compatibilidad con el formato de texto esperado.

    Args:
        file_bytes: Contenido del archivo PDF en bytes

    Returns:
        Texto extraído del PDF

    Raises:
        ValueError: Si el PDF no contiene texto extraíble
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is not installed. Install with: pip install pymupdf")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")  # type: ignore[union-attr]
        text_parts: list[str] = []

        for page in doc:
            # Extraer texto de la página
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)

        doc.close()

        # Unir todas las páginas con espacio
        all_text = " ".join(text_parts)

        if not all_text.strip():
            raise ValueError("El PDF no contiene texto extraíble o el formato no es válido")

        return all_text

    except Exception as exc:
        if "FileDataError" in type(exc).__name__:
            raise ValueError(f"Error al parsear el PDF: {exc}") from exc
        raise ValueError(f"Error al procesar el PDF: {exc}") from exc


def detectar_formato(texto: str) -> PDFFormat | None:
    """
    Detecta el formato del PDF según palabras clave en el texto extraído.

    Equivalente exacto de detectarFormato() en pdfUtils.ts

    Args:
        texto: Texto extraído del PDF

    Returns:
        El formato detectado o None si no se identifica
    """
    upper_text = texto.upper()

    # Orden de prioridad igual al sistema TypeScript
    if "CERTIFICADO DE HOMOLOGACIÓN" in upper_text:
        return PDFFormat.CERTIFICADO_DE_HOMOLOGACION

    if "CERTIFICADO DE REVISIÓN TÉCNICA" in upper_text or "FECHA REVISIÓN" in upper_text:
        return PDFFormat.CRT

    if "SEGURO OBLIGATORIO" in upper_text or "SOAP" in upper_text:
        return PDFFormat.SOAP

    if "PERMISO DE CIRCULACIÓN" in upper_text or "PLACA ÚNICA" in upper_text:
        return PDFFormat.PERMISO_CIRCULACION

    return None


def get_format_display_name(pdf_format: PDFFormat) -> str:
    """
    Obtiene el nombre para mostrar de un formato de PDF.

    Args:
        pdf_format: Formato de PDF

    Returns:
        Nombre legible del formato
    """
    names = {
        PDFFormat.CERTIFICADO_DE_HOMOLOGACION: "Certificado de Homologación",
        PDFFormat.CRT: "Certificado de Revisión Técnica (CRT)",
        PDFFormat.SOAP: "Seguro Obligatorio (SOAP)",
        PDFFormat.PERMISO_CIRCULACION: "Permiso de Circulación",
    }
    return names.get(pdf_format, "Consolidado")
