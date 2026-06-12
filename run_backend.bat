@echo off
setlocal enabledelayedexpansion
set "ROOT_DIR=%~dp0"

echo Starting backend-only stack using backend\infra\docker-compose.yml
docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
IF ERRORLEVEL 1 EXIT /B 1

echo Backend-only services are starting. To watch logs:
echo    docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" logs -f --tail=200
ENDLOCAL
