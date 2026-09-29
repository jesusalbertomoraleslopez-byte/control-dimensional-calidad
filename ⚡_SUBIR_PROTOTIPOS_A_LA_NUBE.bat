@echo off
chcp 65001 > nul
title SIGRAMA METALES - Sincronizador de Prototipos a Google Cloud

echo ======================================================================
echo    INDUSTRIA SIGRAMA S.A. DE C.V. - INGENIERIA Y CALIDAD 4.0
echo    Sincronizador Automatico de Prototipos a Google Cloud Storage
echo ======================================================================
echo.
echo [1/2] Verificando entorno de ejecucion...

set APP_SCRIPT=C:\Users\albertol\.gemini\antigravity\scratch\control-dimensional-calidad\scripts\gui_sincronizador.py

if exist "%APP_SCRIPT%" (
    echo [2/2] Abriendo interfaz grafica de sincronizacion SIGRAMA...
    start "" py -3.12 "%APP_SCRIPT%"
    exit /b 0
)

set LOCAL_SCRIPT=%~dp0gui_sincronizador.py
if exist "%LOCAL_SCRIPT%" (
    echo [2/2] Abriendo aplicacion local...
    start "" py -3.12 "%LOCAL_SCRIPT%"
    exit /b 0
)

echo.
echo [ERROR] No se localizo el script de sincronizacion.
echo Verifique que el equipo cuente con acceso a la aplicacion de calidad.
pause
