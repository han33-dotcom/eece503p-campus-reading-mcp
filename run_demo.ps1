param(
    [switch]$Offline,
    [switch]$Chat,
    [switch]$Test
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create a Python virtual environment.' }
    & $pythonExe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
if ($Test) {
    & $pythonExe -m pytest -q
} elseif ($Offline) {
    & $pythonExe agent.py --offline
} else {
    if (-not $env:OPENAI_API_KEY) {
        $env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User')
    }
    if (-not $env:OPENAI_API_KEY) { throw 'Configure OPENAI_API_KEY or use -Offline.' }
    if ($Chat) { & $pythonExe agent.py --chat }
    else { & $pythonExe agent.py }
}
if ($LASTEXITCODE -ne 0) { throw "Run failed with exit code $LASTEXITCODE." }
