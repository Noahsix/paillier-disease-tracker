$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name "paillier-disease-tracker-web" `
  --collect-all "paillier_disease_tracker" `
  --hidden-import "paillier_disease_tracker.web.app" `
  --add-data "src\paillier_disease_tracker\web\static;paillier_disease_tracker\web\static" `
  src\paillier_disease_tracker\web\main.py
