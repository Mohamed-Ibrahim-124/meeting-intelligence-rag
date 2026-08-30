# Start API + frontend locally (Qdrant must be running — see setup.ps1)
# Usage:  .\scripts\start-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "Missing .env — run .\scripts\setup.ps1 first" -ForegroundColor Red
    exit 1
}

# Load SSL for Hugging Face
try {
    $cert = python -c "import certifi; print(certifi.where())" 2>$null
    if ($cert) {
        $env:SSL_CERT_FILE = $cert
        $env:REQUESTS_CA_BUNDLE = $cert
        $env:CURL_CA_BUNDLE = $cert
    }
} catch { }

$env:QDRANT_URL = "http://localhost:6333"
$env:PYTHONPATH = "src"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

# Read key vars from .env for display
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)$' -and $_.Trim() -notmatch '^\#') {
        $name = $matches[1]
        $val = $matches[2].Trim('"').Trim("'")
        if ($name -in @("LLM_PROVIDER","OLLAMA_MODEL","OPENAI_MODEL","EMBEDDING_MODEL","WHISPER_MODEL_SIZE")) {
            Set-Item -Path "env:$name" -Value $val
        }
    }
}

Write-Host "Starting backend on http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  LLM_PROVIDER=$env:LLM_PROVIDER  EMBEDDING_MODEL=$env:EMBEDDING_MODEL" -ForegroundColor DarkGray
Write-Host "  WHISPER_MODEL_SIZE=$env:WHISPER_MODEL_SIZE" -ForegroundColor DarkGray
Write-Host "Starting frontend on http://localhost:3000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C in each terminal to stop.`n" -ForegroundColor DarkGray

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root\backend'; `$env:QDRANT_URL='http://localhost:6333'; `$env:PYTHONPATH='src'; `$env:SSL_CERT_FILE='$env:SSL_CERT_FILE'; `$env:REQUESTS_CA_BUNDLE='$env:REQUESTS_CA_BUNDLE'; uvicorn clinical_meeting.api.app:app --host 127.0.0.1 --port 8000"
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root\frontend'; `$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8000'; npm run dev"
)

Write-Host "[ok] Opened backend and frontend in new windows." -ForegroundColor Green
