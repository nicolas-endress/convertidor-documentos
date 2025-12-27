"""
Tests unitarios para Permiso Circulación Extractor.

ACTUALIZADO para coincidir con la implementación que devuelve:
{"data": {...}, "regexes": {...}} cuando return_regex=True
{"data": {...}} cuando return_regex=False
"""

from app.extractors.permiso_circulacion_extractor import (
    extraer_datos_permiso_circulacion,
)


class TestPermisoCirculacionExtractor:
    """Tests para el extractor de Permiso de Circulación."""

    def test_extrae_datos_completos(self):
        """Test de extracción completa."""
        text = """
        Placa Única: ABCD12
        Codigo SII: 123456789
        Valor Permiso: 125000
        Fecha de emisión: 01/01/2024
        Fecha de vencimiento: 31/12/2024
        Forma de Pago: EFECTIVO
        Pago total: X
        Total a pagar: 125000
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]

        assert datos["Placa Única"] == "ABCD12"
        assert datos["Código SII"] == "123456789"
        assert datos["Valor Permiso"] == "125000"
        assert datos["Fecha de emisión"] == "01/01/2024"
        assert datos["Forma de Pago"] == "EFECTIVO"

    def test_extrae_placa_unica(self):
        """Test de extracción de Placa Única."""
        text = """
        Placa Única: XY-1234
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]
        assert datos["Placa Única"] == "XY-1234"

    def test_campos_pago_vacios_default_no_aplica(self):
        """Test que campos de pago vacíos devuelven 'No aplica'."""
        text = """
        Placa Única: ABCD12
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]

        # Los campos de pago deben ser "No aplica" cuando están vacíos
        assert datos["Pago total"] == "No aplica"
        assert datos["Pago Cuota 1"] == "No aplica"
        assert datos["Pago Cuota 2"] == "No aplica"

    def test_return_regex_incluye_patrones(self):
        """Test que return_regex devuelve los patrones usados."""
        text = """
        Placa Única: TEST12
        Codigo SII: 987654321
        """
        result = extraer_datos_permiso_circulacion(text, return_regex=True)

        # Debe incluir el campo regexes con los patrones
        assert "regexes" in result
        regex_dict = result["regexes"]

        # Verificar que contiene patrones para los campos principales
        assert "Placa Única" in regex_dict
        assert "Código SII" in regex_dict

    def test_sin_return_regex_no_incluye_patrones(self):
        """Test que sin return_regex no hay patrones."""
        text = """
        Placa Única: TEST12
        """
        result = extraer_datos_permiso_circulacion(text, return_regex=False)

        assert "regexes" not in result

    def test_variantes_fecha_emision(self):
        """Test de variantes de fecha de emisión."""
        variantes = [
            "Fecha emisión: 15/06/2024",
            "Fecha de emisión: 15/06/2024",
            "FECHA EMISION: 15/06/2024",
        ]
        for text in variantes:
            result = extraer_datos_permiso_circulacion(text)
            datos = result["data"]
            assert datos.get("Fecha de emisión", "") == "15/06/2024"

    def test_pago_total_marcado(self):
        """Test de extracción de pago total marcado."""
        text = """
        Pago total: X
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]
        assert datos["Pago total"] == "X"

    def test_total_a_pagar_formato_numerico(self):
        """Test de total a pagar con formato numérico."""
        text = """
        Total a pagar: 250000
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]
        assert datos["Total a pagar"] == "250000"

    def test_valor_permiso_extraccion(self):
        """Test de extracción de valor permiso."""
        text = """
        Valor Permiso: 125000
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]
        assert datos["Valor Permiso"] == "125000"

    def test_forma_pago_variantes(self):
        """Test de variantes de forma de pago."""
        text = """
        Forma de Pago: TRANSFERENCIA
        """
        result = extraer_datos_permiso_circulacion(text)
        datos = result["data"]
        assert datos["Forma de Pago"] == "TRANSFERENCIA"
