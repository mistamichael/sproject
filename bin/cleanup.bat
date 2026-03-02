@echo off
REM ================================================================
REM PDF Rechnungen Organisator - Cleanup Skript
REM ================================================================

REM Lade Umgebungsvariablen
call "%~dp0\setenv.bat"

REM Prüfe ob PV_RESULTS nach dem Laden gesetzt ist
if not defined PV_RESULTS (
    echo Fehler: Die Umgebungsvariable PV_RESULTS konnte nicht gesetzt werden!
    echo Bitte prüfen Sie die setenv.bat auf Fehler.
    echo.
    pause
    exit /b 1
)

echo PDF Rechnungen Organisator - Cleanup
echo ================================================================

echo.
echo Was möchten Sie bereinigen?
echo.
echo [1] Nur Ergebnisse löschen (%PV_RESULTS%\*)
echo [2] Virtuelle Umgebung löschen (venv\)
echo [3] Alles löschen (venv + %PV_RESULTS% + __pycache__)
echo [4] Abbrechen
echo.
set /p choice="Ihre Wahl (1-4): "

if "%choice%"=="1" goto clean_results
if "%choice%"=="2" goto clean_venv
if "%choice%"=="3" goto clean_all
if "%choice%"=="4" goto abort
goto invalid

:clean_results
echo.
echo Lösche Ergebnisse...
if exist "%PV_RESULTS%" (
    rmdir /s /q "%PV_RESULTS%"
    echo Ergebnisse-Ordner gelöscht.
) else (
    echo Kein Ergebnisse-Ordner vorhanden.
)
goto done

:clean_venv
echo.
echo Lösche virtuelle Umgebung...
if exist "%PROJECT%\venv" (
    rmdir /s /q "%PROJECT%\venv"
    echo Virtuelle Umgebung gelöscht.
    echo Führen Sie bin\setup_env.bat aus, um sie neu zu erstellen.
) else (
    echo Keine virtuelle Umgebung vorhanden.
)
goto done

:clean_all
echo.
echo Lösche alles (venv + ergebnisse + cache)...
if exist "%PROJECT%\venv" rmdir /s /q "%PROJECT%\venv"
if exist "%PV_RESULTS%" rmdir /s /q "%PV_RESULTS%"
if exist "%PV_LIB%\__pycache__" rmdir /s /q "%PV_LIB%\__pycache__"
if exist "%PROJECT%\__pycache__" rmdir /s /q "%PROJECT%\__pycache__"
echo Alles bereinigt.
echo Führen Sie bin\setup_env.bat aus, um neu zu beginnen.
goto done

:invalid
echo.
echo Ungültige Auswahl!
goto abort

:abort
echo.
echo Cleanup abgebrochen.
goto end

:done
echo.
echo Cleanup abgeschlossen.

:end
echo.
pause
