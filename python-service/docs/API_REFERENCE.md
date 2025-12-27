# API Reference - Python PDF Processor Service

## Endpoints

### POST /convert

Procesa uno o más archivos PDF y retorna un Excel consolidado con los datos extraídos.

#### Request

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Requerido | Descripción |

|-------|------|-----------|-------------|
| `pdf` | File[] | ✅ | Uno o más archivos PDF a procesar |
| `pdfFormat` | string | ❌ | Formato esperado: `CERTIFICADO_DE_HOMOLOGACION`, `CRT`, `SOAP`, `PERMISO_CIRCULACION` |
| `returnRegex` | boolean | ❌ | Si `true`, retorna las regex usadas (solo para PERMISO_CIRCULACION). Default: `false` |
| `concurrency` | integer | ❌ | Concurrencia máxima de procesamiento. Default: `15` |

#### Response

**Content-Type:** `text/event-stream`

La respuesta es un stream de Server-Sent Events (SSE) con el siguiente formato:

```text
data: {"progress": 1, "total": 10, ...}\n\n
data: {"progress": 2, "total": 10, ...}\n\n
...
data: {"final": {...}}\n\n
```

#### Eventos de Progreso

Cada evento de progreso tiene la siguiente estructura:

```json
{
  "progress": 3,
  "total": 10,
  "file": "documento.pdf",
  "status": "fulfilled",
  "successes": 3,
  "failures": 0,
  "elapsedMsSoFar": 1234,
  "estimatedMsLeft": 2500,
  "error": null
}
```

| Campo | Tipo | Descripción |

|-------|------|-------------|
| `progress` | integer | Número de archivos procesados hasta ahora |
| `total` | integer | Total de archivos a procesar |
| `file` | string | Nombre del archivo actual |
| `status` | string | `"fulfilled"` (éxito) o `"rejected"` (error) |
| `successes` | integer | Cantidad de archivos exitosos hasta ahora |
| `failures` | integer | Cantidad de archivos fallidos hasta ahora |
| `elapsedMsSoFar` | integer | Tiempo transcurrido en milisegundos |
| `estimatedMsLeft` | integer | Tiempo estimado restante en milisegundos |
| `error` | string\|null | Mensaje de error si `status === "rejected"` |

#### Evento Final

El último evento contiene el resultado completo:

```json
{
  "final": {
    "totalProcesados": 10,
    "totalExitosos": 9,
    "totalFallidos": 1,
    "exitosos": [
      {
        "fileName": "crt_001.pdf",
        "datos": {
          "Fecha de Revisión": "15 DICIEMBRE 2024",
          "Planta": "SGS-001",
          "Placa Patente": "ABCD12",
          "Válido Hasta Revisión Técnica": "DICIEMBRE 2025",
          "Válido Hasta Contaminantes": "DICIEMBRE 2025",
          "Folio": "N°B123456"
        }
      }
    ],
    "fallidos": [
      {
        "fileName": "invalido.pdf",
        "error": "El archivo invalido.pdf no corresponde al formato esperado (CRT). Se detectó que pertenece a: SOAP."
      }
    ],
    "excel": "UEsDBBQAAAAIAH...",
    "fileName": "Certificado%20de%20Revisi%C3%B3n%20T%C3%A9cnica%20(CRT).xlsx"
  }
}
```

| Campo | Tipo | Descripción |

|-------|------|-------------|
| `totalProcesados` | integer | Total de archivos procesados |
| `totalExitosos` | integer | Archivos procesados con éxito |
| `totalFallidos` | integer | Archivos que fallaron |
| `exitosos` | array | Lista de resultados exitosos con datos extraídos |
| `fallidos` | array | Lista de archivos fallidos con mensajes de error |
| `excel` | string | Excel codificado en Base64 |
| `fileName` | string | Nombre del archivo Excel (URL encoded) |

---

### GET /health

Health check para monitoreo y balanceadores de carga.

#### Responses

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "processed_total": 1500,
  "errors_total": 25
}
```

---

### GET /docs

Swagger UI auto-generado por FastAPI.

---

## Ejemplos con cURL

### Procesar un solo PDF

```bash
curl -X POST http://localhost:8000/convert \
  -F "pdf=@/path/to/documento.pdf" \
  -F "pdfFormat=CRT" \
  --no-buffer
