#!/usr/bin/env bash
set -e

echo "🐳 Starting local development stack..."

# Pull images quietly
docker compose pull --quiet

# Build and start services
docker compose up --build -d

# Wait a moment for services to fully start
sleep 5

echo ""
echo "🚀 Local stack running:"
echo "  - Backend API:     http://localhost:8000/health"
echo "  - MinIO Console:   http://localhost:9001 (user: clip, pw: secret)"
echo "  - MinIO S3 API:    http://localhost:9000"
echo "  - Redis:           localhost:6379"
echo ""
echo "Use './scripts/dev-down.sh' to stop and clean up." 