# Plan de Migración: Next.js → Python Service

## Resumen Ejecutivo

Este documento detalla el plan de migración del motor de procesamiento de PDFs desde el sistema actual (Next.js/TypeScript) a un servicio Python independiente, manteniendo 100% de compatibilidad en la salida.

## Etapas de Migración

---

## ETAPA 1: Feature Parity (Semanas 1-2)

### Objetivo

Replicar exactamente el comportamiento del sistema actual: mismas regex, mismos campos, mismo Excel.

### Tareas

#### 1.1 Configuración del Proyecto (Día 1-2)

- [ ] Crear estructura de carpetas Python
- [ ] Configurar `pyproject.toml` con dependencias
- [ ] Configurar pre-commit hooks (black, ruff, mypy)
- [ ] Crear Dockerfile para desarrollo
- [ ] Configurar pytest con fixtures

#### 1.2 Portar Utilidades Base (Día 2-3)

- [ ] Implementar `text_utils.py`:
  - `buscar(text, pattern)` → equivalente exacto
  - `sanitizar_nombre(str)` → equivalente exacto
  - `normalize_plate_with_check(value)` → equivalente exacto
- [ ] Implementar `pdf_utils.py`:
  - `extract_text_from_pdf(bytes)` → usando PyMuPDF
  - `detectar_formato(texto)` → mismas palabras clave

#### 1.3 Portar Extractores (Día 3-6)

- [ ] **CRT Extractor**:
  - Portar todas las regex literalmente
  - Portar `extraer_datos_crt()` con misma lógica de secciones
  - Portar `best_effort_validation_crt()` con mismos patrones
  - Campos: Fecha de Revisión, Planta, Placa Patente, Válido Hasta RT, Válido Hasta Contaminantes, Folio

- [ ] **Homologación Extractor**:
  - Portar 14 campos con regex exactas
  - Portar limpieza de Patente (6 caracteres)
  - Portar limpieza de Nº Motor (eliminar sufijos)
  - Portar limpieza de Firmado por (eliminar fechas)

- [ ] **SOAP Extractor**:
  - Portar 7 campos con normalización de espacios
  - Portar normalización de RUT
  - Portar normalización de POLIZA N°

- [ ] **Permiso Circulación Extractor**:
  - Portar 10 campos
  - Implementar `returnRegex` (retornar diccionario de regex usadas)
  - Portar normalización de campos de pago ("No aplica")

#### 1.4 Implementar Servicios (Día 6-8)

- [ ] **PDFService**:
  - Procesar archivos con concurrencia (asyncio.Semaphore)
  - Emitir eventos de progreso compatibles
  - Calcular `elapsedMsSoFar` y `estimatedMsLeft`
  - Manejar errores por archivo (fulfilled/rejected)

- [ ] **ExcelService**:
  - Generar DataFrame Polars con registros
  - Aplicar transformaciones por formato (normalización placas)
  - Generar Excel con XlsxWriter
  - Crear hoja "Datos" con orden de columnas correcto
  - Crear hoja "Estadisticas" con fallidos

#### 1.5 Implementar API (Día 8-9)

- [ ] Endpoint POST /convert con FastAPI
- [ ] StreamingResponse para SSE
- [ ] Validación de inputs (Pydantic)
- [ ] Manejo de errores global

#### 1.6 Tests de Compatibilidad (Día 9-10)

- [ ] Tests unitarios para cada extractor
- [ ] Tests comparativos: mismo PDF → mismo output JSON
- [ ] Tests de Excel: mismas columnas, mismo orden
- [ ] Tests de SSE: mismo formato de eventos

### Criterio de Éxito Etapa 1

✅ Para un conjunto de 50 PDFs de prueba:

- JSON de datos extraídos idéntico (diff = 0)
- Excel generado con mismas columnas y valores
- Eventos SSE con misma estructura

### Entregables

- Código Python funcional con los 4 extractores
- Suite de tests con >90% cobertura
- Documentación de diferencias encontradas

---

## ETAPA 2: Optimización (Semana 3)

### Objetivos

Mejorar el rendimiento para ser significativamente más rápido que el sistema actual.

### Tareass

#### 2.1 Optimización de Extracción PDF

- [ ] Compilar regex una sola vez (re.compile en módulo)
- [ ] Extraer texto por página en paralelo si es necesario
- [ ] Cache de texto extraído para re-procesamiento
- [ ] Lazy loading de páginas para PDFs grandes

#### 2.2 Optimización de Procesamiento

- [ ] Usar `asyncio.gather()` con Semaphore eficiente
- [ ] Pool de workers para CPU-bound (ProcessPoolExecutor)
- [ ] Streaming de resultados en lugar de acumulación
- [ ] Batch inserts en DataFrame

#### 2.3 Optimización de Excel

- [ ] Usar Polars `write_excel()` directamente si es suficiente
- [ ] Streaming write para Excel grandes
- [ ] Compresión optimizada del archivo

#### 2.4 Benchmark y Profiling

