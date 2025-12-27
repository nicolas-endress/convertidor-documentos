"""
Extractor CRT - Certificado de Revisión Técnica.

PORTADO LITERALMENTE desde crtExtractor.ts
Mantiene las mismas regex, campos y validaciones.
"""

import logging
import re

logger = logging.getLogger(__name__)


# ============================================================================
# REGEX COMPILADAS (equivalentes exactas a TypeScript)
# ============================================================================

# Campos fijos
REGEX_FECHA_REVISION = re.compile(
    r"FECHA REVISIÓN:\s*(\d{1,2}\s+[A-ZÁÉÍÓÚÑ]+\s+\d{4})", re.IGNORECASE
)

REGEX_PLANTA = re.compile(r"PLANTA:\s*([A-Z0-9-]+)", re.IGNORECASE)

REGEX_PLACA_PATENTE = re.compile(r"PLACA PATENTE\s+([A-Z0-9]+)", re.IGNORECASE)

REGEX_FOLIO = re.compile(r"(N°B\d+)", re.IGNORECASE)

# Secciones de certificados
REGEX_REVISION_SECTION = re.compile(
    r"CERTIFICADO\s+(?:DE\s+)?REVISI[ÓO]N\s+T[EÉ]CNICA([\s\S]*?)(?=CERTIFICADO\s+(?:DE\s+)?(?:EMISIONES\s+)?CONTAMINANTES|$)",
    re.IGNORECASE,
)

REGEX_CONTAMINANTES_SECTION = re.compile(
    r"CERTIFICADO\s+(?:DE\s+)?(?:EMISIONES\s+)?CONTAMINANTES([\s\S]*?)(?=CERTIFICADO\s|$)",
    re.IGNORECASE,
)

# Patrón para "VÁLIDO HASTA" dentro de secciones
REGEX_VALIDO_HASTA = re.compile(
    r"VÁLIDO HASTA(?:\s*FECHA REVISIÓN:)?\s*(?:(\d{1,2}\s+[A-ZÁÉÍÓÚÑ]+\s+\d{4})\s+)?([A-ZÁÉÍÓÚÑ]+\s+\d{4})",
    re.IGNORECASE,
)

# ============================================================================
# PATRONES DE VALIDACIÓN (equivalentes exactos)
# ============================================================================

REQUIRED_PATTERNS = {
    "Fecha de Revisión": re.compile(r"^\d{1,2}\s+[A-ZÁÉÍÓÚÑ]+\s+\d{4}$"),
    "Placa Patente": re.compile(r"^[A-Z0-9]+$"),
    "Planta": re.compile(r"^.+$"),
    "Folio": re.compile(r"^N°B\d+$", re.IGNORECASE),
}

OPTIONAL_PATTERNS = {
    "Válido Hasta Revisión Técnica": re.compile(r"^[A-ZÁÉÍÓÚÑ]+\s+\d{4}$", re.IGNORECASE),
    "Válido Hasta Contaminantes": re.compile(r"^[A-ZÁÉÍÓÚÑ]+\s+\d{4}$", re.IGNORECASE),
}


def extraer_datos_crt(text: str) -> dict[str, str]:
    """
    Extrae los datos CRT del texto del PDF.

    PORTADO LITERALMENTE desde extraerDatosCRT() en crtExtractor.ts

    Acepta PDFs con uno o ambos certificados:
    - Solo Certificado de Revisión Técnica
    - Solo Certificado de Emisiones Contaminantes
    - Ambos certificados

    Args:
        text: Texto extraído del PDF

    Returns:
        Diccionario con todos los campos extraídos

    Raises:
        ValueError: Si no se encuentra ningún certificado válido
    """
    datos: dict[str, str] = {}
    logger.info("Iniciando extracción de datos CRT")

    # Extracción de campos fijos (comunes a todos los certificados)
    fecha_match = REGEX_FECHA_REVISION.search(text)
    datos["Fecha de Revisión"] = fecha_match.group(1).strip() if fecha_match else ""
    logger.info(f"Fecha de Revisión extraída: {datos['Fecha de Revisión']}")

    planta_match = REGEX_PLANTA.search(text)
    datos["Planta"] = planta_match.group(1).strip() if planta_match else ""
    logger.info(f"Planta extraída: {datos['Planta']}")

    placa_match = REGEX_PLACA_PATENTE.search(text)
    datos["Placa Patente"] = placa_match.group(1).strip() if placa_match else ""
    logger.info(f"Placa Patente extraída: {datos['Placa Patente']}")

    # Separación de secciones
    revision_section_match = REGEX_REVISION_SECTION.search(text)
    contaminantes_section_match = REGEX_CONTAMINANTES_SECTION.search(text)

    # Inicializar campos "Válido Hasta" como vacíos
    datos["Válido Hasta Revisión Técnica"] = ""
    datos["Válido Hasta Contaminantes"] = ""

    # Procesar sección de Revisión Técnica si existe
    if revision_section_match:
        revision_section = revision_section_match.group(1)
        valido_revision_match = REGEX_VALIDO_HASTA.search(revision_section)

        if valido_revision_match:
            datos["Válido Hasta Revisión Técnica"] = (
                valido_revision_match.group(2) or valido_revision_match.group(1) or ""
            ).strip()
            logger.info(
                f"Válido Hasta Revisión Técnica extraído: {datos['Válido Hasta Revisión Técnica']}"
            )
        else:
            logger.info("No se encontró 'VÁLIDO HASTA' en la sección de Revisión Técnica")
    else:
        logger.info("No se encontró la sección de Certificado de Revisión Técnica")

    # Procesar sección de Contaminantes si existe
    if contaminantes_section_match:
        contaminantes_section = contaminantes_section_match.group(1)
        valido_contaminantes_match = REGEX_VALIDO_HASTA.search(contaminantes_section)

        if valido_contaminantes_match:
            datos["Válido Hasta Contaminantes"] = (
                valido_contaminantes_match.group(2) or valido_contaminantes_match.group(1) or ""
            ).strip()
            logger.info(
                f"Válido Hasta Contaminantes extraído: {datos['Válido Hasta Contaminantes']}"
            )
        else:
            logger.info("No se encontró 'VÁLIDO HASTA' en la sección de Contaminantes")
    else:
        logger.info("No se encontró la sección de Certificado de Contaminantes")

    # Validar que al menos uno de los certificados esté presente
    if not revision_section_match and not contaminantes_section_match:
        raise ValueError(
            "El PDF no contiene ningún certificado válido (Revisión Técnica o Emisiones Contaminantes)."
        )

    # Extraer folio (debe quedar al final)
    folio_match = REGEX_FOLIO.search(text)
    datos["Folio"] = folio_match.group(1).strip() if folio_match else ""
    logger.info(f"Folio extraído: {datos['Folio']}")

    return datos


