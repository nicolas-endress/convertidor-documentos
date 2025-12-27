"""
Extractor SOAP - Seguro Obligatorio de Accidentes Personales.

PORTADO LITERALMENTE desde soapExtractor.ts
Mantiene las mismas regex, campos y validaciones.
"""

import logging
import re

from ..utils.text_utils import buscar

logger = logging.getLogger(__name__)


# ============================================================================
# REGEX COMPILADAS (equivalentes exactas a TypeScript)
# ============================================================================

# INSCRIPCION R.V.M: Ejemplo esperado: "TWGV11 - 7" (se permite espacio alrededor del guion)
REGEX_INSCRIPCION_RVM = re.compile(
    r"INSCRIPC[ÍI]ON\s*R\s*\.?\s*V\s*\.?\s*M\s*\.?\s*(?::|\-)?\s*([A-Z0-9]+\s*-\s*[A-Z0-9]+)",
    re.IGNORECASE,
)

# Bajo el código
REGEX_BAJO_CODIGO = re.compile(r"Bajo\s+el\s+c[óo]digo\s*[:\-]?\s*([A-Z0-9\-]+)", re.IGNORECASE)

# RUT: Captura números con o sin puntos, seguidos de guion y dígito o k/K
REGEX_RUT = re.compile(
    r"RUT\s*[:\-]?\s*((?:\d{1,3}(?:\.\d{3})+)|\d{7,8})\s*[-]\s*([0-9kK])", re.IGNORECASE
)

# Fecha de inicio del seguro
REGEX_RIGE_DESDE = re.compile(r"RIGE\s+DESDE\s*[:\-]?\s*(\d{2}[-/]\d{2}[-/]\d{4})", re.IGNORECASE)

# Fecha de finalización del seguro
REGEX_HASTA = re.compile(r"HAST(?:\s*A)?\s*[:\-]?\s*(\d{2}[-/]\d{2}[-/]\d{4})", re.IGNORECASE)

# Número de póliza: acepta números, guiones y letras (ej: 6297613-M o 123906245-4)
REGEX_POLIZA = re.compile(
    r"POLI[ZS]A\s*N[°º]?\s*[:\-]?\s*([A-Z0-9]+\s*-\s*[A-Z0-9]+)", re.IGNORECASE
)

# Prima del seguro
REGEX_PRIMA = re.compile(r"PRIMA\s*[:\-]?\s*([\d\.]+)", re.IGNORECASE)

# ============================================================================
# PATRONES DE VALIDACIÓN (equivalentes exactos)
# ============================================================================

EXPECTED_PATTERNS = {
    # Inscripción R.V.M: al menos 6 caracteres alfanuméricos antes del guion,
    # espacios opcionales y luego un guion seguido de un único carácter
    "INSCRIPCION R.V.M": re.compile(r"^[A-Z0-9]{6,}\s*-\s*[A-Z0-9]$", re.IGNORECASE),
    "Bajo el codigo": re.compile(r"^[A-Z0-9\-]+$"),
    "RUT": re.compile(r"^(?:\d{7,8}|(?:\d{1,3}(?:\.\d{3})+))-[0-9kK]$"),
    "RIGE DESDE": re.compile(r"^\d{2}[-/]\d{2}[-/]\d{4}$"),
    "HASTA": re.compile(r"^\d{2}[-/]\d{2}[-/]\d{4}$"),
    # POLIZA N°: 6-9 dígitos, guion, letra/dígito
    "POLIZA N°": re.compile(r"^\d{6,9}-[A-Z0-9]$", re.IGNORECASE),
    "PRIMA": re.compile(r"^[\d\.]+$"),
}


def extraer_datos_soap_simplificado(text: str) -> dict[str, str]:
    """
    Extrae los datos SOAP del texto del PDF.

    PORTADO LITERALMENTE desde extraerDatosSoapSimplificado() en soapExtractor.ts

    Se han ajustado las expresiones regulares para permitir espacios, puntos y guiones
    opcionales en campos críticos como INSCRIPCION R.V.M y RUT.

    Args:
        text: Texto extraído del PDF

    Returns:
        Diccionario con todos los campos extraídos
    """
    # Normalizar saltos de línea
    t = re.sub(r"\r?\n|\r", " ", text)

    # INSCRIPCION R.V.M
    inscripcion = (buscar(t, REGEX_INSCRIPCION_RVM) or "").strip()

    # Bajo el código
    bajo_codigo = (buscar(t, REGEX_BAJO_CODIGO) or "").strip()

    # RUT: Extraer y normalizar
    rut_match = REGEX_RUT.search(t)
    if rut_match:
        # Eliminar puntos y espacios del RUT
        rut_num = rut_match.group(1).replace(".", "").replace(" ", "")
        rut_dv = rut_match.group(2)
        rut = f"{rut_num}-{rut_dv}"
    else:
        rut = ""

    # RIGE DESDE
    rige_desde = (buscar(t, REGEX_RIGE_DESDE) or "").strip()

    # HASTA
    hasta = (buscar(t, REGEX_HASTA) or "").strip()

    # POLIZA N°: Normalizar espacios alrededor del guion
    poliza_raw = (buscar(t, REGEX_POLIZA) or "").strip()
    poliza = re.sub(r"\s*-\s*", "-", poliza_raw)  # Normaliza espacios alrededor del guion

    # PRIMA
    prima = (buscar(t, REGEX_PRIMA) or "").strip()

    data = {
        "INSCRIPCION R.V.M": inscripcion,
        "Bajo el codigo": bajo_codigo,
        "RUT": rut,
        "RIGE DESDE": rige_desde,
        "HASTA": hasta,
        "POLIZA N°": poliza,
        "PRIMA": prima,
    }

    logger.debug("Datos extraídos SOAP Simplificado (flexible): %s", data)
    return data


def best_effort_validation_soap(datos: dict[str, str], file_name: str) -> None:
    """
    Validación estricta para SOAP.

    PORTADO LITERALMENTE desde bestEffortValidationSoap() en soapExtractor.ts

    Si la póliza no cumple el patrón esperado, la fila se descarta (lanza error).

    Args:
        datos: Diccionario con los datos extraídos
        file_name: Nombre del archivo para mensajes de error

    Raises:
        ValueError: Si algún campo está incompleto o no coincide con el formato esperado
    """
    errors: list[str] = []

    for field, pattern in EXPECTED_PATTERNS.items():
        value = datos.get(field, "")
        if not value or len(value.strip()) < 3:
            errors.append(f'El campo "{field}" está incompleto (menos de 3 caracteres).')
        elif not pattern.match(value):
            errors.append(
                f'El campo "{field}" con valor "{value}" no coincide con el formato esperado.'
            )

    if errors:
        raise ValueError(
            f"El archivo {file_name} presenta problemas en los datos:\n - " + "\n - ".join(errors)
        )


# Orden de columnas para Excel
SOAP_COLUMN_ORDER = [
    "Nombre PDF",
    "INSCRIPCION R.V.M",
    "digito verificador",
    "Bajo el codigo",
    "RUT",
    "RIGE DESDE",
    "HASTA",
    "POLIZA N°",
    "PRIMA",
]
