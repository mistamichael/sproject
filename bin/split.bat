@echo off
CALL manage_interpreter.bat activate
if errorlevel 1 (
    echo ERROR: Failed to activate Python environment
    exit /b 1
)

pushd "%PROJECT%"

"%VIRTUAL_ENV%\Scripts\python.exe" -m lib.split %*
set PYTHON_EXIT=%ERRORLEVEL%

popd
CALL manage_interpreter.bat deactivate
exit /b %PYTHON_EXIT%
