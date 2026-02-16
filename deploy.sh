#!/bin/bash
# Deploy CoverageIQ to Cloudflare Pages
# Requires CLOUDFLARE_API_TOKEN environment variable

set -e

echo "Deploying CoverageIQ frontend to Cloudflare Pages..."

if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "❌ ERROR: CLOUDFLARE_API_TOKEN is not set"
    echo ""
    echo "To get your API token:"
    echo "1. Go to https://dash.cloudflare.com/profile/api-tokens"
    echo "2. Create a token with 'Cloudflare Pages:Edit' permission"
    echo "3. Run: export CLOUDFLARE_API_TOKEN=your_token_here"
    echo ""
    exit 1
fi

cd "$(dirname "$0")/frontend"

echo "📦 Building frontend..."
npm run build

echo "🚀 Deploying to Cloudflare Pages..."
npx wrangler pages deploy dist --project-name=coverageiq --branch=main

echo "✅ Deployment complete!"
