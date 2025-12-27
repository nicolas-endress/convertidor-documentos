"""Utilidades del servicio."""

from .logger import get_logger, logger, setup_logging
from .pdf_utils import detectar_formato, extract_text_from_pdf, get_format_display_name
from .text_utils import (
    buscar,
    normalize_plate_with_check,
    safe_filename,
    sanitizar_nombre,
    strip_html_tags,
)

__all__ = [
    "buscar",
    "sanitizar_nombre",
    "normalize_plate_with_check",
    "strip_html_tags",
    "safe_filename",
    "extract_text_from_pdf",
    "detectar_formato",
    "get_format_display_name",
    "setup_logging",
    "get_logger",
    "logger",
]
