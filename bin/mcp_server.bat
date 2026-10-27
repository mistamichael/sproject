@echo off
REM ================================================================
REM SPROJECT - MCP-Server (KI-Schnittstelle, siehe doc/de/ki-schnittstelle.md)
REM ================================================================
REM Es laeuft genau EIN moncapro-Server. Claude Code (.mcp.json) und die GUI
REM (Menue Server -> Verbinden) verbinden sich beide mit ihm.
REM
REM   bin\mcp_server.bat                  HTTP auf http://127.0.0.1:8765/mcp (Standard)
REM   bin\mcp_server.bat --port [N]       HTTP auf Port N (ohne N: 8765)
REM   bin\mcp_server.bat --claude         stdio - nur fuer Skripte/Tests, die GUI kann sich nicht verbinden
REM   bin\mcp_server.bat --help           diese Hilfe
REM Weitere Argumente gehen an den Server, z. B. --project examples\tankdesign.json
REM Im stdio-Modus darf nichts auf stdout erscheinen - daher setenv ohne Ausgabe.
REM ================================================================
setlocal

REM bin-Verzeichnis merken, bevor shift auch %0 verschiebt
set "BIN_DIR=%~dp0"
set "MODE=http"
set "PORT=8765"
set "EXTRA="

:parse
if "%~1"=="" goto run
if /I "%~1"=="--claude" (
    set "MODE=stdio"
    shift
    goto parse
)
if /I "%~1"=="--port" (
    set "MODE=http"
    shift
    goto port_value
)
if /I "%~1"=="--help" goto help
if /I "%~1"=="-h" goto help
set EXTRA=%EXTRA% "%~1"
shift
goto parse

:port_value
REM Optionaler Wert nach --port: nur uebernehmen, wenn er nicht mit - beginnt
set "NEXT=%~1"
if "%NEXT%"=="" goto parse
if "%NEXT:~0,1%"=="-" goto parse
set "PORT=%NEXT%"
shift
goto parse

:run
CALL "%BIN_DIR%setenv.bat" >nul

if not exist "%PROJECT%\.venv\Scripts\python.exe" (
    echo ERROR: .venv nicht gefunden - zuerst bin\install_py.bat ausfuehren 1>&2
    exit /b 1
)

pushd "%PROJECT%"
if "%MODE%"=="http" (
    "%PROJECT%\.venv\Scripts\python.exe" -m moncapro.mcp --http --port %PORT% %EXTRA%
) else (
    "%PROJECT%\.venv\Scripts\python.exe" -m moncapro.mcp %EXTRA%
)
set "PYTHON_EXIT=%ERRORLEVEL%"
popd
exit /b %PYTHON_EXIT%

:help
echo Aufruf: bin\mcp_server.bat [--port [N] ^| --claude] [--project DATEI]
echo.
echo   (ohne)        HTTP auf http://127.0.0.1:8765/mcp - Claude Code und GUI verbinden sich damit
echo   --port [N]    HTTP auf Port N (ohne N: 8765)
echo   --claude      stdio - nur fuer Skripte/Tests, die GUI kann sich dann nicht verbinden
echo   --project F   Projektdatei beim Start oeffnen
echo   --help        diese Hilfe
echo.
echo Es laeuft immer nur ein Server je Port; ein zweiter Start bricht mit einer Meldung ab.
exit /b 0
