# One-time project setup (Windows PowerShell)
# Usage:  .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== Clinical Meeting Intelligence setup ==" -ForegroundColor Cyan

# .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[ok] Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "[skip] .env already exists" -ForegroundColor Yellow
}

# SSL for Hugging Face model downloads (embeddings + whisper)
try {
    $cert = python -c "import certifi; print(certifi.where())" 2>$null
    if ($cert) {
        $env:SSL_CERT_FILE = $cert
        $env:REQUESTS_CA_BUNDLE = $cert
        Write-Host "[ok] SSL certs: $cert" -ForegroundColor Green
        Write-Host "     Add these to .env if downloads fail on Windows." -ForegroundColor DarkGray
    }
} catch {
    Write-Host "[warn] Could not resolve certifi path" -ForegroundColor Yellow
}

# Backend
Write-Host "`nInstalling backend (Python 3.12+)..." -ForegroundColor Cyan
Set-Location "$Root\backend"
python -m pip install -e ".[dev]" -q
Write-Host "[ok] Backend dependencies installed" -ForegroundColor Green

# Frontend
Write-Host "`nInstalling frontend..." -ForegroundColor Cyan
Set-Location "$Root\frontend"
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm install --silent
    Write-Host "[ok] Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[warn] npm not found — install Node.js LTS, then run: cd frontend && npm install" -ForegroundColor Yellow
}

Set-Location $Root

# Qdrant
Write-Host "`nStarting Qdrant (Docker)..." -ForegroundColor Cyan
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $existing = docker ps -a --filter "name=cmi-qdrant" --format "{{.Names}}" 2>$null
    if ($existing -eq "cmi-qdrant") {
        docker start cmi-qdrant 2>$null | Out-Null
    } else {
        docker run -d --name cmi-qdrant -p 6333:6333 qdrant/qdrant:v1.12.5 | Out-Null
    }
    Write-Host "[ok] Qdrant on http://localhost:6333" -ForegroundColor Green
} else {
    Write-Host "[warn] Docker not found — start Qdrant manually or use docker compose" -ForegroundColor Yellow
}

# Ollama (optional local LLM)
Write-Host "`nChecking Ollama (optional local LLM)..." -ForegroundColor Cyan
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Pulling default model llama3.1:8b (may take a few minutes)..." -ForegroundColor DarkGray
    ollama pull llama3.1:8b
    Write-Host "[ok] Ollama model ready" -ForegroundColor Green
} else {
    Write-Host "[skip] Ollama not installed — use OpenAI/Anthropic in .env instead" -ForegroundColor Yellow
    Write-Host "       Or install from https://ollama.com and run: ollama pull llama3.1:8b" -ForegroundColor DarkGray
}

Set-Location $Root
Write-Host "`n== Setup complete ==" -ForegroundColor Cyan
Write-Host @"

Next steps:
  1. Edit .env if you want OpenAI/Anthropic instead of Ollama
  2. Start the stack:     .\scripts\start-local.ps1
     Or with Docker:      docker compose up --build
  3. Seed sample data:    python scripts/seed_samples.py
  4. Open UI:             http://localhost:3000

Models download on first use:
  - Embeddings:  EMBEDDING_MODEL (Hugging Face, ~130 MB default)
  - Whisper:     first audio upload (WHISPER_MODEL_SIZE, ~500 MB for small)
  - LLM:         ollama pull ... OR cloud API keys in .env

"@
