# PowerShell script to automate build and run for Google Places Enricher 2.0

Write-Host "=== Building executable with PyInstaller ==="
$distPath = Join-Path $PSScriptRoot "dist"
if (Test-Path $distPath) {
    Write-Host "Removing existing build output directory: $distPath"
    Remove-Item -Recurse -Force $distPath
}
cd $PSScriptRoot
.\pyinstaller.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed. Exiting."
    exit 1
}

$exePath = Join-Path $PSScriptRoot "dist\Google Places Enricher 2.0\Google Places Enricher 2.0.exe"

if (-Not (Test-Path $exePath)) {
    Write-Host "Executable not found: $exePath"
    exit 1
}

Write-Host "=== Running the executable ==="
& $exePath

if ($LASTEXITCODE -ne 0) {
    Write-Host "Executable exited with errors. Check output above for details."
    exit $LASTEXITCODE
}

Write-Host "Workflow complete."
