#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting backend-only stack using backend/infra/docker-compose.yml"
docker compose -f "$ROOT_DIR/backend/infra/docker-compose.yml" up -d --build

echo "Backend-only services are starting. To watch logs:"
echo "  docker compose -f backend/infra/docker-compose.yml logs -f --tail=200"
