# PDF Converter Python Service

Motor de procesamiento de PDFs en Python para el convertidor de documentos.

## 🚀 Inicio Rápido

### Requisitos

- Python 3.11+
- pip o uv

### Instalación

```bash
# Clonar o navegar al directorio
cd python-service

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Ejecución

```bash
# Desarrollo (con hot-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O usando el script de desarrollo
scripts\dev.bat dev
```

### Verificar funcionamiento

```bash
curl http://localhost:8000/health
```

## 📁 Estructura del Proyecto

```text
python-service/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── config.py            # Configuración con Pydantic
│   ├── models.py            # Modelos de datos
│   ├── extractors/          # Extractores por formato
│   │   ├── crt_extractor.py
│   │   ├── homologacion_extractor.py
│   │   ├── soap_extractor.py
│   │   └── permiso_circulacion_extractor.py
│   ├── services/            # Servicios de negocio
│   │   ├── pdf_service.py
│   │   └── excel_service.py
│   └── utils/               # Utilidades
│       ├── text_utils.py
│       ├── pdf_utils.py
│       └── logger.py
├── tests/                   # Tests
│   ├── unit/
│   └── integration/
├── benchmarks/              # Scripts de benchmark
├── scripts/                 # Scripts de utilidad
├── docs/                    # Documentación
└── requirements.txt
```

## 📖 API

### POST /convert

Convierte PDFs al formato Excel.

**Request:**

- `Content-Type: multipart/form-data`
- `files`: Archivos PDF (múltiples)
- `pdfFormat`: Formato de PDF (`CRT`, `CERTIFICADO_DE_HOMOLOGACION`, `SOAP`, `PERMISO_CIRCULACION`)
- `returnRegex`: (opcional) Incluir patrones regex en respuesta

**Response:**

- `Content-Type: text/event-stream`
- Eventos SSE con progreso y resultado

### GET /health

Health check del servicio.

## 🧪 Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/test_crt_extractor.py -v
```

## 🏭 Despliegue en Windows

### Como ejecutable

```bash
# Crear ejecutable
pyinstaller main.spec

# El ejecutable estará en dist/main.exe
```

### Como servicio Windows

```bash
# Instalar servicio (requiere Admin)
scripts\install_service.bat

# Desinstalar servicio
scripts\uninstall_service.bat
```

## 📊 Benchmark

```bash
python benchmarks/compare_systems.py --pdfs-dir ./test_pdfs --format CRT
```

## 📚 Documentación

- [Arquitectura](docs/ARQUITECTURA.md)
- [API Reference](docs/API_REFERENCE.md)
- [Plan de Migración](docs/PLAN_MIGRACION.md)

## 🔧 Configuración

Variables de entorno:

| Variable | Descripción | Default |
| -------- | ----------- | ------- |
| `HOST` | Host del servidor | `0.0.0.0` |
| `PORT` | Puerto del servidor | `8000` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `LOG_FORMAT` | Formato de logs (`json`/`text`) | `json` |
| `MAX_CONCURRENCY` | Concurrencia máxima | `15` |
| `DEBUG` | Modo debug | `false` |

## 📝 Licencia

Privado - Uso interno
