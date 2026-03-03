@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM run_test.bat - Verarbeitet Projekt-Dateien mit sproject.py
REM
REM Usage:
REM   run_test.bat                      - Verarbeitet alle .json Dateien im examples Ordner
REM   run_test.bat <filename>           - Verarbeitet eine einzelne Projekt-Datei
REM   run_test.bat --create_svg_graph       - Erstellt Abhängigkeitsdiagramme für alle Projekte
REM   run_test.bat <filename> --create_svg_graph - Erstellt Graph für einzelne Datei
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

REM Prüfe auf --create_svg_graph Flag
set "CREATE_GRAPH="
if /i "%1"=="--create_svg_graph" (
    set "CREATE_GRAPH=--create_svg_graph"
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
if /i "%2"=="--create_svg_graph" (
    set "PARAMS=%PARAMS% --create_svg_graph"
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

REM Vergleiche Ergebnisse und aktualisiere Referenzen
if %TEST_RESULT% EQU 0 (
    call :compare_results "%PROJECT_FILE%"
)

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
        python sproject.py --project "%%F" --create_svg_graph
        set LAST_RESULT=!ERRORLEVEL!
    ) else (
        python sproject.py --project "%%F"
        set LAST_RESULT=!ERRORLEVEL!
    )

    REM Vergleiche Ergebnisse wenn erfolgreich
    if !LAST_RESULT! EQU 0 (
        popd
        call :compare_results "%%F"
        pushd "%PV_LIB%"
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

:compare_results
REM ============================================================================
REM Vergleicht Ergebnisdateien mit Referenzdaten
REM Parameter: %1 = Projektdatei (z.B. examples\tankdesign.json)
REM ============================================================================
setlocal

REM Extrahiere Basisnamen der Projektdatei (ohne Pfad und Erweiterung)
for %%F in ("%~1") do set "BASENAME=%%~nF"

echo.
echo --- Vergleiche Ergebnisse fuer %BASENAME% ---
echo.

REM Erstelle Referenzverzeichnis falls nicht vorhanden
if not exist "%PV_EXAMPLE_RESULTS%" mkdir "%PV_EXAMPLE_RESULTS%"

REM Durchsuche alle generierten Dateien im results Ordner
set "DIFFERENCES_FOUND=0"
set "NEW_FILES=0"

for %%T in (json svg png) do (
    if exist "%PV_RESULTS%\%BASENAME%*.%%T" (
        for %%R in ("%PV_RESULTS%\%BASENAME%*.%%T") do (
            set "RESULT_FILE=%%R"
            set "RESULT_NAME=%%~nxR"
            set "REFERENCE_FILE=%PV_EXAMPLE_RESULTS%\%%~nxR"

            if exist "!REFERENCE_FILE!" (
                REM Vergleiche mit Referenz
                fc /b "!RESULT_FILE!" "!REFERENCE_FILE!" >nul 2>&1
                if errorlevel 1 (
                    echo [DIFF] !RESULT_NAME! unterscheidet sich von Referenz
                    set "DIFFERENCES_FOUND=1"
                ) else (
                    echo [OK]   !RESULT_NAME! stimmt mit Referenz ueberein
                )
            ) else (
                REM Keine Referenz vorhanden - kopiere als neue Referenz
                echo [NEU]  !RESULT_NAME! - erstelle Referenzdatei
                copy /Y "!RESULT_FILE!" "!REFERENCE_FILE!" >nul
                set "NEW_FILES=1"
            )
        )
    )
)

if %NEW_FILES% EQU 1 (
    echo.
    echo Neue Referenzdateien wurden in %PV_EXAMPLE_RESULTS% erstellt.
)

if %DIFFERENCES_FOUND% EQU 1 (
    echo.
    echo WARNUNG: Unterschiede zu Referenzdaten gefunden!
    echo Pruefe die Aenderungen und aktualisiere ggf. die Referenz manuell.
)

echo.
endlocal
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
echo   --create_svg_graph    Erstellt Abhängigkeitsdiagramm(e) als PNG-Datei(en)
echo.
echo Beispiele:
echo   %~nx0                          Verarbeitet alle .json Dateien im examples Ordner
echo   %~nx0 --create_svg_graph           Erstellt Graphen für alle Projektdateien
echo   %~nx0 tankdesign               Verarbeitet tankdesign.json
echo   %~nx0 tankdesign.json          Verarbeitet tankdesign.json
echo   %~nx0 tankdesign --create_svg_graph  Erstellt nur den Graphen für tankdesign.json
echo.
echo Hinweis:
echo   Ergebnisse werden in %PV_RESULTS% erzeugt und automatisch mit
echo   Referenzdaten in %PV_EXAMPLE_RESULTS% verglichen.
echo.
exit /B 1
