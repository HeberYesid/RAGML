$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeLock = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config\runtime.lock.json') | ConvertFrom-Json
if ($runtimeLock.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid runtime version' }
if (-not $runtimeLock.archive_url.StartsWith('https://github.com/ollama/ollama/releases/download/')) {
    throw 'The runtime download must use the official Ollama GitHub release.'
}
$downloadDirectory = Join-Path $projectRoot '.cache\downloads'
New-Item -ItemType Directory -Force -Path $downloadDirectory | Out-Null
$archivePath = Join-Path $downloadDirectory "ollama-v$($runtimeLock.version).zip"
if (-not (Test-Path -LiteralPath $archivePath)) {
    & curl.exe --fail --location --retry 2 --output $archivePath $runtimeLock.archive_url
    if ($LASTEXITCODE -ne 0) { throw 'Ollama download failed' }
}
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $runtimeLock.archive_sha256) {
    throw 'Ollama archive checksum mismatch. No executable will be launched.'
}
$runtimeDirectory = Join-Path $projectRoot ".cache\ollama\runtime-v$($runtimeLock.version)"
$runtimePath = Join-Path $runtimeDirectory 'ollama.exe'
if (-not (Test-Path -LiteralPath $runtimePath)) {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $runtimeDirectory
}
& (Join-Path $PSScriptRoot 'start-models.ps1') -Background
$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/version' -TimeoutSec 2 -NoProxy
        $ready = $true
        break
    } catch { Start-Sleep -Milliseconds 250 }
}
if (-not $ready) { throw 'Local model server did not become available; inspect the project logs.' }
$modelLock = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config\models.lock.json') | ConvertFrom-Json
foreach ($selectedModel in @($modelLock.generation, $modelLock.embedding)) {
    & $runtimePath pull $selectedModel.tag
    if ($LASTEXITCODE -ne 0) { throw "Model download failed: $($selectedModel.tag)" }
}
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $pythonPath -m ragml --project-dir $projectRoot doctor
if ($LASTEXITCODE -ne 0) { throw 'Model identities do not match the selected lockfile' }
