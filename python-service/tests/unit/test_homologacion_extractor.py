"""
Tests unitarios para Homologación Extractor.
"""

import pytest

from app.extractors.homologacion_extractor import (
    best_effort_validation_homologacion,
    extraer_datos_homologacion,
)


class TestHomologacionExtractor:
    """Tests para el extractor de Homologación."""

    def test_extrae_datos_completos(self):
        """Test de extracción completa."""
        text = """
        FECHA DE EMISIÓN 15/DIC/2024
        Nº CORRELATIVO ABC-123
        CÓDIGO DE INFORME TÉCNICO INF-456
        PATENTE AB-CD-12
        VÁLIDO HASTA DIC/2025
        TIPO DE VEHÍCULO AUTOMOVIL
        MARCA TOYOTA
        AÑO 2020
        MODELO COROLLA XLI COLOR BLANCO
        VIN 1HGBH41JXMN109186
        Nº MOTOR 4A92F123456
        Firmado por: Juan Pérez
        """
        datos = extraer_datos_homologacion(text)

        assert datos["Fecha de Emisión"] == "15/DIC/2024"
        assert datos["Nº Correlativo"] == "ABC-123"
        assert datos["Código Informe Técnico"] == "INF-456"
        # Patente debe ser limpiada a 6 caracteres sin guiones
        assert datos["Patente"] == "ABCD12"
        assert datos["Válido Hasta"] == "DIC/2025"
        assert datos["Tipo de Vehículo"] == "AUTOMOVIL"
        assert datos["Marca"] == "TOYOTA"
        assert datos["Año"] == "2020"
        assert datos["Modelo"] == "COROLLA XLI"
        assert datos["Color"] == "BLANCO"
        assert datos["VIN"] == "1HGBH41JXMN109186"

    def test_limpia_patente_con_guiones(self):
        """Test que la patente se limpia correctamente."""
        text = """
        PATENTE LX-WJ-75-4
        """
        datos = extraer_datos_homologacion(text)
        # Debe tomar solo los primeros 6 caracteres después de limpiar
        assert datos["Patente"] == "LXWJ75"

    def test_limpia_motor_con_sufijo(self):
        """Test que el motor se limpia correctamente."""
        text = """
        Nº MOTOR ABC123 C
        """
        datos = extraer_datos_homologacion(text)
        # Debe eliminar el sufijo " C"
        assert datos["Nº Motor"] == "ABC123"

    def test_limpia_firmado_con_fecha(self):
        """Test que el firmado se limpia correctamente."""
        text = """
        Firmado por: Juan Pérez 15/12/2024 algo más
        """
        datos = extraer_datos_homologacion(text)
        # Debe cortar antes de la fecha
        assert datos["Firmado por"] == "Juan Pérez"

    def test_validacion_exitosa(self):
        """Test de validación exitosa."""
        datos = {
            "Fecha de Emisión": "15/DIC/2024",
            "Nº Correlativo": "ABC-123",
            "Código Informe Técnico": "INF-456",
            "Patente": "ABCD12",
            "Válido Hasta": "DIC/2025",
            "Tipo de Vehículo": "AUTOMOVIL",
            "Marca": "TOYOTA",
            "Año": "2020",
            "Modelo": "COROLLA",
            "Color": "BLANCO",
            "VIN": "1HGBH41JXMN109186",
            "Nº Motor": "4A92F123456",
            "Firmado por": "Juan Pérez",
        }
        # No debe lanzar excepción
        best_effort_validation_homologacion(datos, "test.pdf")

    def test_validacion_falla_patente_incorrecta(self):
        """Test de validación con patente incorrecta."""
        datos = {
            "Fecha de Emisión": "15/DIC/2024",
            "Nº Correlativo": "ABC-123",
            "Código Informe Técnico": "INF-456",
            "Patente": "ABC",  # Menos de 6 caracteres
            "Válido Hasta": "DIC/2025",
            "Tipo de Vehículo": "AUTOMOVIL",
            "Marca": "TOYOTA",
            "Año": "2020",
            "Modelo": "COROLLA",
            "Color": "BLANCO",
            "VIN": "1HGBH41JXMN109186",
            "Nº Motor": "4A92F123456",
            "Firmado por": "Juan Pérez",
        }
        with pytest.raises(ValueError) as exc_info:
            best_effort_validation_homologacion(datos, "test.pdf")

        assert "Patente" in str(exc_info.value)
