@echo off
where pythonw >nul 2>&1
if %errorlevel%==0 (
    pythonw "%~dp0postit.py"
) else (
    start /b python "%~dp0postit.py"
)
