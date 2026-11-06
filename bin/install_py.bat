call setenv.bat
py -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" 2>nul
if errorlevel 1 (
    echo FEHLER: Python 3.12 oder hoeher erforderlich ^(py -V pruefen^).
    exit /b 1
)
if not exist %PROJECT%\.venv (
   ECHO Initialisiere Python virtual environment...
   py -m venv %PROJECT%\.venv --upgrade-deps
   ECHO Erfolgreich.

   call %PROJECT%\.venv\Scripts\activate.bat
   ECHO Installiere erforderliche Python Packages...
   pip install -r %PROJECT%/requirements.txt -q
   ECHO Erfolgreich
   deactivate

    ) ELSE (
        ECHO Erforderliche Python Packages bereits installiert!
    )
