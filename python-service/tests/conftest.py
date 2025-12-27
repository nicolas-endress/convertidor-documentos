"""
conftest.py - Configuración global de pytest para el proyecto.
"""

import sys
from pathlib import Path

import pytest

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(scope="session")
def sample_texts():
    """Textos de ejemplo para todos los formatos de PDF."""
    return {
        "crt": """
            CERTIFICADO REVISIÓN TÉCNICA
            FECHA REVISIÓN: 15 ENERO 2024
            PLACA PATENTE: ABCD12
            PLANTA: PLANTA REVISIÓN TÉCNICA 001
            Nº DE CERTIFICADO: 123456
            Válido hasta Revisión Técnica: 31/12/2024
            Válido hasta Emisiones: 31/12/2024

            CERTIFICADO EMISIONES CONTAMINANTES
            FECHA REVISIÓN: 15 ENERO 2024
            PLACA PATENTE: ABCD12
            PLANTA: PLANTA REVISIÓN TÉCNICA 001
            Nº DE CERTIFICADO: 789012
        """,
        "homologacion": """
            CERTIFICADO DE HOMOLOGACION
            PATENTE LXWJ754
            MARCA TOYOTA
            MODELO COROLLA
            AÑO 2022
            TIPO AUTOMOVIL
            VIN 1HGBH41JXMN109186
            MOTOR 2ZR1234567
            COLOR BLANCO
            Nº Serie 12345
            Firmado por: Juan Pérez - 15/01/2024
        """,
        "soap": """
            SEGURO OBLIGATORIO ACCIDENTES PERSONALES
            INSCRIPCION R.V.M: TWGV11 - 7
            Bajo el código: ABC-123-XYZ
            RUT: 12.345.678-9
            RIGE DESDE: 01/01/2024
            HASTA: 31/12/2024
            POLIZA Nº: 6297613 - M
            PRIMA: 45000
        """,
        "permiso_circulacion": """
            PERMISO DE CIRCULACION
            Patente: ABCD12-3
            Nº CERTIFICADO: 123456789
            PPU: WXYZ99
            Fecha emisión: 01/01/2024
            Nº Documento pago: DOC-2024-001
            TOTAL PAGADO: $125.000
            MULTA: $5.000
        """,
    }


@pytest.fixture(scope="session")
def invalid_texts():
    """Textos que deberían fallar la validación."""
    return {
        "crt_incompleto": """
            CERTIFICADO REVISIÓN TÉCNICA
            FECHA REVISIÓN: 15 ENERO 2024
            # Falta PLACA PATENTE y otros campos
        """,
        "soap_rut_invalido": """
            RUT: 12
            POLIZA: ABC
        """,
    }


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Directorio temporal para PDFs de prueba."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir
