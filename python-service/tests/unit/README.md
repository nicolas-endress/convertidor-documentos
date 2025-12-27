# Tests unitarios para Python Service

Este directorio contiene los tests unitarios para cada módulo del servicio.

## Estructura

```text
unit/
├── test_crt_extractor.py          # Tests para extractor CRT
├── test_homologacion_extractor.py # Tests para extractor Homologación
├── test_soap_extractor.py         # Tests para extractor SOAP
├── test_permiso_extractor.py      # Tests para extractor Permiso Circulación
```

## Ejecución

```bash
# Todos los tests unitarios
pytest tests/unit/ -v

# Test específico
pytest tests/unit/test_crt_extractor.py -v

# Con cobertura
pytest tests/unit/ --cov=app/extractors --cov-report=html
```

## Convenciones

- Cada test verifica una funcionalidad específica
- Los nombres de test describen el comportamiento esperado
- Se usan fixtures de `conftest.py` para datos compartidos
