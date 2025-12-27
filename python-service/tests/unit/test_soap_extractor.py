"""
Tests unitarios para SOAP Extractor.
"""

import pytest

from app.extractors.soap_extractor import (
    best_effort_validation_soap,
    extraer_datos_soap_simplificado,
)


class TestSOAPExtractor:
    """Tests para el extractor SOAP."""

    def test_extrae_datos_completos(self):
        """Test de extracción completa."""
        text = """
        INSCRIPCION R.V.M: TWGV11 - 7
        Bajo el código: ABC-123-XYZ
        RUT: 12.345.678-9
        RIGE DESDE: 01/01/2024
        HASTA: 31/12/2024
        POLIZA Nº: 6297613-M
        PRIMA: 45000
        """
        datos = extraer_datos_soap_simplificado(text)

        assert datos["INSCRIPCION R.V.M"] == "TWGV11 - 7"
        assert datos["Bajo el codigo"] == "ABC-123-XYZ"
        # RUT debe normalizarse (sin puntos)
        assert datos["RUT"] == "12345678-9"
        assert datos["RIGE DESDE"] == "01/01/2024"
        assert datos["HASTA"] == "31/12/2024"
        # Póliza debe normalizarse (sin espacios alrededor del guion)
        assert datos["POLIZA N°"] == "6297613-M"
        assert datos["PRIMA"] == "45000"

    def test_normaliza_rut_sin_puntos(self):
        """Test que el RUT se normaliza sin puntos."""
        text = """
        RUT: 12345678-K
        """
        datos = extraer_datos_soap_simplificado(text)
        assert datos["RUT"] == "12345678-K"

    def test_normaliza_rut_con_puntos(self):
        """Test que el RUT con puntos se normaliza."""
        text = """
        RUT: 12.345.678-K
        """
        datos = extraer_datos_soap_simplificado(text)
        assert datos["RUT"] == "12345678-K"

    def test_normaliza_poliza_con_espacios(self):
        """Test que la póliza se normaliza sin espacios."""
        text = """
        POLIZA Nº: 6297613 - M
        """
        datos = extraer_datos_soap_simplificado(text)
        assert datos["POLIZA N°"] == "6297613-M"

    def test_inscripcion_variantes(self):
        """Test de variantes de INSCRIPCION R.V.M."""
        # El regex espera el formato específico con guion separador
        text = "INSCRIPCION R.V.M: ABCD12 - 3"
        datos = extraer_datos_soap_simplificado(text)
        # La inscripción se extrae con espacios alrededor del guion
        assert "ABCD12" in datos["INSCRIPCION R.V.M"]

    def test_inscripcion_con_punto(self):
        """Test con puntos en R.V.M."""
        # El regex espera INSCRIPCION con o sin tilde y puntos en R.V.M.
        text = "INSCRIPCION R.V.M: WXYZ99 - K"
        datos = extraer_datos_soap_simplificado(text)
        assert "WXYZ99" in datos["INSCRIPCION R.V.M"]

    def test_validacion_exitosa(self):
        """Test de validación exitosa."""
        datos = {
            "INSCRIPCION R.V.M": "TWGV11-7",
            "Bajo el codigo": "ABC123",
            "RUT": "12345678-9",
            "RIGE DESDE": "01/01/2024",
            "HASTA": "31/12/2024",
            "POLIZA N°": "6297613-M",
            "PRIMA": "45000",
        }
        # No debe lanzar excepción
        best_effort_validation_soap(datos, "test.pdf")

    def test_validacion_falla_poliza_incorrecta(self):
        """Test de validación con póliza incorrecta."""
        datos = {
            "INSCRIPCION R.V.M": "TWGV11-7",
            "Bajo el codigo": "ABC123",
            "RUT": "12345678-9",
            "RIGE DESDE": "01/01/2024",
            "HASTA": "31/12/2024",
            "POLIZA N°": "123",  # Muy corta
            "PRIMA": "45000",
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_soap(datos, "test.pdf")

        assert "POLIZA" in str(exc_info.value)

    def test_validacion_falla_rut_incompleto(self):
        """Test de validación con RUT incompleto."""
        datos = {
            "INSCRIPCION R.V.M": "TWGV11-7",
            "Bajo el codigo": "ABC123",
            "RUT": "12",  # Muy corto
            "RIGE DESDE": "01/01/2024",
            "HASTA": "31/12/2024",
            "POLIZA N°": "6297613-M",
            "PRIMA": "45000",
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_soap(datos, "test.pdf")

        assert "RUT" in str(exc_info.value)
