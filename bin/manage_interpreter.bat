@echo off

IF /I "%1"=="activate" GOTO activate
IF /I "%1"=="deactivate" GOTO deactivate
if /I "%1"=="activate_interpreter" goto activate_interpreter
if /I "%1"=="deactivate_interpreter" goto deactivate_interpreter
goto usage

:activate
REM Interpreter wählen
IF DEFINED NETWORK_PYTHON (
    SET PYTHON_EXE=%NETWORK_PYTHON%\python.exe
) ELSE (
    SET PYTHON_EXE=python
)

REM venv sicherstellen
IF NOT EXIST "%PROJECT%\.venv" (
    "%PYTHON_EXE%" -m venv "%PROJECT%\.venv"
)

REM venv aktivieren
CALL "%PROJECT%\.venv\Scripts\activate.bat"

REM Interpreter festnageln
SET VIRTUAL_ENV_PYTHON=%PYTHON_EXE%
GOTO :eof

:deactivate
CALL "%PROJECT%\.venv\Scripts\deactivate.bat"
SET VIRTUAL_ENV_PYTHON=
GOTO :eof