- [ ] Implementar script de benchmark reproducible
- [ ] Medir tiempo por PDF (promedio, p50, p95, p99)
- [ ] Medir uso de memoria (peak, average)
- [ ] Comparar contra sistema actual

### Criterio de Éxito Etapa 2

✅ Performance targets:

- Tiempo por PDF: <200ms (vs ~500ms actual)
- Speedup total: ≥2.5x
- Memoria: <500MB para 100 PDFs

### Entregabless

- Código optimizado
- Reporte de benchmark con gráficos
- Guía de tuning de parámetros

---

## ETAPA 3: Hardening y Producción (Semana 4)

### Objetivoss

Preparar el servicio para producción en Windows Server.

### Tarease

#### 3.1 Robustez

- [ ] Implementar límites configurables:
  - `MAX_FILE_SIZE`: 10 MB
  - `MAX_FILES`: 100
  - `MAX_CONCURRENCY`: 50
  - `FILE_TIMEOUT`: 30s
  - `REQUEST_TIMEOUT`: 600s
- [ ] Manejo de archivos temporales con limpieza automática
- [ ] Graceful shutdown con cleanup
- [ ] Retry logic para operaciones de I/O

#### 3.2 Logging y Observabilidad

- [ ] Logging estructurado JSON con structlog
- [ ] Request ID tracking end-to-end
- [ ] Métricas Prometheus (opcional)
- [ ] Health check endpoint completo

#### 3.3 Seguridad

- [ ] Validación estricta de inputs
- [ ] Sanitización de nombres de archivo
- [ ] Protección contra path traversal
- [ ] No ejecución de contenido embebido
- [ ] Rate limiting básico

#### 3.4 Empaquetado Windows

- [ ] Crear spec file para PyInstaller
- [ ] Generar .exe standalone
- [ ] Crear scripts de instalación NSSM:
  - `install_service.bat`
  - `uninstall_service.bat`
  - `restart_service.bat`
- [ ] Configurar auto-restart en fallo
- [ ] Documentar requisitos de sistema

#### 3.5 Documentación

- [ ] README completo
- [ ] Guía de instalación Windows
- [ ] Guía de troubleshooting
- [ ] Guía de actualización

### Criterio de Éxito Etapa 3

✅ Producción-ready:

- Servicio Windows estable 24/7
- Logs estructurados para debugging
- Manejo robusto de errores
- Instalación en <5 minutos

### Entregablese

- Ejecutable .exe
- Scripts de instalación
- Documentación completa
- Checklist de despliegue

---

## Timeline Visual

```text
Semana 1-2: ETAPA 1 - Feature Parity
├── Día 1-2:   Setup proyecto
├── Día 2-3:   Utilidades base
├── Día 3-6:   Extractores (CRT, Homolog., SOAP, Permiso)
├── Día 6-8:   Servicios (PDF, Excel)
├── Día 8-9:   API FastAPI
└── Día 9-10:  Tests compatibilidad

Semana 3: ETAPA 2 - Optimización
├── Día 1-2:   Optimización PDF
├── Día 3-4:   Optimización procesamiento
├── Día 4-5:   Optimización Excel
└── Día 5-7:   Benchmark y ajustes

Semana 4: ETAPA 3 - Hardening
├── Día 1-2:   Robustez y límites
├── Día 3-4:   Logging y seguridad
├── Día 4-5:   Empaquetado Windows
└── Día 6-7:   Documentación y entrega
```

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |

|--------|--------------|---------|------------|
| Diferencias sutiles en regex Python vs JS | Media | Alto | Tests exhaustivos, comparación celda a celda |
| PyMuPDF extrae texto diferente a pdf2json | Media | Alto | Normalizar espacios/saltos, ajustar regex |
| Performance no alcanza target | Baja | Medio | Profiling temprano, optimización incremental |
| Problemas con PyInstaller en Windows | Media | Medio | Probar empaquetado desde Etapa 1 |
| Incompatibilidad con Excel existente | Baja | Alto | Validar estructura con archivos reales |

---

## Checklist de Validación Final

### Funcionalidad

- [ ] Los 4 formatos extraen todos los campos correctamente
- [ ] Validaciones best-effort funcionan igual
- [ ] Excel tiene mismas columnas y orden
- [ ] Hoja "Estadísticas" incluye fallidos
- [ ] Eventos SSE tienen misma estructura
- [ ] returnRegex funciona para Permiso Circulación

### Performance

- [ ] Benchmark documenta mejora ≥2x
- [ ] Uso de memoria aceptable (<1GB para 100 PDFs)
- [ ] No hay memory leaks en procesamiento largo

### Producción

- [ ] Servicio inicia correctamente en Windows
- [ ] Logs se escriben en archivo
- [ ] Health check responde
- [ ] Servicio se recupera de errores
- [ ] Instalación documentada paso a paso

---

## Próximos Pasos Inmediatos

1. **Crear estructura de carpetas** → Ver `ESTRUCTURA_PROYECTO.md`
2. **Instalar dependencias** → `pip install -r requirements.txt`
3. **Ejecutar primer test** → `pytest tests/ -v`
4. **Portar primer extractor** → Comenzar con CRT (más complejo)
