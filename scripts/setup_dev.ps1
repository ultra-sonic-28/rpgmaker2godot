# Set up the Python development environment.
#
# Usage (from the repository root):
#   powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
#
# The script:
#   1. verifies it is run from the project directory
#      (C:\My Program Files\rpgmaker2godot) and aborts with an error
#      message otherwise;
#   2. activates the .venv virtual environment;
#   3. installs the project in editable mode with the development
#      extras (ruff + mypy).

$ErrorActionPreference = "Stop"

# The project directory the script must be run from.
$projectDirectory = "C:\My Program Files\rpgmaker2godot"

# ------------------------------------------------------------
# 1. Refuse to run from outside the project directory.
# ------------------------------------------------------------
$currentDirectory = (Get-Location).ProviderPath.TrimEnd("\")

if (-not $currentDirectory.Equals(
        $projectDirectory,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "Error: this script must be run from the project directory:" -ForegroundColor Red
    Write-Host "  $projectDirectory" -ForegroundColor Red
    Write-Host "Current directory: $currentDirectory" -ForegroundColor Red

    exit 1
}

# ------------------------------------------------------------
# 2. Activate the virtual environment.
# ------------------------------------------------------------
$activateScript = Join-Path $projectDirectory ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "Error: virtual environment not found:" -ForegroundColor Red
    Write-Host "  $activateScript" -ForegroundColor Red
    Write-Host "Create it first with: python -m venv .venv" -ForegroundColor Yellow

    exit 1
}

Write-Host "Activating the virtual environment (.venv)..."
. $activateScript

# ------------------------------------------------------------
# 3. Editable install with the development extras.
# ------------------------------------------------------------
Write-Host "Installing the project in editable mode with the dev extras (ruff + mypy)..."
python -m pip install -e ".[dev]"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: pip install failed with exit code $LASTEXITCODE." -ForegroundColor Red

    exit $LASTEXITCODE
}

Write-Host "Development environment ready." -ForegroundColor Green

exit 0
