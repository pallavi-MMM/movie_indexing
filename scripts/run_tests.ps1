# Helper to run the test suite in PowerShell
# Usage: Open PowerShell in repo root and run `.









Write-Host "All tests passed"}    exit $LASTEXITCODE    Write-Error "Tests failed with exit code $LASTEXITCODE"if ($LASTEXITCODE -ne 0) {python -m pytest -qWrite-Host "Running pytest..."un_tests.ps1`