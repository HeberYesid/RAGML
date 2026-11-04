param([switch]$Background)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeLock = Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'config\runtime.lock.json') | ConvertFrom-Json
if ($runtimeLock.version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid runtime version' }
$runtimePath = Join-Path $projectRoot ".cache\ollama\runtime-v$($runtimeLock.version)\ollama.exe"
if (-not (Test-Path -LiteralPath $runtimePath)) {
    throw 'Portable Ollama is missing. Follow docs/architecture/local-models.md first.'
}
if ((Get-FileHash -LiteralPath $runtimePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $runtimeLock.executable_sha256) {
    throw 'Portable Ollama executable does not match runtime.lock.json'
}
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = Join-Path $projectRoot '.cache\ollama\models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
$env:OLLAMA_KEEP_ALIVE = '2m'
$pidPath = Join-Path $projectRoot '.cache\ollama\server.pid'
if (Test-Path -LiteralPath $pidPath) {
    $savedProcessId = [int](Get-Content -LiteralPath $pidPath)
    $existingProcess = Get-Process -Id $savedProcessId -ErrorAction SilentlyContinue
    if ($existingProcess -and $existingProcess.Path -eq $runtimePath) {
        Write-Output "Project model server is already running: $savedProcessId"
        return
    }
}
$portProbe = [System.Net.Sockets.TcpClient]::new()
try {
    try { $portProbe.Connect('127.0.0.1', 11435) } catch [System.Net.Sockets.SocketException] { }
    if ($portProbe.Connected) { throw 'Port 11435 is occupied by another service; it will not be reused.' }
} finally { $portProbe.Dispose() }
New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
if ($Background) {
    $modelProcess = Start-Process -FilePath $runtimePath -ArgumentList 'serve' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot '.cache\ollama\server.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.cache\ollama\server.stderr.log')
    $modelProcess.Id | Set-Content -LiteralPath $pidPath
    Write-Output "Local model process: $($modelProcess.Id)"
} else {
    & $runtimePath serve
}
