#!/bin/bash
# DigitalOcean App Platform deployment script
# Prerequisites: doctl CLI installed and authenticated

set -e

APP_NAME="${1:-housing-platform}"
CONFIG_FILE="${2:-.do/app.yaml}"
REGION="${3:-nyc}"

echo "🚀 Deploying to DigitalOcean App Platform"
echo "App Name: $APP_NAME"
echo "Config: $CONFIG_FILE"
echo "Region: $REGION"

# Check doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl CLI not found. Install from https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check authentication
if ! doctl auth list 2>/dev/null | grep -q "default"; then
    echo "❌ Not authenticated with doctl. Run: doctl auth init"
    exit 1
fi

# Validate config file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Check if app exists
if doctl apps list --format Name --no-header | grep -q "^$APP_NAME$"; then
    echo "✅ App exists, updating..."
    APP_ID=$(doctl apps list --format ID,Name --no-header | grep "$APP_NAME" | awk '{print $1}')
    doctl apps update "$APP_ID" --spec "$CONFIG_FILE"
else
    echo "✅ Creating new app..."
    doctl apps create --spec "$CONFIG_FILE"
fi

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Visit https://cloud.digitalocean.com/apps"
echo "2. Configure environment variables (WEB_JWT_SECRET, WEB_ALLOWED_ORIGINS)"
echo "3. Monitor deployment progress in the console"
echo ""
echo "To check deployment status:"
echo "  doctl apps list"
echo ""
echo "To view logs:"
echo "  doctl apps logs <app-id>"
