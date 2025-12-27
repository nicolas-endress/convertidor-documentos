"""
Extractor Homologación - Certificado de Homologación.

PORTADO LITERALMENTE desde homologacionExtractor.ts
Mantiene las mismas regex, campos y validaciones.
"""

import logging
import re

from ..utils.text_utils import buscar

logger = logging.getLogger(__name__)


# ============================================================================
# REGEX COMPILADAS (equivalentes exactas a TypeScript)
# ============================================================================

REGEX_FECHA_EMISION = re.compile(r"FECHA DE EMISIÓN\s+([0-9A-Z\/]+)", re.IGNORECASE)
REGEX_N_CORRELATIVO = re.compile(r"N[°º]\s*CORRELATIVO\s+([A-Z0-9\-]+)", re.IGNORECASE)
REGEX_CODIGO_INFORME = re.compile(r"CÓDIGO DE INFORME TÉCNICO\s+([A-Z0-9\-]+)", re.IGNORECASE)
REGEX_PATENTE = re.compile(r"PATENTE\s+([A-Z0-9\-]+)", re.IGNORECASE)
REGEX_VALIDO_HASTA = re.compile(r"VÁLIDO HASTA\s+([0-9A-Z\/]+)", re.IGNORECASE)
REGEX_TIPO_VEHICULO = re.compile(r"TIPO DE VEHÍCULO\s+([A-ZÑ]+)", re.IGNORECASE)
REGEX_MARCA = re.compile(r"MARCA\s+([A-Z]+)", re.IGNORECASE)
REGEX_ANO = re.compile(r"AÑO\s+([0-9]{4})", re.IGNORECASE)
# Modificado: usar re.DOTALL para permitir saltos de línea entre MODELO y COLOR
REGEX_MODELO = re.compile(r"MODELO\s+(.+?)\s+COLOR", re.IGNORECASE | re.DOTALL)
REGEX_COLOR = re.compile(r"COLOR\s+([A-Z\s\(\)0-9\.\-]+?)(?=\s+VIN\b|$)", re.IGNORECASE)
REGEX_VIN = re.compile(r"VIN\s+([A-Z0-9]+)", re.IGNORECASE)
REGEX_N_MOTOR = re.compile(r"N[°º]\s*MOTOR\s+([A-Z0-9]+(?:\s+[A-Z0-9]+)?)", re.IGNORECASE)
REGEX_FIRMADO_POR = re.compile(r"Firmado por:\s+(.+?)(?=\s+AUDITORÍA|\r?\n|$)", re.IGNORECASE)

# ============================================================================
# PATRONES DE VALIDACIÓN (equivalentes exactos)
# ============================================================================

EXPECTED_PATTERNS = {
    "Fecha de Emisión": re.compile(r"^\d{1,2}\/[A-Z]{3}\/\d{4}$"),
    "Nº Correlativo": re.compile(r"^[A-Z0-9\-]+$"),
    "Código Informe Técnico": re.compile(r"^[A-Z0-9\-]+$"),
    # Patente debe ser exactamente 6 caracteres alfanuméricos (sin guiones ni espacios)
    "Patente": re.compile(r"^[A-Z0-9]{6}$", re.IGNORECASE),
    "Válido Hasta": re.compile(r"^[A-Z]{3}\/\d{4}$"),
    "Tipo de Vehículo": re.compile(r"^[A-ZÑ]+$"),
    "Marca": re.compile(r"^[A-Z]+$"),
    "Año": re.compile(r"^\d{4}$"),
    "Modelo": re.compile(r"^.+$"),
    "Color": re.compile(r"^[A-Z\s\(\)0-9\.\-]+\.?$"),
    "VIN": re.compile(r"^[A-Z0-9]+$"),
    "Nº Motor": re.compile(r"^[A-Z0-9 ]+(?:\s*[A-Za-z]+)?$"),
    "Firmado por": re.compile(r"^.+$"),
}


def _limpiar_patente(value: str) -> str:
    """
    Limpia la patente eliminando guiones y espacios.
    Si el resultado es mayor a 6 caracteres, toma solo los primeros 6.

    Equivalente exacto de la IIFE en TypeScript para "Patente".
    """
    cleaned = value.replace("-", "").replace(" ", "").strip()
    return cleaned[:6] if len(cleaned) > 6 else cleaned