def best_effort_validation_crt(datos: dict[str, str], file_name: str) -> None:
    """
    Valida que los datos extraídos cumplan con los formatos esperados para CRT.

    PORTADO LITERALMENTE desde bestEffortValidationCRT() en crtExtractor.ts

    Validación flexible que acepta uno o ambos certificados.

    Args:
        datos: Diccionario con los datos extraídos
        file_name: Nombre del archivo para mensajes de error

    Raises:
        ValueError: Si falta algún campo obligatorio o su formato no coincide
    """
    logger.info(f"Iniciando validación de datos CRT para el archivo: {file_name}")

    errors: list[str] = []

    # Validar campos obligatorios
    for field, pattern in REQUIRED_PATTERNS.items():
        value = datos.get(field, "")
        if not value:
            errors.append(f'Falta el campo obligatorio "{field}".')
            logger.info(f'Validación: Falta el campo obligatorio "{field}".')
        elif not pattern.match(value):
            errors.append(
                f'Campo "{field}" con valor "{value}" no coincide con el formato esperado.'
            )
            logger.info(
                f'Validación: Campo "{field}" con valor "{value}" no coincide con el formato esperado.'
            )
        else:
            logger.info(f'Validación: Campo "{field}" con valor "{value}" es correcto.')

    # Validar campos opcionales solo si están presentes
    for field, pattern in OPTIONAL_PATTERNS.items():
        value = datos.get(field, "")
        if value:  # Solo validar si el campo tiene valor
            if not pattern.match(value):
                errors.append(
                    f'Campo "{field}" con valor "{value}" no coincide con el formato esperado.'
                )
                logger.info(
                    f'Validación: Campo "{field}" con valor "{value}" no coincide con el formato esperado.'
                )
            else:
                logger.info(f'Validación: Campo "{field}" con valor "{value}" es correcto.')
        else:
            logger.info(f'Validación: Campo "{field}" está vacío (certificado no presente).')

    # Verificar que al menos uno de los campos "Válido Hasta" esté presente
    has_revision_tecnica = bool(datos.get("Válido Hasta Revisión Técnica", "").strip())
    has_contaminantes = bool(datos.get("Válido Hasta Contaminantes", "").strip())

    if not has_revision_tecnica and not has_contaminantes:
        errors.append(
            'Debe haber al menos uno de los campos "Válido Hasta Revisión Técnica" o "Válido Hasta Contaminantes".'
        )
        logger.info(
            'Validación: Falta al menos uno de los campos "Válido Hasta" (Revisión Técnica o Contaminantes).'
        )

    if errors:
        raise ValueError(
            f"El archivo {file_name} presenta problemas en los datos:\n - " + "\n - ".join(errors)
        )

    logger.info("Validación completada exitosamente.")


# Orden de columnas para Excel (equivalente a headers en TypeScript)
CRT_COLUMN_ORDER = [
    "Nombre PDF",
    "Fecha de Revisión",
    "Planta",
    "Placa Patente",
    "Válido Hasta Revisión Técnica",
    "Válido Hasta Contaminantes",
    "Folio",
]
