$ErrorActionPreference = "Stop"

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

function Write-LauncherNotReady {
    [Console]::Error.WriteLine('{"schema_version":1,"ok":false,"command":"launcher","error":{"code":"LAUNCHER_NOT_READY","message":"The project-local BA Tools runtime is not ready.","details":[],"remediation":["Rerun the repository installer, then retry this command."]}}')
    exit 2
}

try {
    $repoRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
    $runtimeRoot = Join-Path $repoRoot ".ba-tools-runtime"
    $pointer = Join-Path $runtimeRoot "current-env.txt"
    if (-not [System.IO.File]::Exists($pointer)) {
        Write-LauncherNotReady
    }

    $generation = [System.IO.File]::ReadAllText($pointer, [System.Text.Encoding]::UTF8).Trim()
    if ($generation -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' -or $generation -eq "." -or $generation -eq "..") {
        Write-LauncherNotReady
    }

    $envsRoot = [System.IO.Path]::GetFullPath((Join-Path $runtimeRoot "envs"))
    $generationRoot = [System.IO.Path]::GetFullPath((Join-Path $envsRoot $generation))
    $requiredPrefix = $envsRoot.TrimEnd('\') + '\'
    if (-not $generationRoot.StartsWith($requiredPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-LauncherNotReady
    }

    $python = Join-Path $generationRoot "Scripts\python.exe"
    if (-not [System.IO.File]::Exists($python)) {
        Write-LauncherNotReady
    }

    & $python -X utf8 -m ba_tools --repo-root $repoRoot @args
    exit $LASTEXITCODE
}
catch {
    Write-LauncherNotReady
}