```

### Procesar múltiples PDFs

```bash
curl -X POST http://localhost:8000/convert \
  -F "pdf=@/path/to/doc1.pdf" \
  -F "pdf=@/path/to/doc2.pdf" \
  -F "pdf=@/path/to/doc3.pdf" \
  -F "pdfFormat=SOAP" \
  -F "concurrency=10" \
  --no-buffer
```

### Procesar con returnRegex

```bash
curl -X POST http://localhost:8000/convert \
  -F "pdf=@/path/to/permiso.pdf" \
  -F "pdfFormat=PERMISO_CIRCULACION" \
  -F "returnRegex=true" \
  --no-buffer
```

### Auto-detectar formato

```bash
curl -X POST http://localhost:8000/convert \
  -F "pdf=@/path/to/desconocido.pdf" \
  --no-buffer
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## Ejemplos con Python

### Cliente básico con requests

```python
import requests
import json
import base64

def process_pdfs(pdf_paths: list, pdf_format: str = None):
    files = [("pdf", open(path, "rb")) for path in pdf_paths]
    data = {}
    if pdf_format:
        data["pdfFormat"] = pdf_format

    response = requests.post(
        "http://localhost:8000/convert",
        files=files,
        data=data,
        stream=True
    )

    for line in response.iter_lines():
        if line:
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                event = json.loads(line_str[6:])

                if "final" in event:
                    # Guardar Excel
                    excel_bytes = base64.b64decode(event["final"]["excel"])
                    with open("resultado.xlsx", "wb") as f:
                        f.write(excel_bytes)
                    print(f"Excel guardado. Exitosos: {event['final']['totalExitosos']}")
                else:
                    # Mostrar progreso
                    print(f"[{event['progress']}/{event['total']}] {event['file']} - {event['status']}")

# Uso
process_pdfs(["doc1.pdf", "doc2.pdf"], "CRT")
```

### Cliente async con httpx

```python
import httpx
import asyncio
import json
import base64

async def process_pdfs_async(pdf_paths: list, pdf_format: str = None):
    files = [("pdf", open(path, "rb")) for path in pdf_paths]
    data = {"pdfFormat": pdf_format} if pdf_format else {}

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/convert",
            files=files,
            data=data
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    yield event

# Uso
async def main():
    async for event in process_pdfs_async(["doc1.pdf"], "CRT"):
        if "final" in event:
            print(f"Completado: {event['final']['totalExitosos']} exitosos")
        else:
            print(f"Progreso: {event['progress']}/{event['total']}")

asyncio.run(main())
```

---

## Códigos de Error HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Procesamiento completado (aunque haya archivos fallidos) |
| 400 | Request inválido (sin archivos, formato inválido, etc.) |
| 413 | Payload demasiado grande (excede límite de tamaño) |
| 422 | Error de validación (archivo corrupto, no es PDF, etc.) |
| 500 | Error interno del servidor |
| 503 | Servicio no disponible (sobrecarga) |

---

## Mensajes de Error Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `No se proporcionó ningún archivo PDF` | Request sin archivos | Incluir al menos un archivo con key `pdf` |
| `El archivo X no corresponde al formato esperado (Y)` | Formato detectado no coincide con `pdfFormat` | Verificar formato o no especificar `pdfFormat` |
| `El PDF no contiene texto extraíble` | PDF escaneado o protegido | Usar OCR previamente o desproteger |
| `Falta el campo "X"` | Extracción incompleta | Verificar calidad del PDF |
| `Campo "X" no coincide con el formato esperado` | Validación best-effort fallida | Revisar contenido del campo |

---

## Límites del Servicio

| Límite | Valor | Configurable |
|--------|-------|--------------|
| Tamaño máximo por archivo | 10 MB | `MAX_FILE_SIZE` |
| Cantidad máxima de archivos | 100 | `MAX_FILES` |
| Concurrencia máxima | 50 | `MAX_CONCURRENCY` |
| Timeout por archivo | 30 segundos | `FILE_TIMEOUT` |
| Timeout total | 10 minutos | `REQUEST_TIMEOUT` |
