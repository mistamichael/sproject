@echo off

REM ================================================================
REM SPROJECT - Umgebungsvariablen Setup
REM ================================================================

echo Setting up environment variables for SPROJECT ...

REM Basis-Projektpfad (aktueller Ordner)
set "PROJECT=%~dp0.."
if "%PROJECT:~-6%"=="bin\.." set "PROJECT=%PROJECT:~0,-6%"
if "%PROJECT:~-1%"=="\" set "PROJECT=%PROJECT:~0,-1%"

REM Pfade für verschiedene Komponenten
set "PV_BIN=%PROJECT%\bin"
set "PV_DATA=%PROJECT%\data"
set "PV_CFG=%PROJECT%\cfg"
set "PV_THEMES=%PROJECT%\cfg\themes"
set "PV_LOG=%PROJECT%\log"
set "PV_TESTS=%PROJECT%\tests"
set "PV_RESULTS=%PROJECT%\results"
set "PV_WORK=%PROJECT%\work"

REM moncapro (Rechenkern) schreibt in dieselben Ordner. MONCAPRO_CFG bleibt ungesetzt:
REM die Berechnungs-Konfiguration kommt aus dem Paket, PV_CFG enthaelt nur gui.cfg und Themes.
set "MONCAPRO_DATA=%PV_DATA%"
set "MONCAPRO_LOG=%PV_LOG%"
set "MONCAPRO_RESULTS=%PV_RESULTS%"
set "MONCAPRO_WORK=%PV_WORK%"


REM Ordner erstellen falls sie nicht existieren
if not exist "%PV_BIN%" mkdir "%PV_BIN%"
if not exist "%PV_CFG%" mkdir "%PV_CFG%"
if not exist "%PV_DATA%" mkdir "%PV_DATA%"
if not exist "%PV_LOG%" mkdir "%PV_LOG%"
if not exist "%PV_RESULTS%" mkdir "%PV_RESULTS%"
if not exist "%PV_WORK%" mkdir "%PV_WORK%"

REM Umgebungsvariablen anzeigen
echo.
echo ================================================================
echo SPROJECT ENVIRONMENT SETUP COMPLETE
echo ================================================================
echo PROJECT         = %PROJECT%
echo PV_BIN          = %PV_BIN%
echo PV_CFG         = %PV_CFG%
echo PV_DATA         = %PV_DATA%
echo PV_RESULTS      = %PV_RESULTS%
echo PV_LOG          = %PV_LOG%
echo ================================================================
echo.
echo Ready to use! Run: bin\create_reports.bat
echo.

REM Optionally keep window open
if "%1"=="--keep-open" pause
