"""
PDF Processor Service - Utilidades de texto.

Funciones equivalentes a las de TypeScript para mantener compatibilidad.
"""

import re
import unicodedata
from re import Pattern


def buscar(text: str, pattern: Pattern[str]) -> str | None:
    """
    Busca en el texto la primera coincidencia del patrón y retorna el grupo 1.

    Equivalente exacto de la función buscar() en pdfUtils.ts

    Args:
        text: Texto en el cual buscar
        pattern: Patrón compilado a buscar

    Returns:
        Cadena encontrada (grupo 1) o None
    """
    match = pattern.search(text)
    if match and match.group(1):
        return match.group(1).strip()
    return None


def sanitizar_nombre(text: str) -> str:
    """
    Sanitiza un nombre eliminando acentos y caracteres especiales.

    Equivalente exacto de sanitizarNombre() en pdfUtils.ts

    Args:
        text: Cadena de entrada

    Returns:
        Cadena sanitizada
    """
    # Normalizar NFD y eliminar marcas diacríticas
    normalized = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")

    # Reemplazar caracteres no permitidos con _
    # Equivalente a: /[^\p{L}\p{N}\s\-_().]/gu
    sanitized = re.sub(r"[^\w\s\-_().]", "_", without_accents, flags=re.UNICODE)
    sanitized = sanitized.strip()

    # Eliminar " A" al final (caso específico del sistema original)
    sanitized = re.sub(r"\s+A$", "", sanitized)

    return sanitized


def normalize_plate_with_check(value: str) -> tuple[str, str | None]:
    """
    Normaliza un valor de placa o similar eliminando guiones y espacios.

    Equivalente exacto de normalizePlateWithCheck() en excelUtils.ts

    Si el resultado tiene:
    - EXACTAMENTE 6 caracteres: se toma tal cual (no hay dígito verificador)
    - Más de 6 caracteres: los primeros 6 son la patente, el resto es dígito verificador

    Args:
        value: Valor de placa (ej: "LXWJ75-4", "LXW-J75-4", "THJL54")

    Returns:
        Tupla (plate, check_digit) donde check_digit puede ser None

    Examples:
        >>> normalize_plate_with_check("LXWJ75-4")
        ("LXWJ75", "4")
        >>> normalize_plate_with_check("THJL54")
        ("THJL54", None)
    """
    # Eliminar todos los guiones y espacios
    cleaned = value.replace("-", "").replace(" ", "")

    if len(cleaned) > 6:
        return (cleaned[:6], cleaned[6:])
    return (cleaned, None)


def strip_html_tags(html_string: str) -> str:
    """
    Elimina etiquetas HTML de un string.

    Equivalente exacto de stripHtmlTags() en excelUtils.ts

    Args:
        html_string: Valor que puede contener HTML

    Returns:
        Cadena limpia sin etiquetas HTML
    """
    return re.sub(r"<[^>]*>", "", html_string)


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Genera un nombre de archivo seguro para evitar path traversal.

    Args:
        filename: Nombre de archivo original
        max_length: Longitud máxima permitida

    Returns:
        Nombre de archivo seguro
    """
    import os

    # Obtener solo el nombre base (sin path)
    safe = os.path.basename(filename)

    # Eliminar .. y otros caracteres peligrosos
    safe = safe.replace("..", "")
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", safe)

    # Truncar si es muy largo
    if len(safe) > max_length:
        name, ext = os.path.splitext(safe)
        safe = name[: max_length - len(ext)] + ext

    return safe or "unnamed"
