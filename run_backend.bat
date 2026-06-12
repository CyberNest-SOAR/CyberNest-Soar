@echo off
setlocal enabledelayedexpansion
set "ROOT_DIR=%~dp0"

echo Starting backend-only stack using backend\infra\docker-compose.yml
docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" up -d --build
IF ERRORLEVEL 1 EXIT /B 1

echo Backend-only services are starting. Streaming logs live...
echo ---------------------------------------------------------------------
:: This line drops you straight into the scrolling logs instantly:
docker compose -f "%ROOT_DIR%backend\infra\docker-compose.yml" logs soar_api -f --tail=200

ENDLOCAL