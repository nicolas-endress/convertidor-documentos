@echo off
REM ===========================================================
REM Script de instalación del servicio Windows para PDF Converter
REM Usa NSSM (Non-Sucking Service Manager)
REM ===========================================================

setlocal enabledelayedexpansion

REM Configuración
set SERVICE_NAME=PDFConverterService
set DISPLAY_NAME=PDF Converter Python Service
set DESCRIPTION=Servicio de conversión de PDF a Excel con FastAPI

REM Rutas (modificar según instalación)
set INSTALL_DIR=%~dp0..
set EXE_PATH=%INSTALL_DIR%\dist\main.exe
set NSSM_PATH=%INSTALL_DIR%\nssm.exe
set LOG_DIR=%INSTALL_DIR%\logs

REM Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Este script debe ejecutarse como Administrador.
    echo Haga clic derecho en el archivo y seleccione "Ejecutar como administrador".
    pause
    exit /b 1
)

REM Verificar que NSSM existe
if not exist "%NSSM_PATH%" (
    echo [ERROR] No se encontró nssm.exe en %NSSM_PATH%
    echo Descargue NSSM de https://nssm.cc/download
    pause
    exit /b 1
)

REM Verificar que el ejecutable existe
if not exist "%EXE_PATH%" (
    echo [ERROR] No se encontró el ejecutable en %EXE_PATH%
    echo Ejecute primero: pyinstaller main.spec
    pause
    exit /b 1
)

REM Crear directorio de logs si no existe
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    echo [INFO] Directorio de logs creado: %LOG_DIR%
)

echo ===========================================================
echo Instalando servicio: %SERVICE_NAME%
echo ===========================================================

REM Detener servicio si ya existe
echo [INFO] Verificando si el servicio ya existe...
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] El servicio ya existe. Deteniendo...
    "%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm >nul 2>&1
    echo [INFO] Servicio anterior removido.
)

REM Instalar el servicio
echo [INFO] Instalando nuevo servicio...
"%NSSM_PATH%" install %SERVICE_NAME% "%EXE_PATH%"

if %errorlevel% neq 0 (
    echo [ERROR] Falló la instalación del servicio.
    pause
    exit /b 1
)

REM Configurar el servicio
echo [INFO] Configurando servicio...

REM Nombre para mostrar y descripción
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
"%NSSM_PATH%" set %SERVICE_NAME% Description "%DESCRIPTION%"

REM Directorio de trabajo
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"

REM Configurar logs de stdout y stderr
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%LOG_DIR%\service_stdout.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%LOG_DIR%\service_stderr.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStdoutCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppStderrCreationDisposition 4
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateOnline 1
"%NSSM_PATH%" set %SERVICE_NAME% AppRotateBytes 10485760

REM Configurar reinicio automático
"%NSSM_PATH%" set %SERVICE_NAME% AppRestartDelay 5000
"%NSSM_PATH%" set %SERVICE_NAME% AppThrottle 10000

REM Tipo de inicio (automático)
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Variables de entorno (opcional - modificar según necesidad)
REM "%NSSM_PATH%" set %SERVICE_NAME% AppEnvironmentExtra HOST=0.0.0.0 PORT=8000 LOG_LEVEL=INFO

echo [INFO] Servicio configurado correctamente.

REM Iniciar el servicio
echo [INFO] Iniciando servicio...
"%NSSM_PATH%" start %SERVICE_NAME%

if %errorlevel% neq 0 (
    echo [ERROR] Falló al iniciar el servicio.
    echo Revise los logs en: %LOG_DIR%
    pause
    exit /b 1
)

REM Verificar estado
timeout /t 3 /nobreak >nul
sc query %SERVICE_NAME% | findstr "RUNNING" >nul
if %errorlevel% equ 0 (
    echo.
    echo ===========================================================
    echo [OK] Servicio instalado e iniciado correctamente!
    echo ===========================================================
    echo.
    echo Nombre del servicio: %SERVICE_NAME%
    echo Endpoint: http://localhost:8000
    echo Health check: http://localhost:8000/health
    echo Logs: %LOG_DIR%
    echo.
    echo Comandos útiles:
    echo   - Estado:    sc query %SERVICE_NAME%
    echo   - Detener:   nssm stop %SERVICE_NAME%
    echo   - Iniciar:   nssm start %SERVICE_NAME%
    echo   - Reiniciar: nssm restart %SERVICE_NAME%
    echo   - Desinstalar: scripts\uninstall_service.bat
    echo.
) else (
    echo [WARN] El servicio se instaló pero puede que no esté corriendo.
    echo Verifique el estado con: sc query %SERVICE_NAME%
    echo Revise los logs en: %LOG_DIR%
)

pause
exit /b 0
