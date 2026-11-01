$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$env:LLM_BASE_URL = 'http://127.0.0.1:11434'
if (-not $env:LLM_MODEL) { $env:LLM_MODEL = 'qwen2.5:3b-instruct' }
if (Test-Path '.venv312/Scripts/python.exe') { $taskPython = '.venv312/Scripts/python.exe' }
elseif (Test-Path '.venv/Scripts/python.exe') { $taskPython = '.venv/Scripts/python.exe' }
else { $taskPython = 'python' }
& $taskPython -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8080 --no-access-log
