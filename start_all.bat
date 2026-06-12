@echo off
REM Start the full CyberNest stack on Windows (falls back to backend-only compose)
SETLOCAL ENABLEDELAYEDEXPANSION
SET ROOT_DIR=%~dp0

IF NOT EXIST "%ROOT_DIR%docker-compose.root.yml" (
  echo docker-compose.root.yml not found, starting backend-only compose...
  docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
  GOTO :EOF
)

echo Attempting to start root docker-compose
docker compose -f "%ROOT_DIR%docker-compose.root.yml" up -d --build || (
  echo Root compose failed or missing includes; falling back to backend-only compose...
  docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
)

echo Services are starting. Use 'docker compose ps' to view status.
ENDLOCAL
