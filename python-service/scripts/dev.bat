@echo off
REM ===========================================================
REM Script de desarrollo para PDF Converter Python Service
REM ===========================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%\..

REM Comando recibido
set CMD=%1

if "%CMD%"=="" (
    echo Uso: dev.bat [comando]
    echo.
    echo Comandos disponibles:
    echo   install    - Instalar dependencias
    echo   dev        - Iniciar servidor de desarrollo
    echo   test       - Ejecutar tests
    echo   test-cov   - Ejecutar tests con cobertura
    echo   lint       - Ejecutar linter (ruff)
    echo   format     - Formatear código
    echo   build      - Crear ejecutable con PyInstaller
    echo   clean      - Limpiar archivos temporales
    echo.
    exit /b 0
)

if "%CMD%"=="install" (
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    goto :end
)

if "%CMD%"=="dev" (
    echo [INFO] Iniciando servidor de desarrollo...
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    goto :end
)

if "%CMD%"=="test" (
    echo [INFO] Ejecutando tests...
    pytest tests/ -v
    goto :end
)

if "%CMD%"=="test-cov" (
    echo [INFO] Ejecutando tests con cobertura...
    pytest tests/ -v --cov=app --cov-report=html --cov-report=term
    echo [INFO] Reporte HTML generado en: htmlcov/index.html
    goto :end
)

if "%CMD%"=="lint" (
    echo [INFO] Ejecutando linter...
    ruff check app/ tests/
    goto :end
)

if "%CMD%"=="format" (
    echo [INFO] Formateando código...
    ruff format app/ tests/
    ruff check --fix app/ tests/
    goto :end
)

if "%CMD%"=="build" (
    echo [INFO] Creando ejecutable...
    pyinstaller main.spec --clean
    echo [INFO] Ejecutable creado en: dist/main.exe
    goto :end
)

if "%CMD%"=="clean" (
    echo [INFO] Limpiando archivos temporales...
    rd /s /q __pycache__ 2>nul
    rd /s /q .pytest_cache 2>nul
    rd /s /q .ruff_cache 2>nul
    rd /s /q htmlcov 2>nul
    rd /s /q dist 2>nul
    rd /s /q build 2>nul
    del /q *.spec 2>nul
    echo [INFO] Limpieza completada.
    goto :end
)

echo [ERROR] Comando desconocido: %CMD%
exit /b 1

:end
exit /b 0
