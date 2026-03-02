call setenv.bat
if not exist %PROJECT%\.venv (
   ECHO Initialisiere Python virtual environment...
   py -m venv %PROJECT%\.venv --upgrade-deps
   ECHO Erfolgreich.

   call %PROJECT%\.venv\Scripts\activate.bat
   ECHO Installiere erforderliche Python Packages...
   pip install -r %PV_LIB%/requirements.txt -q
   ECHO Erfolgreich
   deactivate

    ) ELSE (
        ECHO Erforderliche Python Packages bereits installiert!
    )
