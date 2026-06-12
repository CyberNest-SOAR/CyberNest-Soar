@echo off
REM Run the full CyberNest stack using docker-compose.root.yml
SETLOCAL ENABLEDELAYEDEXPANSION
SET ROOT_DIR=%~dp0
REM Copy root .env to backend/.env if backend/.env missing
IF EXIST "%ROOT_DIR%.env" (
  IF NOT EXIST "%ROOT_DIR%backend\.env" (
    echo Copying root .env to backend/.env
    copy "%ROOT_DIR%.env" "%ROOT_DIR%backend\.env" >nul
  )
)
REM Check for referenced compose files in docker-compose.root.yml (PowerShell)
powershell -NoProfile -Command "& { $root = Split-Path -Parent '%~f0'; $content = Get-Content -Path (Join-Path $root 'docker-compose.root.yml') -Raw; $matches = [regex]::Matches($content, 'file:\s*(\S+)'); $files = $matches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique; $missing = @(); foreach ($f in $files) { if (-not (Test-Path (Join-Path $root $f))) { $missing += $f } }; if ($missing.Count -gt 0) { Write-Host 'Error: Missing compose include files:'; $missing | ForEach-Object { Write-Host ('  - ' + $_) }; Write-Host ''; Write-Host 'You can run only the backend API compose with:'; Write-Host '  docker compose -f backend/infra/docker-compose.yml up -d --build'; exit 1 } }"
IF ERRORLEVEL 1 (
  echo Warning: one or more referenced compose include files are missing.
  echo Falling back to the available backend-only compose.
  docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
  IF ERRORLEVEL 1 EXIT /B 1
  echo All backend services starting. To watch logs run:
  echo    docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" logs -f --tail=200
  ENDLOCAL
  EXIT /B 0
)

REM Start the stack
powershell -NoProfile -Command "if (-not (docker compose -f '%ROOT_DIR%docker-compose.root.yml' config 2>$null)) { exit 1 }"
IF ERRORLEVEL 1 (
  echo Warning: docker-compose.root.yml validation failed. Falling back to backend-only compose.
  docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
  IF ERRORLEVEL 1 EXIT /B 1
  echo All backend services starting. To watch logs run:
  echo    docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" logs -f --tail=200
  ENDLOCAL
  EXIT /B 0
)

docker compose -f "%ROOT_DIR%docker-compose.root.yml" up -d --build
echo All services starting. To watch logs run:
	docker compose -f "%ROOT_DIR%docker-compose.root.yml" logs -f --tail=200
ENDLOCAL
