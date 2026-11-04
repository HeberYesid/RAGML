$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $projectRoot '.cache\ollama\server.pid'
if (-not (Test-Path -LiteralPath $pidPath)) { Write-Output 'No project model process recorded.'; return }
$savedProcessId = [int](Get-Content -LiteralPath $pidPath)
$runtimeLock = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config\runtime.lock.json') | ConvertFrom-Json
if ($runtimeLock.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid runtime version' }
$runtimePath = Join-Path $projectRoot ".cache\ollama\runtime-v$($runtimeLock.version)\ollama.exe"
$modelProcess = Get-Process -Id $savedProcessId -ErrorAction SilentlyContinue
if ($modelProcess) {
    if ($modelProcess.Path -ne $runtimePath) { throw 'Recorded PID belongs to another executable; it will not be stopped.' }
    $env:OLLAMA_HOST = '127.0.0.1:11435'
    $modelLock = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config\models.lock.json') | ConvertFrom-Json
    foreach ($selectedModel in @($modelLock.generation, $modelLock.embedding)) {
        & $runtimePath stop $selectedModel.tag
    }
    Stop-Process -Id $savedProcessId
}
Remove-Item -LiteralPath $pidPath
Write-Output 'Stopped the recorded project model server.'
