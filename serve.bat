@echo off
REM PAM dashboard launcher
REM Starts a local web server on http://localhost:8765 and opens dashboard.html
cd /d "%~dp0"
echo Starting PAM dashboard at http://localhost:8765/dashboard.html
start "" "http://localhost:8765/dashboard.html"
python -m http.server 8765
