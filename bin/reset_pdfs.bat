@echo off
REM Reset PDFs - Undo the last rename operation using the renamer's --undo switch
REM This uses the JSON log to restore files to their original names and locations

echo ====================================
echo PDF RESET TOOL
echo ====================================
echo.

REM Load environment variables
call "%~dp0setenv.bat"

if not defined PROJECT (
    echo ERROR: Environment variables not set. Please run setenv.bat first.
    pause
    exit /b 1
)

echo Rueckgaengig-Machung der letzten Umbenennung...
echo.

REM Activate virtual environment and run renamer with --undo
call manage_interpreter.bat activate_interpreter
python "%PV_LIB%\renamer.py" --undo  %*
call manage_interpreter.bat deactivate_interpreter
set UNDO_RESULT=%errorlevel%


echo.

if %UNDO_RESULT% equ 0 (
    echo ====================================
    echo RESET COMPLETE
    echo ====================================
    echo PDFs wurden erfolgreich zurueckverschoben.
    echo.
) else (
    echo ====================================
    echo RESET FAILED
    echo ====================================
    echo Fehler beim Zurueckverschieben der PDFs.
    echo.
)

pause