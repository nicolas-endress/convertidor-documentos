"""
Tests unitarios para CRT Extractor.

Verifica que las regex y validaciones produzcan el mismo output que TypeScript.
"""

import pytest

from app.extractors.crt_extractor import (
    REGEX_FECHA_REVISION,
    REGEX_PLACA_PATENTE,
    REGEX_PLANTA,
    best_effort_validation_crt,
    extraer_datos_crt,
)


class TestCRTExtractor:
    """Tests para el extractor CRT."""

    def test_extrae_fecha_revision(self):
        """Verifica extracción de fecha de revisión."""
        text = "FECHA REVISIÓN: 15 DICIEMBRE 2024 algo más"
        match = REGEX_FECHA_REVISION.search(text)
        assert match is not None
        assert match.group(1).strip() == "15 DICIEMBRE 2024"

    def test_extrae_fecha_revision_con_espacios(self):
        """Verifica extracción con espacios variados."""
        text = "FECHA REVISIÓN:   5 ENERO 2025  "
        match = REGEX_FECHA_REVISION.search(text)
        assert match is not None
        assert match.group(1).strip() == "5 ENERO 2025"

    def test_extrae_planta(self):
        """Verifica extracción de planta."""
        text = "PLANTA: SGS-001 más texto"
        match = REGEX_PLANTA.search(text)
        assert match is not None
        assert match.group(1).strip() == "SGS-001"

    def test_extrae_placa_patente(self):
        """Verifica extracción de placa patente."""
        text = "PLACA PATENTE ABCD12 resto"
        match = REGEX_PLACA_PATENTE.search(text)
        assert match is not None
        assert match.group(1).strip() == "ABCD12"

    def test_extraer_datos_crt_completo(self):
        """Test de extracción completa con ambos certificados."""
        text = """
        FECHA REVISIÓN: 15 DICIEMBRE 2024
        PLANTA: SGS-001
        PLACA PATENTE ABCD12
        CERTIFICADO DE REVISIÓN TÉCNICA
        VÁLIDO HASTA DICIEMBRE 2025
        CERTIFICADO DE EMISIONES CONTAMINANTES
        VÁLIDO HASTA JUNIO 2025
        N°B123456
        """
        datos = extraer_datos_crt(text)

        assert datos["Fecha de Revisión"] == "15 DICIEMBRE 2024"
        assert datos["Planta"] == "SGS-001"
        assert datos["Placa Patente"] == "ABCD12"
        assert datos["Válido Hasta Revisión Técnica"] == "DICIEMBRE 2025"
        assert datos["Válido Hasta Contaminantes"] == "JUNIO 2025"
        assert datos["Folio"] == "N°B123456"

    def test_extraer_datos_crt_solo_revision_tecnica(self):
        """Test con solo certificado de revisión técnica."""
        text = """
        FECHA REVISIÓN: 10 MARZO 2024
        PLANTA: DEKRA-002
        PLACA PATENTE WXYZ99
        CERTIFICADO DE REVISIÓN TÉCNICA
        VÁLIDO HASTA MARZO 2025
        N°B654321
        """
        datos = extraer_datos_crt(text)

        assert datos["Fecha de Revisión"] == "10 MARZO 2024"
        assert datos["Válido Hasta Revisión Técnica"] == "MARZO 2025"
        assert datos["Válido Hasta Contaminantes"] == ""

    def test_extraer_datos_crt_solo_contaminantes(self):
        """Test con solo certificado de contaminantes."""
        text = """
        FECHA REVISIÓN: 20 JULIO 2024
        PLANTA: TUV-003
        PLACA PATENTE QWER88
        CERTIFICADO DE EMISIONES CONTAMINANTES
        VÁLIDO HASTA JULIO 2025
        N°B111222
        """
        datos = extraer_datos_crt(text)

        assert datos["Válido Hasta Revisión Técnica"] == ""
        assert datos["Válido Hasta Contaminantes"] == "JULIO 2025"

    def test_extraer_datos_sin_certificado_lanza_error(self):
        """Test que sin ningún certificado lanza error."""
        text = """
        FECHA REVISIÓN: 15 DICIEMBRE 2024
        PLANTA: SGS-001
        PLACA PATENTE ABCD12
        N°B123456
        """
        with pytest.raises(ValueError) as exc_info:
            extraer_datos_crt(text)

        assert "no contiene ningún certificado válido" in str(exc_info.value)

    def test_validacion_exitosa(self):
        """Test de validación exitosa."""
        datos = {
            "Fecha de Revisión": "15 DICIEMBRE 2024",
            "Planta": "SGS-001",
            "Placa Patente": "ABCD12",
            "Válido Hasta Revisión Técnica": "DICIEMBRE 2025",
            "Válido Hasta Contaminantes": "",
            "Folio": "N°B123456",
        }
        # No debe lanzar excepción
        best_effort_validation_crt(datos, "test.pdf")

    def test_validacion_falla_sin_fecha(self):
        """Test de validación fallida sin fecha."""
        datos = {
            "Fecha de Revisión": "",
            "Planta": "SGS-001",
            "Placa Patente": "ABCD12",
            "Válido Hasta Revisión Técnica": "DICIEMBRE 2025",
            "Válido Hasta Contaminantes": "",
            "Folio": "N°B123456",
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_crt(datos, "test.pdf")

        assert 'Falta el campo obligatorio "Fecha de Revisión"' in str(exc_info.value)

    def test_validacion_falla_sin_valido_hasta(self):
        """Test de validación fallida sin ningún 'Válido Hasta'."""
        datos = {
            "Fecha de Revisión": "15 DICIEMBRE 2024",
            "Planta": "SGS-001",
            "Placa Patente": "ABCD12",
            "Válido Hasta Revisión Técnica": "",
            "Válido Hasta Contaminantes": "",
            "Folio": "N°B123456",
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_crt(datos, "test.pdf")

        assert "Debe haber al menos uno" in str(exc_info.value)

    def test_validacion_folio_formato_incorrecto(self):
        """Test de validación con folio en formato incorrecto."""
        datos = {
            "Fecha de Revisión": "15 DICIEMBRE 2024",
            "Planta": "SGS-001",
            "Placa Patente": "ABCD12",
            "Válido Hasta Revisión Técnica": "DICIEMBRE 2025",
            "Válido Hasta Contaminantes": "",
            "Folio": "123456",  # Sin prefijo N°B
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_crt(datos, "test.pdf")

        assert "Folio" in str(exc_info.value)
