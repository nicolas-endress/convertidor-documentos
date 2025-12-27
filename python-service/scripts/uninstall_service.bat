@echo off
REM ===========================================================
REM Script de desinstalación del servicio Windows para PDF Converter
REM ===========================================================

setlocal enabledelayedexpansion

REM Configuración
set SERVICE_NAME=PDFConverterService
set NSSM_PATH=%~dp0..\nssm.exe

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
    echo [WARN] No se encontró nssm.exe en %NSSM_PATH%
    echo Intentando con NSSM del sistema...
    set NSSM_PATH=nssm
)

echo ===========================================================
echo Desinstalando servicio: %SERVICE_NAME%
echo ===========================================================

REM Verificar si el servicio existe
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] El servicio %SERVICE_NAME% no está instalado.
    pause
    exit /b 0
)

REM Detener el servicio
echo [INFO] Deteniendo servicio...
"%NSSM_PATH%" stop %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Servicio detenido.
) else (
    echo [WARN] El servicio puede que ya estuviera detenido.
)

REM Esperar a que se detenga
timeout /t 3 /nobreak >nul

REM Remover el servicio
echo [INFO] Removiendo servicio...
"%NSSM_PATH%" remove %SERVICE_NAME% confirm

if %errorlevel% equ 0 (
    echo.
    echo ===========================================================
    echo [OK] Servicio desinstalado correctamente.
    echo ===========================================================
) else (
    echo [ERROR] Hubo un problema al desinstalar el servicio.
    echo Intente removerlo manualmente:
    echo   sc delete %SERVICE_NAME%
)

pause
exit /b 0
