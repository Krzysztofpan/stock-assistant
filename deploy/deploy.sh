#!/bin/bash
set -euo pipefail
git pull origin main
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml build
docker compose -f docker-compose.prod.yaml run --rm backend uv run aerich upgrade
docker compose -f docker-compose.prod.yaml up -d
docker image prune -f
