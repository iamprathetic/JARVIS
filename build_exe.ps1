$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== Jarvis EXE Build Script ===" -ForegroundColor Cyan
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
}

Write-Host "Installing dependencies..."
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt pyinstaller==6.15.0
if ($LASTEXITCODE -ne 0) { throw "Installing dependencies failed." }

Write-Host "Building EXE..."
& $python -m PyInstaller --noconfirm JARVIS_gui.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "=== Build Finished! ===" -ForegroundColor Green
Write-Host "Your EXE is in the 'dist' folder."
Write-Host "API keys are NOT bundled into the EXE. Put a .env file next to dist\JARVIS_gui.exe (see .env.example)." -ForegroundColor Yellow
