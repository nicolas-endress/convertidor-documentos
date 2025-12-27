"""
Extractor Permiso de Circulación.

PORTADO LITERALMENTE desde permisoCirculacionExtractor.ts
Mantiene las mismas regex, campos y validaciones.
Soporta returnRegex para retornar las expresiones regulares usadas.
"""

import logging
import re
from typing import Any

from ..utils.text_utils import buscar

logger = logging.getLogger(__name__)


# ============================================================================
# REGEX COMPILADAS (equivalentes exactas a TypeScript)
# ============================================================================

REGEXES: dict[str, re.Pattern[str]] = {
    # Placa Única: secuencia de letras, números y guiones
    "Placa Única": re.compile(r"Placa\s+Única\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    # Código SII: secuencia de letras y números
    "Código SII": re.compile(r"Codigo\s+SII\s*[:\-]?\s*([A-Z0-9]+)", re.IGNORECASE),
    # Valor Permiso: dígitos
    "Valor Permiso": re.compile(r"Valor\s+Permiso\s*[:\-]?\s*(\d+)", re.IGNORECASE),
    # Pago total: captura "X" si se marca
    "Pago total": re.compile(r"Pago\s+total\s*[:\-]?\s*(X)?", re.IGNORECASE),
    # Pago Cuota 1: captura "X" si se marca
    "Pago Cuota 1": re.compile(r"Pago\s+cuota\s+1\s*[:\-]?\s*(X)?", re.IGNORECASE),
    # Pago Cuota 2: captura "X" si se marca
    "Pago Cuota 2": re.compile(r"Pago\s+cuota\s+2\s*[:\-]?\s*(X)?", re.IGNORECASE),
    # Total a pagar: dígitos
    "Total a pagar": re.compile(r"Total\s+a\s+pagar\s*[:\-]?\s*(\d+)", re.IGNORECASE),
    # Fecha de emisión: admite "Fecha de emisión:" o "Fecha emisión:" en formato dd/mm/yyyy
    "Fecha de emisión": re.compile(
        r"Fecha(?:\s+de)?\s+emisi[oó]n\s*[:\-]?\s*(\d{2}\/\d{2}\/\d{4})", re.IGNORECASE
    ),
    # Fecha de vencimiento: admite "Fecha de vencimiento:" o "Fecha vencimiento:" en formato dd/mm/yyyy
    "Fecha de vencimiento": re.compile(
        r"Fecha(?:\s+de)?\s+vencimiento\s*[:\-]?\s*(\d{2}\/\d{2}\/\d{4})", re.IGNORECASE
    ),
    # Forma de Pago: captura una palabra (alfanumérica)
    "Forma de Pago": re.compile(r"Forma\s+de\s+Pago\s*[:\-]?\s*(\w+)", re.IGNORECASE),
}


# ============================================================================
# PATRONES DE VALIDACIÓN
# ============================================================================

PAGOS_PATTERN: dict[str, re.Pattern[str]] = {
    "Pago total": re.compile(r"^(X|No aplica)$", re.IGNORECASE),
    "Pago Cuota 1": re.compile(r"^(X|No aplica)$", re.IGNORECASE),
    "Pago Cuota 2": re.compile(r"^(X|No aplica)$", re.IGNORECASE),
}


def extraer_datos_permiso_circulacion(text: str, return_regex: bool = False) -> dict[str, Any]:
    """
    Extrae los datos del Permiso de Circulación desde el texto extraído del PDF.

    PORTADO LITERALMENTE desde extraerDatosPermisoCirculacion() en permisoCirculacionExtractor.ts

    Args:
        text: Texto extraído del PDF
        return_regex: Si True, retorna también las regex usadas

    Returns:
        Diccionario con:
        - data: los datos extraídos (dict[str, str])
        - regexes: las expresiones regulares usadas (dict[str, str]) si return_regex=True
    """
    # Unificar saltos de línea
    t = re.sub(r"\r?\n|\r", " ", text)

    data: dict[str, str] = {}

    for key, pattern in REGEXES.items():
        data[key] = buscar(t, pattern) or ""

    # Normalización:
    # Si un campo está vacío:
    # - Para "Pago total", "Pago Cuota 1" y "Pago Cuota 2" se asigna "No aplica"
    # - Para los demás se deja como cadena vacía ("")
    for key in data:
        if data[key].strip() == "":
            if key in ["Pago total", "Pago Cuota 1", "Pago Cuota 2"]:
                data[key] = "No aplica"
            else:
                data[key] = ""

    logger.debug("Datos extraídos Permiso de Circulación: %s", data)

    result: dict[str, Any] = {"data": data}

    if return_regex:
        # Convertir regex a strings para serialización
        result["regexes"] = {key: pattern.pattern for key, pattern in REGEXES.items()}

    return result


def best_effort_validation_permiso_circulacion(datos: dict[str, str], file_name: str) -> None:
    """
    Validación "best-effort" para Permiso de Circulación.

    PORTADO LITERALMENTE desde bestEffortValidationPermisoCirculacion() en permisoCirculacionExtractor.ts

    - Para campos obligatorios se requiere que tengan al menos 3 caracteres.
    - Los campos de pago se validan contra su patrón.

    Args:
        datos: Diccionario con los datos extraídos
        file_name: Nombre del archivo para mensajes de error

    Raises:
        ValueError: Si algún campo obligatorio está incompleto o no es válido
    """
    errors: list[str] = []

    # Campos obligatorios (no de pago)
    obligatorios = [
        "Placa Única",
        "Código SII",
        "Valor Permiso",
        "Total a pagar",
        "Fecha de emisión",
        "Fecha de vencimiento",
        "Forma de Pago",
    ]

    for field in obligatorios:
        value = datos.get(field, "")
        if not value or len(value.strip()) < 3:
            errors.append(f'Campo "{field}" es obligatorio y debe tener al menos 3 caracteres.')

    # Validar campos de pago
    pagos = ["Pago total", "Pago Cuota 1", "Pago Cuota 2"]
    for field in pagos:
        value = datos.get(field, "")
        pattern = PAGOS_PATTERN[field]
        if not pattern.match(value):
            errors.append(f'Campo "{field}" con valor "{value}" no es válido.')

    if errors:
        raise ValueError(f"El archivo {file_name} presenta problemas:\n - " + "\n - ".join(errors))


# Orden de columnas para Excel
PERMISO_COLUMN_ORDER = [
    "Nombre PDF",
    "Placa Única",
    "digito verificador",
    "Código SII",
    "Valor Permiso",
    "Pago total",
    "Pago Cuota 1",
    "Pago Cuota 2",
    "Total a pagar",
    "Fecha de emisión",
    "Fecha de vencimiento",
    "Forma de Pago",
]
