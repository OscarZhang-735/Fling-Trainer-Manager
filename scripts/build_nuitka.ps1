param(
    [string]$Python = "python",
    [string]$OutputDir = "build/nuitka",
    [switch]$DryRun
)

$arguments = @((Join-Path $PSScriptRoot "build_nuitka.py"), "--output-dir", $OutputDir)
if ($DryRun) { $arguments += "--dry-run" }
& $Python @arguments
exit $LASTEXITCODE
