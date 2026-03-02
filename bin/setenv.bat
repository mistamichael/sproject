@echo off

REM ================================================================
REM PDF Rechnungen Organisator - Umgebungsvariablen Setup
REM ================================================================

echo Setting up environment variables for PDF Organizer...

REM Basis-Projektpfad (aktueller Ordner)
set "PROJECT=%~dp0.."
if "%PROJECT:~-6%"=="bin\.." set "PROJECT=%PROJECT:~0,-6%"
if "%PROJECT:~-1%"=="\" set "PROJECT=%PROJECT:~0,-1%"

REM Pfade für verschiedene Komponenten
set "PV_BIN=%PROJECT%\bin"
set "PV_LIB=%PROJECT%\lib"
set "PV_DATA=%PROJECT%\data"
set "PV_CFG=%PROJECT%\cfg"
set "PV_LOG=%PROJECT%\log"
set "PV_RESULTS=%PROJECT%\results"

REM Python-Pfad erweitern (nur wenn noch nicht vorhanden)
echo %PYTHONPATH% | find /i "%PV_LIB%" >nul
if errorlevel 1 (
    set "PYTHONPATH=%PV_LIB%;%PYTHONPATH%"
) else (
    REM Path ist bereits in PYTHONPATH enthalten, nicht erneut hinzufügen
)

REM Ordner erstellen falls sie nicht existieren
if not exist "%PV_BIN%" mkdir "%PV_BIN%"
if not exist "%PV_CFG%" mkdir "%PV_CFG%"
if not exist "%PV_LIB%" mkdir "%PV_LIB%"
if not exist "%PV_DATA%" mkdir "%PV_DATA%"
if not exist "%PV_LOG%" mkdir "%PV_LOG%"
if not exist "%PV_RESULTS%" mkdir "%PV_RESULTS%"

REM Umgebungsvariablen anzeigen
echo.
echo ================================================================
echo PDF ORGANIZER ENVIRONMENT SETUP COMPLETE
echo ================================================================
echo PROJECT         = %PROJECT%
echo PV_BIN          = %PV_BIN%
echo PV_CFG         = %PV_CFG%
echo PV_LIB          = %PV_LIB%
echo PV_DATA         = %PV_DATA%
echo PV_RESULTS      = %PV_RESULTS%
echo PV_LOG          = %PV_LOG%
echo PYTHONPATH      = %PYTHONPATH%
echo ================================================================
echo.
echo Ready to use! Run: bin\run_organizer.bat
echo.

REM Optionally keep window open
if "%1"=="--keep-open" pause
