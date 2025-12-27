"""Servicios del procesador de PDFs."""

from .excel_service import generate_excel, generate_excel_from_results
from .pdf_service import procesar_pdf, process_pdf_files

__all__ = [
    "procesar_pdf",
    "process_pdf_files",
    "generate_excel",
    "generate_excel_from_results",
]
