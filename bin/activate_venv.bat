@echo off 
REM Aktiviert die virtuelle Python-Umgebung 
cd /d "%~dp0\.." 
call venv\Scripts\activate.bat 
echo Virtuelle Umgebung aktiviert. 
echo Python-Version: 
python --version 
echo. 
echo Installierte Pakete: 
pip list 
