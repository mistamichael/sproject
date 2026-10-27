@echo off
REM Startet den sproject MCP-Server (KI-Schnittstelle, siehe doc/de/ki-schnittstelle.md)
REM   bin\mcp_server.bat                        stdio (fuer Claude Code / Claude Desktop)
REM   bin\mcp_server.bat --http --port 8765     HTTP: http://127.0.0.1:8765/mcp
REM Im stdio-Modus darf nichts auf stdout erscheinen - daher setenv ohne Ausgabe.

CALL "%~dp0setenv.bat" >nul

IF NOT EXIST "%PROJECT%\.venv\Scripts\python.exe" (
    echo ERROR: .venv nicht gefunden - zuerst bin\install_py.bat ausfuehren 1>&2
    exit /b 1
)

pushd "%PROJECT%"
"%PROJECT%\.venv\Scripts\python.exe" -m mcp_server %*
set PYTHON_EXIT=%ERRORLEVEL%
popd
exit /b %PYTHON_EXIT%
