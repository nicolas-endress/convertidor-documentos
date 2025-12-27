"""
PDF Processor Service - Logger estructurado.

Usa logging estándar de Python. Si structlog está disponible,
se puede usar para logging estructurado en JSON.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# Intentar importar structlog si está disponible
_structlog: Any = None
_structlog_available = False

try:
    import structlog as _structlog_module  # type: ignore[import-not-found]

    _structlog = _structlog_module
    _structlog_available = True
except ImportError:
    pass

# Importación tardía de settings para evitar circular imports
_settings_loaded = False
_log_level = "INFO"


def _get_settings_log_level() -> str:
    """Obtiene el nivel de log de settings de forma lazy."""
    global _settings_loaded, _log_level
    if not _settings_loaded:
        try:
            from ..config import settings

            _log_level = settings.LOG_LEVEL
        except ImportError:
            pass
        _settings_loaded = True
    return _log_level


def setup_logging() -> None:
    """Configura el logging estructurado."""
    log_level_str = _get_settings_log_level()
    log_level = getattr(logging, log_level_str, logging.INFO)

    if _structlog_available and _structlog is not None:
        # Procesadores de structlog
        processors: list[Any] = [
            _structlog.contextvars.merge_contextvars,
            _structlog.processors.add_log_level,
            _structlog.processors.TimeStamper(fmt="iso"),
            _structlog.processors.StackInfoRenderer(),
            _structlog.processors.format_exc_info,
        ]

        # En desarrollo, usar formato legible; en producción, JSON
        if log_level_str == "DEBUG":
            processors.append(_structlog.dev.ConsoleRenderer(colors=True))
        else:
            processors.append(_structlog.processors.JSONRenderer())

        _structlog.configure(
            processors=processors,
            wrapper_class=_structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=_structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configurar logging estándar
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Obtiene un logger con contexto.

    Args:
        name: Nombre del módulo

    Returns:
        Logger (structlog si está disponible, sino logging estándar)
    """
    if _structlog_available and _structlog is not None:
        return _structlog.get_logger(name)  # type: ignore[return-value]
    return logging.getLogger(name)


# Logger por defecto
logger: logging.Logger = get_logger("pdf-processor")
