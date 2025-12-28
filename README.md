
# Conversor PDF a Excel

**Conversor PDF a Excel** es una aplicación desarrollada con Next.js y TypeScript que permite convertir archivos PDF a un documento Excel. Soporta diversos formatos de PDF, incluyendo:

- Certificado de Homologación
- Certificado de Revisión Técnica (CRT)
- SOAP (Seguro Obligatorio)
- Permiso de Circulación

La aplicación extrae datos relevantes de los PDFs utilizando extractores específicos, valida la información y genera un Excel que incluye tanto los datos extraídos como (opcionalmente) estadísticas del procesamiento. Además, se utiliza Server-Sent Events (SSE) para notificar en tiempo real el progreso del procesamiento.

---

## Características

- **Extracción y Validación de Datos:**
  Cada formato de PDF cuenta con un extractor especializado que utiliza expresiones regulares para obtener y validar campos críticos.

- **Generación de Excel:**
  Los datos se organizan en una hoja de Excel, con una hoja adicional opcional para mostrar estadísticas (totales procesados, éxitos, fallos y detalles de archivos fallidos).

- **Feedback en Tiempo Real:**
  Se informa al usuario sobre el progreso del procesamiento de los PDFs mediante SSE, permitiendo visualizar actualizaciones y tiempos estimados.

- **Interfaz de Usuario Intuitiva:**
  Basada en React, facilita la carga de archivos mediante arrastrar y soltar, selección de formato y vista previa de los resultados.

- **Pruebas Automatizadas:**
  Cuenta con una robusta suite de tests con Jest y ESLint para mantener la calidad del código y la estabilidad del proyecto.

---

## Instalación

### Requisitos

- **Frontend:** Bun ≥ 1.1 (usa los scripts de `package.json` con `bun run ...`).
- **Backend:** Python ≥ 3.10 y `uv` (o `pip`) para el servicio `python-service/`.

### Frontend (Next.js)

1. Clona el repositorio y entra al proyecto

```bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```

1. Instala dependencias

```bash
bun install
```

1. Configura variables de entorno

Crea `.env.local` en la raíz con al menos:

```env
NEXT_PUBLIC_MAX_FILE_SIZE=5242880
```

### Backend (python-service)

1. Entra al servicio Python

```bash
cd python-service
```

1. Instala dependencias (recomendado con uv)

```bash
uv sync
# o
pip install -r requirements.txt
```

1. (Opcional) Ejecutar en desarrollo

```bash
uv run uvicorn app.main:app --reload --port 8001
```

Variables clave: revisa `python-service/app/config.py` para límites de tamaño, concurrencia y CORS.

---

## Uso

### En desarrollo

1. Arranca el backend (opcional si solo consumes la API Next)

```bash
cd python-service
uv run uvicorn app.main:app --reload --port 8001
```

1. Arranca el frontend

```bash
cd ..
bun run dev
```

1. Abre [http://localhost:3000](http://localhost:3000) y carga tus PDFs. El sistema muestra progreso vía SSE y entrega el Excel generado.

### Ejecución de pruebas

- Frontend: `bun run test`
- Backend: `cd python-service && uv run pytest`

---

## Arquitectura del Proyecto

El proyecto se organiza en las siguientes áreas:

- **Frontend (Next.js + React 19):**
  - UI de carga y vista previa (`components/`), flujo principal en `app/page.tsx`.
  - Ruta API en `app/api/convert/route.ts` que orquesta la conversión y expone progreso por SSE.

- **Backend (python-service, FastAPI):**
  - Endpoint `/convert` que procesa múltiples PDFs con PyMuPDF, aplica extractores (CRT, SOAP, Homologación, Permiso) y devuelve Excel vía SSE.
  - Configuración en `app/config.py` para tamaños máximos, concurrencia y límites de archivos.

- **Extractores y utilidades:**
  - JavaScript/TypeScript: carpeta `extractors/` y `utils/` para parsing y validaciones.
  - Python: servicios en `app/services/` y utilidades en `app/utils/` (mismo dominio funcional).

- **Pruebas:**
  - Frontend: Jest + Testing Library.
  - Backend: Pytest (incluye pruebas de extractores y conversión).

---

## Contribución

¡Las contribuciones son bienvenidas! Para contribuir:

1. Haz un _fork_ del repositorio.
2. Crea una rama (_branch_) para tu mejora o corrección.
3. Envía un _pull request_ describiendo los cambios realizados.

---

## Licencia

Este proyecto está bajo la licencia [GNU AGPL v3](LICENSE).

---

## Cambios recientes

- Configuración de Pyright en `python-service/` para eliminar falsos positivos de tipado en PyMuPDF.
- Correcciones en `pdf_service_turbo.py` y scripts de benchmarks para manejo seguro de texto extraído.
- Auditoría de dependencias: el backend usa PyMuPDF (licencia AGPL-3.0), alineando la licencia del repositorio a AGPL.

---
