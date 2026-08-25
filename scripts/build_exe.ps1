# Build the standalone Windows executable.
#
# Usage (from the repository root):
#   powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
#
# Prerequisite: the build extra must be installed first:
#   pip install -e ".[build]"

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

try {
    python -m PyInstaller --clean --noconfirm rpgmaker2godot.spec

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "Built: $(Join-Path $root 'dist\rpgmaker2godot.exe')"
}
finally {
    Pop-Location
}