@echo off
REM ============================================================================
REM run_test.bat - Verarbeitet Projekt-Dateien mit sproject.py
REM
REM Usage:
REM   run_test.bat                      - Verarbeitet alle .json Dateien im examples Ordner
REM   run_test.bat <filename>           - Verarbeitet eine einzelne Projekt-Datei
REM   run_test.bat --create-graph       - Erstellt Abhängigkeitsdiagramme für alle Projekte
REM   run_test.bat <filename> --create-graph - Erstellt Graph für einzelne Datei
REM
REM ============================================================================

REM Wenn keine Parameter, verarbeite alle examples
if [%1]==[] goto process_all_examples

REM Umgebungsvariablen laden
call "%~dp0setenv.bat"

if exist "%~dp0_setenv.bat" (
    echo Lade lokale Umgebungseinstellungen aus _setenv.bat...
    call "%~dp0_setenv.bat"
)

REM Prüfe auf --create-graph Flag
set "CREATE_GRAPH="
if /i "%1"=="--create-graph" (
    set "CREATE_GRAPH=--create-graph"
    goto process_all_examples
)

REM Einzelne Datei verarbeiten
set "PROJECT_FILE=%~1"

REM Wenn Datei nicht absoluter Pfad ist, schaue im examples Ordner
if not exist "%PROJECT_FILE%" (
    set "PROJECT_FILE=%PV_EXAMPLES%\%~1"
)

REM Füge .json hinzu falls nicht vorhanden
if not "%PROJECT_FILE:~-5%"==".json" (
    set "PROJECT_FILE=%PROJECT_FILE%.json"
)

if not exist "%PROJECT_FILE%" (
    echo Fehler: Projektdatei nicht gefunden: %PROJECT_FILE%
    echo.
    goto usage
)

REM Sammle zusätzliche Parameter
set "PARAMS=--project "%PROJECT_FILE%""
:parse_args
if "%2"=="" goto run_test
if /i "%2"=="--create-graph" (
    set "PARAMS=%PARAMS% --create-graph"
)
shift
goto parse_args

:run_test
echo.
echo ============================================================================
echo Verarbeite Projektdatei: %PROJECT_FILE%
echo Parameter: %PARAMS%
echo ============================================================================
echo.

REM Wechsle ins Projektverzeichnis und führe sproject.py aus
pushd "%PV_LIB%"

python sproject.py %PARAMS%
set TEST_RESULT=%ERRORLEVEL%

popd

echo.
echo ============================================================================
if %TEST_RESULT% EQU 0 (
    echo Verarbeitung erfolgreich abgeschlossen
) else (
    echo Verarbeitung fehlgeschlagen
)
echo ============================================================================
echo.

exit /B %TEST_RESULT%

:process_all_examples
REM Umgebungsvariablen laden falls noch nicht geschehen
call "%~dp0setenv.bat"

echo.
echo ============================================================================
echo Verarbeite alle JSON-Dateien im examples Ordner
if defined CREATE_GRAPH echo Erstelle Abhängigkeitsdiagramme
echo ============================================================================
echo.

REM Wechsle ins lib Verzeichnis
pushd "%PV_LIB%"

REM Verarbeite alle .json Dateien im examples Ordner
for %%F in ("%PV_EXAMPLES%\*.json") do (
    echo.
    echo --- Verarbeite: %%~nxF ---
    if defined CREATE_GRAPH (
        python sproject.py --project "%%F" --create-graph
    ) else (
        python sproject.py --project "%%F"
    )
    echo.
)

popd

echo.
echo ============================================================================
echo Alle Dateien verarbeitet
echo ============================================================================
echo.

exit /B 0

:usage
echo.
echo Usage: %~nx0 [filename] [OPTIONS]
echo.
echo Argumente:
echo   filename          Name der Projektdatei (mit oder ohne .json Erweiterung)
echo                     Die Datei wird im examples Ordner gesucht.
echo                     Ohne Angabe werden alle .json Dateien im examples Ordner verarbeitet.
echo.
echo Optionen:
echo   --create-graph    Erstellt Abhängigkeitsdiagramm(e) als PNG-Datei(en)
echo.
echo Beispiele:
echo   %~nx0                          Verarbeitet alle .json Dateien im examples Ordner
echo   %~nx0 --create-graph           Erstellt Graphen für alle Projektdateien
echo   %~nx0 tankdesign               Verarbeitet tankdesign.json
echo   %~nx0 tankdesign.json          Verarbeitet tankdesign.json
echo   %~nx0 tankdesign --create-graph  Erstellt nur den Graphen für tankdesign.json
echo.
exit /B 1
