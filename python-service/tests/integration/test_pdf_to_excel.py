"""
Tests de integración para el flujo completo PDF → Excel.
"""

# Importar después de configurar el path
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import ExcelStats, PDFFormat
from app.services.excel_service import generate_excel
from app.services.pdf_service import process_pdf_files


class TestPDFToExcelIntegration:
    """Tests de integración para el flujo completo."""

    @pytest.fixture
    def sample_crt_text(self):
        """Texto de ejemplo de un CRT válido."""
        return """
        CERTIFICADO DE REVISIÓN TÉCNICA
        FECHA REVISIÓN: 15 ENERO 2024
        PLACA PATENTE ABCD12
        PLANTA: PLANTA-TEST-001
        N°B123456
        VÁLIDO HASTA DICIEMBRE 2024

        CERTIFICADO DE EMISIONES CONTAMINANTES
        FECHA REVISIÓN: 15 ENERO 2024
        PLACA PATENTE ABCD12
        PLANTA: PLANTA-TEST-001
        N°B789012
        VÁLIDO HASTA DICIEMBRE 2024
        """

    @pytest.fixture
    def sample_homologacion_text(self):
        """Texto de ejemplo de Homologación."""
        return """
        CERTIFICADO DE HOMOLOGACIÓN
        FECHA DE EMISIÓN 01/ENE/2024
        Nº CORRELATIVO ABC-123
        CÓDIGO DE INFORME TÉCNICO IT-2024-001
        PATENTE LXWJ75-4
        VÁLIDO HASTA DIC/2025
        TIPO DE VEHÍCULO AUTOMOVIL
        MARCA TOYOTA
        AÑO 2022
        MODELO COROLLA COLOR BLANCO
        VIN 1HGBH41JXMN109186
        Nº MOTOR 2ZR1234567
        Firmado por: CERTIFICADOR OFICIAL
        """

    @pytest.mark.asyncio
    async def test_process_single_crt_file(self, sample_crt_text, tmp_path):
        """Test de procesamiento de un archivo CRT."""
        # Crear archivo PDF de prueba (mock)
        pdf_file = tmp_path / "test_crt.pdf"
        pdf_file.write_bytes(b"PDF mock content")

        events: list[dict] = []

        def capture_event(event: dict):
            events.append(event)

        # Mock de extract_text_from_pdf
        with patch("app.services.pdf_service.extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = sample_crt_text

            results = await process_pdf_files(
                files=[(str(pdf_file), pdf_file.read_bytes())],
                pdf_format=PDFFormat.CRT,
                return_regex=False,
                on_event=capture_event,
            )

        # Verificar resultados - process_pdf_files retorna lista de dicts con status y value
        assert len(results) == 1
        assert results[0]["status"] == "fulfilled"
        assert "value" in results[0]

        # Verificar que se emitieron eventos
        assert len(events) > 0
        # Los eventos son diccionarios con claves como 'progress', 'total', 'status'
        assert any("progress" in e for e in events)
        assert any("status" in e for e in events)

    @pytest.mark.asyncio
    async def test_excel_generation_from_records(self, sample_crt_text):
        """Test de generación de Excel desde registros."""
        # Registros de prueba - usando la firma real de generate_excel
        records = [
            {
                "Nombre PDF": "test1.pdf",
                "Patente": "ABCD12",
                "Planta": "PLANTA TEST",
                "Fecha Revisión": "15/01/2024",
            },
            {
                "Nombre PDF": "test2.pdf",
                "Patente": "WXYZ99",
                "Planta": "PLANTA TEST 2",
                "Fecha Revisión": "20/01/2024",
            },
        ]

        # ExcelStats tiene campos específicos: totalProcesados, totalExitosos, totalFallidos, fallidos
        stats = ExcelStats(
            totalProcesados=2,
            totalExitosos=2,
            totalFallidos=0,
            fallidos=[],
        )

        # Generar Excel - usando firma real: generate_excel(registros, file_name, pdf_format, stats)
        excel_bytes, encoded_name = generate_excel(
            registros=records,
            file_name="test_output",
            pdf_format=PDFFormat.CRT,
            stats=stats,
        )

        # Verificar que se generó contenido
        assert excel_bytes is not None
        assert len(excel_bytes) > 0

        # Verificar que es un archivo Excel válido (magic bytes)
        assert excel_bytes[:4] == b"PK\x03\x04"  # ZIP header (xlsx es un zip)

    @pytest.mark.asyncio
    async def test_batch_processing_with_failures(self, tmp_path, sample_homologacion_text):
        """Test de procesamiento por lotes con archivos que fallan."""
        events: list[dict] = []

        def capture_event(event: dict):
            events.append(event)

        # Mock que falla para algunos archivos
        call_count = [0]

        def mock_extract(content):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise ValueError("Error simulado")
            return sample_homologacion_text

        with patch("app.services.pdf_service.extract_text_from_pdf", side_effect=mock_extract):
            await process_pdf_files(
                files=[
                    ("file1.pdf", b"content1"),
                    ("file2.pdf", b"content2"),
                    ("file3.pdf", b"content3"),
                ],
                pdf_format=PDFFormat.CERTIFICADO_DE_HOMOLOGACION,
                return_regex=False,
                on_event=capture_event,
            )

        # Verificar que se reportaron éxitos y fallos en los eventos
        # Los eventos contienen 'successes' y 'failures' como claves
        successes = [e for e in events if e.get("successes", 0) > 0]
        failures = [e for e in events if e.get("failures", 0) > 0]

        assert len(successes) > 0
        assert len(failures) > 0

    @pytest.mark.asyncio
    async def test_concurrency_limit_respected(self, tmp_path, sample_homologacion_text):
        """Test que el límite de concurrencia se respeta."""
        max_concurrent = [0]
        current_concurrent = [0]

        def slow_extract(content):
            import time

            current_concurrent[0] += 1
            max_concurrent[0] = max(max_concurrent[0], current_concurrent[0])
            time.sleep(0.05)  # Usar sleep síncrono porque extract_text_from_pdf no es async
            current_concurrent[0] -= 1
            return sample_homologacion_text

        events = []

        with patch("app.services.pdf_service.extract_text_from_pdf", side_effect=slow_extract):
            await process_pdf_files(
                files=[(f"file{i}.pdf", b"content") for i in range(20)],
                pdf_format=PDFFormat.CERTIFICADO_DE_HOMOLOGACION,
                return_regex=False,
                on_event=lambda e: events.append(e),
                concurrency=5,  # Límite de 5
            )

        # Verificar que nunca superamos el límite de concurrencia
        assert max_concurrent[0] <= 5


class TestEndToEndAPI:
    """Tests end-to-end simulando llamadas API."""

    @pytest.mark.asyncio
    async def test_full_convert_flow(self, tmp_path):
        """Test del flujo completo de conversión."""
        # Este test simularía una llamada al endpoint /convert
        # En un entorno real, usaríamos TestClient de FastAPI
        pass  # Implementar con TestClient cuando el servidor esté disponible


class TestFormatDetection:
    """Tests para detección automática de formato."""

    def test_detect_crt_format(self):
        """Test de detección de formato CRT."""
        from app.utils.pdf_utils import detectar_formato

        # La detección busca "CERTIFICADO DE REVISIÓN TÉCNICA" o "FECHA REVISIÓN"
        text = "CERTIFICADO DE REVISIÓN TÉCNICA FECHA REVISIÓN"
        format_detected = detectar_formato(text)
        assert format_detected == PDFFormat.CRT

    def test_detect_homologacion_format(self):
        """Test de detección de formato Homologación."""
        from app.utils.pdf_utils import detectar_formato

        # La detección busca "CERTIFICADO DE HOMOLOGACIÓN"
        text = "CERTIFICADO DE HOMOLOGACIÓN VEHICULAR"
        format_detected = detectar_formato(text)
        assert format_detected == PDFFormat.CERTIFICADO_DE_HOMOLOGACION

    def test_detect_soap_format(self):
        """Test de detección de formato SOAP."""
        from app.utils.pdf_utils import detectar_formato

        # La detección busca "SEGURO OBLIGATORIO" o "SOAP"
        text = "SEGURO OBLIGATORIO ACCIDENTES PERSONALES POLIZA"
        format_detected = detectar_formato(text)
        assert format_detected == PDFFormat.SOAP

    def test_detect_permiso_format(self):
        """Test de detección de formato Permiso de Circulación."""
        from app.utils.pdf_utils import detectar_formato

        # La detección busca "PERMISO DE CIRCULACIÓN" o "PLACA ÚNICA"
        text = "PERMISO DE CIRCULACIÓN MUNICIPAL"
        format_detected = detectar_formato(text)
        assert format_detected == PDFFormat.PERMISO_CIRCULACION
