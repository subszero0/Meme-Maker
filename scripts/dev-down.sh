#!/usr/bin/env bash
set -e

echo "🛑 Stopping local development stack..."

# Stop and remove containers, networks, and volumes
docker compose down -v

echo "✅ Local stack stopped and volumes cleaned up." 