def _limpiar_motor(value: str) -> str:
    """
    Limpia el número de motor eliminando sufijos como " C" o " El".

    Equivalente exacto de la IIFE en TypeScript para "Nº Motor".
    """
    return re.sub(r"\s+(C|El)$", "", value, flags=re.IGNORECASE).strip()


def _limpiar_firmado(value: str) -> str:
    """
    Limpia el campo "Firmado por" eliminando fechas.

    Equivalente exacto de la IIFE en TypeScript para "Firmado por".
    """
    match = re.search(r"\d{2}\/\d{2}\/\d{4}", value)
    if match:
        return value.split(match.group())[0].strip()
    return value.strip()


def _limpiar_modelo(value: str) -> str:
    """
    Limpia el campo "Modelo" eliminando saltos de línea y espacios múltiples.

    PyMuPDF puede extraer texto con saltos de línea que pdf2json no tiene.
    """
    # Reemplazar saltos de línea y espacios múltiples por un solo espacio
    cleaned = re.sub(r"\s+", " ", value)
    return cleaned.strip()


def extraer_datos_homologacion(text: str) -> dict[str, str]:
    """
    Extrae los datos de Homologación del texto del PDF.

    PORTADO LITERALMENTE desde extraerDatosHomologacion() en homologacionExtractor.ts

    Args:
        text: Texto extraído del PDF

    Returns:
        Diccionario con todos los campos extraídos
    """
    # Extraer Patente y limpiar
    patente_raw = buscar(text, REGEX_PATENTE) or ""
    patente = _limpiar_patente(patente_raw)

    # Extraer Nº Motor y limpiar
    motor_raw = buscar(text, REGEX_N_MOTOR) or ""
    motor = _limpiar_motor(motor_raw)

    # Extraer Firmado por y limpiar
    firmado_raw = buscar(text, REGEX_FIRMADO_POR) or ""
    firmado = _limpiar_firmado(firmado_raw)

    # Extraer Modelo y limpiar (puede tener saltos de línea)
    modelo_raw = buscar(text, REGEX_MODELO) or ""
    modelo = _limpiar_modelo(modelo_raw)

    return {
        "Fecha de Emisión": buscar(text, REGEX_FECHA_EMISION) or "",
        "Nº Correlativo": buscar(text, REGEX_N_CORRELATIVO) or "",
        "Código Informe Técnico": buscar(text, REGEX_CODIGO_INFORME) or "",
        "Patente": patente,
        "Válido Hasta": buscar(text, REGEX_VALIDO_HASTA) or "",
        "Tipo de Vehículo": buscar(text, REGEX_TIPO_VEHICULO) or "",
        "Marca": buscar(text, REGEX_MARCA) or "",
        "Año": buscar(text, REGEX_ANO) or "",
        "Modelo": modelo,
        "Color": buscar(text, REGEX_COLOR) or "",
        "VIN": buscar(text, REGEX_VIN) or "",
        "Nº Motor": motor,
        "Firmado por": firmado,
    }


def best_effort_validation_homologacion(datos: dict[str, str], file_name: str) -> None:
    """
    Valida que los datos extraídos cumplan con los formatos esperados para Homologación.

    PORTADO LITERALMENTE desde bestEffortValidationHomologacion() en homologacionExtractor.ts

    Args:
        datos: Diccionario con los datos extraídos
        file_name: Nombre del archivo para mensajes de error

    Raises:
        ValueError: Si falta algún campo o su formato no coincide
    """
    errors: list[str] = []

    for field, pattern in EXPECTED_PATTERNS.items():
        value = datos.get(field, "")
        if not value:
            errors.append(f'Falta el campo "{field}".')
        elif not pattern.match(value.strip()):
            errors.append(
                f'Campo "{field}" con valor "{value}" no coincide con el formato esperado.'
            )

    if errors:
        raise ValueError(
            f"El archivo {file_name} presenta problemas en los datos:\n - " + "\n - ".join(errors)
        )


# Orden de columnas para Excel
HOMOLOGACION_COLUMN_ORDER = [
    "Nombre PDF",
    "Patente",
    "Fecha de Emisión",
    "Nº Correlativo",
    "Código Informe Técnico",
    "Válido Hasta",
    "Tipo de Vehículo",
    "Marca",
    "Año",
    "Modelo",
    "Color",
    "VIN",
    "Nº Motor",
    "Firmado por",
]
