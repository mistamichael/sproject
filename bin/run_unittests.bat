@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM run_unittests.bat - Führt Unit-Tests für sproject aus
REM
REM Usage:
REM   run_unittests.bat                 - Führt alle Unit-Tests aus
REM   run_unittests.bat -v              - Führt Tests mit verbose Ausgabe aus
REM   run_unittests.bat <TestClass>     - Führt nur eine Test-Klasse aus
REM   run_unittests.bat <TestClass.test_method> - Führt nur einen Test aus
REM
REM Beispiele:
REM   run_unittests.bat
REM   run_unittests.bat -v
REM   run_unittests.bat TestCPMCalculation
REM   run_unittests.bat TestCPMCalculation.test_cpm_critical_path
REM
REM ============================================================================

REM Umgebungsvariablen laden
call "%~dp0setenv.bat"

if exist "%~dp0_setenv.bat" (
    echo Lade lokale Umgebungseinstellungen aus _setenv.bat...
    call "%~dp0_setenv.bat"
)

REM Python-Pfad prüfen
where python >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden!
    echo Bitte installieren Sie Python oder aktivieren Sie die virtuelle Umgebung.
    exit /B 1
)

REM Setze PROJECT als Root-Verzeichnis
set "PROJECT_ROOT=%PROJECT%"
if not defined PROJECT_ROOT (
    REM Fallback: Berechne aus Batch-Pfad
    set "PROJECT_ROOT=%~dp0.."
)

echo.
echo ============================================================================
echo sproject Unit-Tests
echo ============================================================================
echo.
echo Python:
python --version
echo Tests: %PROJECT_ROOT%\tests\test_sproject.py
echo.

REM Prüfe ob Test-Datei existiert
if not exist "%PROJECT_ROOT%\tests\test_sproject.py" (
    echo FEHLER: Test-Datei nicht gefunden!
    echo Erwartet: %PROJECT_ROOT%\tests\test_sproject.py
    exit /B 1
)

REM Wechsle ins Root-Verzeichnis
pushd "%PROJECT_ROOT%"

REM Parameter verarbeiten
set "TEST_PARAMS="
set "VERBOSE="
set "SPECIFIC_TEST="

:parse_args
if "%1"=="" goto run_tests

if /i "%1"=="-v" (
    set "VERBOSE=1"
    shift
    goto parse_args
)

if /i "%1"=="--verbose" (
    set "VERBOSE=1"
    shift
    goto parse_args
)

if /i "%1"=="-h" goto usage
if /i "%1"=="--help" goto usage
if /i "%1"=="/?" goto usage

REM Ansonsten ist es ein spezifischer Test
set "SPECIFIC_TEST=%1"
shift
goto parse_args

:run_tests
echo ============================================================================

if defined SPECIFIC_TEST (
    echo Fuehre spezifischen Test aus: %SPECIFIC_TEST%
    echo ============================================================================
    echo.

    if defined VERBOSE (
        python -m unittest tests.test_sproject.%SPECIFIC_TEST% -v
    ) else (
        python -m unittest tests.test_sproject.%SPECIFIC_TEST%
    )
) else (
    echo Fuehre alle Unit-Tests aus...
    echo ============================================================================
    echo.

    REM Führe alle Tests aus
    python tests\test_sproject.py
)

set TEST_RESULT=%ERRORLEVEL%

popd

echo.
echo ============================================================================
if %TEST_RESULT% EQU 0 (
    echo [SUCCESS] Alle Tests erfolgreich abgeschlossen!
    echo ============================================================================
    echo.
    exit /B 0
) else (
    echo [FAILED] Tests fehlgeschlagen!
    echo ============================================================================
    echo.
    exit /B 1
)

:usage
echo.
echo ============================================================================
echo run_unittests.bat - Fuehrt Unit-Tests fuer sproject aus
echo ============================================================================
echo.
echo Usage: %~nx0 [OPTIONS] [TEST]
echo.
echo Optionen:
echo   -v, --verbose     Ausfuehrliche Test-Ausgabe
echo   -h, --help, /?    Diese Hilfe anzeigen
echo.
echo Test-Auswahl:
echo   (keine Angabe)                  Fuehrt alle Tests aus
echo   TestClassName                   Fuehrt alle Tests einer Klasse aus
echo   TestClassName.test_method       Fuehrt einen spezifischen Test aus
echo.
echo Verfuegbare Test-Klassen:
echo   TestProjectLoading              Tests fuer Projekt-Laden
echo   TestProjectMethods              Tests fuer Projekt-Methoden
echo   TestCPMCalculation              Tests fuer CPM-Berechnung
echo   TestProjectExpansion            Tests fuer Projekt-Expansion
echo   TestReportModels                Tests fuer Report-Modelle
echo   TestProjectSaveLoad             Tests fuer Speichern/Laden
echo   TestExcelExport                 Tests fuer Excel-Export
echo   TestPersonProject               Tests fuer PersonProject
echo   TestTaskValidation              Tests fuer Task-Validierung
echo.
echo Beispiele:
echo   %~nx0                                           - Alle Tests ausfuehren
echo   %~nx0 -v                                        - Alle Tests (verbose)
echo   %~nx0 TestCPMCalculation                        - Nur CPM-Tests
echo   %~nx0 TestCPMCalculation.test_cpm_critical_path - Nur einen Test
echo.
echo Weitere Informationen:
echo   Siehe tests\README.md fuer detaillierte Test-Dokumentation
echo.
echo ============================================================================
echo.
exit /B 0
