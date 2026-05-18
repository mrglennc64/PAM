# PAM dashboard launcher (PowerShell)
# Starts a local web server on http://localhost:8765 and opens dashboard.html

Set-Location -Path $PSScriptRoot
Write-Host "Starting PAM dashboard at http://localhost:8765/dashboard.html"
Start-Process "http://localhost:8765/dashboard.html"
python -m http.server 8765
