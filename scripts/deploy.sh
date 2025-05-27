#!/bin/bash

set -euo pipefail

# Graceful error handling
trap 'echo "⚠️ Deploy aborted"; exit 1' ERR

# Check required environment variables
if [[ -z "${API:-}" ]]; then
    echo "❌ Error: API environment variable is required"
    exit 1
fi

if [[ -z "${CF_DIST_ID:-}" ]]; then
    echo "❌ Error: CF_DIST_ID environment variable is required"
    exit 1
fi

# Functions for AWS operations
sync_site() {
    echo "📤 Syncing site to S3..."
    aws s3 sync frontend/out/ s3://clip-downloader-web --delete \
        --profile "${AWS_PROFILE:-default}"
    echo "✅ Site sync complete"
}

invalidate_cache() {
    echo "🔄 Invalidating CloudFront cache..."
    local invalidation_id
    invalidation_id=$(aws cloudfront create-invalidation \
        --distribution-id "$CF_DIST_ID" \
        --paths "/*" \
        --profile "${AWS_PROFILE:-default}" \
        --query 'Invalidation.Id' \
        --output text)
    echo "✅ CloudFront invalidation created: $invalidation_id"
}

# Main deployment process
echo "🚀 Starting deployment at $(date '+%F %T')"

echo "🏗️ Building frontend..."
cd frontend
NEXT_PUBLIC_API_URL="$API" npm run build
echo "✅ Frontend build complete"

cd ..

sync_site
invalidate_cache

echo "🎉 Deployment completed at $(date '+%F %T')" 