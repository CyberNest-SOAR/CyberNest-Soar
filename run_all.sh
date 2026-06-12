#!/usr/bin/env bash
# Run the full CyberNest stack using docker-compose.root.yml
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
# Ensure backend/.env exists (copy from root .env if present)
if [ -f "$ROOT_DIR/.env" ] && [ ! -f "$ROOT_DIR/backend/.env" ]; then
  echo "Copying root .env to backend/.env"
  cp "$ROOT_DIR/.env" "$ROOT_DIR/backend/.env"
fi
# Verify included compose files referenced by docker-compose.root.yml exist
MISSING=()
while IFS= read -r line; do
  # look for lines like: file: path/to/child.yml
  if [[ $line =~ file:[[:space:]]*(.*) ]]; then
    child=${BASH_REMATCH[1]}
    # normalize path relative to root
    child_path="$ROOT_DIR/${child}"
    if [ ! -f "$child_path" ]; then
      MISSING+=("$child")
    fi
  fi
done < "$ROOT_DIR/docker-compose.root.yml"

if [ ${#MISSING[@]} -ne 0 ]; then
  echo "Warning: Missing docker-compose include files referenced in docker-compose.root.yml:"
  for f in "${MISSING[@]}"; do
    echo "  - $f"
  done
  echo
  echo "Falling back to the available backend-only compose."
  echo "Starting backend API stack with backend/infra/docker-compose.yml"
  docker compose -f "$ROOT_DIR/backend/infra/docker-compose.yml" up -d --build
  exit 0
fi

# Validate the root compose and fall back if the project is invalid
if ! docker compose -f "$ROOT_DIR/docker-compose.root.yml" config > /dev/null 2>&1; then
  echo "Warning: docker-compose.root.yml is invalid or incomplete. Falling back to backend-only compose."
  docker compose -f "$ROOT_DIR/backend/infra/docker-compose.yml" up -d --build
  echo "Backend-only services starting. To watch logs: docker compose -f backend/infra/docker-compose.yml logs -f --tail=200"
  exit 0
fi

# Build and start the entire stack (detached)
docker compose -f "$ROOT_DIR/docker-compose.root.yml" up -d --build
# Give a short status summary
echo "All services starting. To watch logs: docker compose -f docker-compose.root.yml logs -f --tail=200"
