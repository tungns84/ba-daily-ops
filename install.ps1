$ErrorActionPreference = "Stop"

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

if ($PSVersionTable.PSVersion -lt [Version]"5.1") {
    [Console]::Error.WriteLine("[FAIL] Checking prerequisites: Windows PowerShell 5.1 or newer is required.")
    [Console]::Error.WriteLine("    Next: Update Windows PowerShell, then rerun the installer.")
    exit 1
}

$git = Get-Command "git.exe" -ErrorAction SilentlyContinue
if ($null -eq $git) {
    [Console]::Error.WriteLine("[FAIL] Checking prerequisites: Git is required.")
    [Console]::Error.WriteLine("    Next: Install Git from https://git-scm.com/download/win, then rerun the installer after Git is available.")
    exit 1
}

$pythonCommand = $null
$pythonPrefix = @()
$py = Get-Command "py.exe" -ErrorAction SilentlyContinue
if ($null -ne $py) {
    & $py.Source -3 -c "import sys;raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = $py.Source
        $pythonPrefix = @("-3")
    }
}

if ($null -eq $pythonCommand) {
    foreach ($name in @("python3.exe", "python.exe")) {
        $candidate = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $candidate) {
            & $candidate.Source -c "import sys;raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonCommand = $candidate.Source
                break
            }
        }
    }
}

if ($null -eq $pythonCommand) {
    [Console]::Error.WriteLine("[FAIL] Checking prerequisites: Python 3.11 or newer is required.")
    [Console]::Error.WriteLine("    Next: Install Python from https://www.python.org/downloads/windows/, then rerun the installer after Python is available.")
    exit 1
}

$bootstrap = Join-Path $PSScriptRoot "installer\bootstrap.py"
$pythonArguments = @()
$pythonArguments += $pythonPrefix
$pythonArguments += @("-X", "utf8", $bootstrap)
$pythonArguments += $args

if ([Console]::IsInputRedirected) {
    $env:BA_TOOLS_NONINTERACTIVE = "1"
}

& $pythonCommand @pythonArguments
exit $LASTEXITCODE
