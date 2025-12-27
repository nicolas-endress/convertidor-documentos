# Arquitectura: Migración del Motor de Procesamiento a Python

## A) Diagrama de Arquitectura

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USUARIOS                                        │
│                         (Navegadores Web)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS (UI Frontend)                                │
│                        Puerto 3000 (ejemplo)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  • Interfaz web multiusuario                                        │    │
│  │  • Selección de archivos PDF                                        │    │
│  │  • Selección de formato (CRT, SOAP, Homologación, Permiso)         │    │
│  │  • Visualización de progreso en tiempo real (SSE)                   │    │
│  │  • Descarga del Excel generado                                      │    │
│  │  • Manejo de errores y reintentos                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP POST multipart/form-data
                                    │ + SSE (Server-Sent Events)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYTHON SERVICE (Motor de Procesamiento)                   │
│                        Puerto 8000 (FastAPI + Uvicorn)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CAPA API (FastAPI)                                                 │    │
│  │  ├── POST /convert         → Procesar PDFs, streaming SSE          │    │
│  │  ├── GET  /health          → Health check                          │    │
│  │  └── GET  /docs            → Swagger UI (auto-generado)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CAPA SERVICIOS                                                     │    │
│  │  ├── PDFService            → Orquestación batch, concurrencia       │    │
│  │  └── ExcelService          → Generación Excel (Polars + XlsxWriter)│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CAPA EXTRACTORES (Portados 1:1 desde TypeScript)                   │    │
│  │  ├── CRTExtractor          → Certificado Revisión Técnica          │    │
│  │  ├── HomologacionExtractor → Certificado Homologación              │    │
│  │  ├── SOAPExtractor         → Seguro Obligatorio                    │    │
│  │  └── PermisoExtractor      → Permiso de Circulación                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CAPA UTILIDADES                                                    │    │
│  │  ├── pdf_utils.py          → PyMuPDF (fitz) para extracción texto  │    │
│  │  ├── text_utils.py         → buscar(), sanitizar(), normalizar()   │    │
│  │  └── logger.py             → Logging estructurado JSON             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Archivos temporales
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SISTEMA DE ARCHIVOS                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  %TEMP%/pdf-processor/                                              │    │
│  │  ├── uploads/              → PDFs subidos (limpieza automática)    │    │
│  │  └── outputs/              → Excel generados (TTL 1 hora)          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## B) Stack Tecnológico

### Frontend (Existente - Sin cambios)

- **Next.js 14+** con App Router
- **React** para UI
- **TypeScript** para type safety
- Comunicación con backend vía `fetch()` + SSE

### Backend Python (Nuevo)

| Componente | Tecnología | Justificación |

|------------|------------|---------------|
| Framework API | **FastAPI** | SSE nativo, async, OpenAPI automático, alto rendimiento |
| Server ASGI | **Uvicorn** | Rápido, compatible con Windows, producción-ready |
| Extracción PDF | **PyMuPDF (fitz)** | 10-50x más rápido que pdf2json, bajo uso de memoria |
| DataFrames | **Polars** | Más rápido que Pandas, zero-copy, lazy evaluation |
| Excel | **XlsxWriter** | Control fino de formato, compatible con xlsx-populate |
| Concurrencia | **asyncio + Semaphore** | No bloqueante, eficiente para I/O bound |
| Logging | **structlog** | JSON estructurado, request_id tracking |
| Empaquetado | **PyInstaller** | .exe standalone para Windows |
| Servicio Windows | **NSSM** | Instalación como servicio sin modificar código |

## C) Flujo de Datos

```text
1. Usuario selecciona PDFs en UI (Next.js)
           │
           ▼
2. Next.js envía POST /convert a Python Service
   - multipart/form-data con N archivos
   - parámetros: pdfFormat, returnRegex, concurrency
           │
           ▼
3. Python Service inicia procesamiento
   - Valida inputs (tamaño, tipo MIME, cantidad)
   - Crea request_id para tracking
   - Inicia StreamingResponse (SSE)
           │
           ▼
4. Por cada PDF (con concurrencia controlada):
   a. Extraer texto con PyMuPDF
   b. Detectar formato por palabras clave
   c. Validar formato esperado vs detectado
   d. Aplicar extractor específico (regex)
   e. Validar datos extraídos (best-effort)
   f. Emitir evento SSE de progreso
           │
           ▼
5. Al finalizar todos los PDFs:
   - Construir DataFrame Polars con resultados
   - Aplicar normalizaciones (placas, dígitos verificadores)
   - Generar Excel con XlsxWriter
   - Codificar Excel en base64
   - Emitir evento SSE "final" con resumen + Excel
           │
           ▼
6. Next.js recibe evento "final":
   - Decodifica Excel de base64
   - Ofrece descarga al usuario
   - Muestra estadísticas de procesamiento
```

## D) Comunicación Next.js ↔ Python

### Opción 1: Proxy Directo (Recomendada para desarrollo)

```javascript
// next.config.ts
async rewrites() {
  return [
    {
      source: '/api/convert',
      destination: 'http://localhost:8000/convert',
    },
  ];
}
```

### Opción 2: Llamada Directa desde Frontend

```typescript
// En el componente React
const response = await fetch('http://python-service:8000/convert', {
  method: 'POST',
  body: formData,
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      // Actualizar UI con evento
    }
  }
}
```

### Opción 3: Servicio Interno (Producción)

```text
[Nginx/IIS] → [Next.js :3000] → [Python :8000 interno]
                    │
                    └── Proxy reverso para /api/convert
```

## E) Consideraciones de Seguridad

1. **Validación de Inputs**
   - Tamaño máximo por archivo: 10 MB
   - Cantidad máxima de archivos: 100
   - Tipos MIME permitidos: application/pdf
   - Sanitización de nombres de archivo

2. **Protección contra Path Traversal**

   ```python
   import os
   def safe_filename(filename: str) -> str:
       return os.path.basename(filename).replace('..', '')
   ```

3. **Limpieza de Temporales**
   - TTL de 1 hora para archivos generados
   - Limpieza al inicio del servicio
   - Limpieza periódica con scheduler

4. **Rate Limiting** (opcional)
   - Por IP: 10 requests/minuto
   - Por request_id: 1 concurrent

5. **No Ejecución de Contenido**
   - PyMuPDF no ejecuta JavaScript en PDFs
   - No se procesan macros ni scripts embebidos
