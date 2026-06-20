# RepoDoc Pro — Windows Development Setup
# Run from repo root: powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1

param(
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up RepoDoc Pro..." -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$ElectronDir = Join-Path $RepoRoot "electron"

# ─── Python ──────────────────────────────────────────────────────────────────
Write-Host "`n📦 Setting up Python backend..." -ForegroundColor Yellow

$PythonVersion = python --version 2>&1
if (-not ($PythonVersion -match "3\.(1[0-9])")) {
    Write-Error "Python 3.10+ required. Found: $PythonVersion"
    exit 1
}
Write-Host "✅ $PythonVersion"

Push-Location $BackendDir

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "✅ Python packages installed"

# Create .env
if (-not (Test-Path ".env")) {
    @"
REPODOC_ENV=development
REPODOC_PORT=8765
REPODOC_LOG_LEVEL=DEBUG
REPODOC_TEMP_DIR=$env:TEMP\repodoc
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env"
}

if (-not $SkipTests) {
    Write-Host "`n🧪 Running backend tests..."
    pytest tests/ -x -q --no-header 2>&1 | Select-Object -Last 15
}

Pop-Location

# ─── Node.js ─────────────────────────────────────────────────────────────────
Write-Host "`n📦 Setting up Electron frontend..." -ForegroundColor Yellow

$NodeVersion = node --version 2>&1
Write-Host "✅ Node.js $NodeVersion"

Push-Location $ElectronDir
npm install --silent
Write-Host "✅ npm packages installed"
Pop-Location

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nTo start development:"
Write-Host "  Backend:  cd backend && .venv\Scripts\activate && python src\main.py --reload"
Write-Host "  Frontend: cd electron && npm run dev"
