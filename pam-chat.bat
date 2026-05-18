@echo off
REM Launch Pam — local chat server + browser
cd /d "%~dp0"
start "" "http://localhost:8765"
python pam-chat\server.py
