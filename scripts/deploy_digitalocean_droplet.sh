#!/bin/bash
# DigitalOcean Droplet deployment script
# Creates a new Droplet and sets up the housing platform

set -e

DROPLET_NAME="${1:-housing-web}"
REGION="${2:-nyc3}"
SIZE="${3:-s-2vcpu-4gb}"
SSH_KEY="${4:-}"
DOMAIN="${5:-}"

echo "🚀 Creating DigitalOcean Droplet"
echo "Name: $DROPLET_NAME"
echo "Region: $REGION"
echo "Size: $SIZE"

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

# Get SSH key if not provided
if [ -z "$SSH_KEY" ]; then
    echo "Available SSH keys:"
    doctl compute ssh-key list --format Name,Fingerprint --no-header
    read -p "Enter SSH key fingerprint: " SSH_KEY
fi

# Create Droplet
echo "✅ Creating Droplet..."
DROPLET_ID=$(doctl compute droplet create "$DROPLET_NAME" \
    --region "$REGION" \
    --image ubuntu-24-04-x64 \
    --size "$SIZE" \
    --enable-ipv6 \
    --ssh-keys "$SSH_KEY" \
    --wait \
    --format ID \
    --no-header)

echo "✅ Droplet created: $DROPLET_ID"

# Get Droplet IP
DROPLET_IP=$(doctl compute droplet get "$DROPLET_ID" --format PublicIPv4 --no-header)
echo "IP: $DROPLET_IP"

# Wait for Droplet to be ready
echo "⏳ Waiting for Droplet to be ready..."
sleep 30

# Setup script
SETUP_SCRIPT='#!/bin/bash
set -e

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.12 python3-pip git nginx mysql-server docker.io docker-compose-v2 curl

# Add appuser
useradd -m -s /bin/bash appuser || true

# Configure Docker
usermod -aG docker appuser

# Clone repository
cd /home/appuser
sudo -u appuser git clone https://github.com/thenewchapter1785-tech/housing-program.git || true

# Create MySQL database
mysql -u root << MYSQL_EOF
CREATE DATABASE IF NOT EXISTS housing_app;
CREATE USER IF NOT EXISTS '\''app'\''@'\''localhost'\'' IDENTIFIED BY '\''change-me'\'';
GRANT ALL PRIVILEGES ON housing_app.* TO '\''app'\''@'\''localhost'\'';
FLUSH PRIVILEGES;
MYSQL_EOF

echo "✅ Setup complete! SSH into the Droplet and configure .env"
echo "   ssh appuser@'"$DROPLET_IP"'"
'

# Send setup script
echo "📝 Running setup script..."
ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" "$SETUP_SCRIPT"

echo ""
echo "✅ Droplet ready!"
echo ""
echo "Next steps:"
echo "1. SSH into Droplet:"
echo "   ssh appuser@$DROPLET_IP"
echo ""
echo "2. Configure environment:"
echo "   cd housing-program"
echo "   cp .env.example .env"
echo "   nano .env"
echo "   # Update MYSQL_PASSWORD, WEB_JWT_SECRET, WEB_ALLOWED_ORIGINS"
echo ""
echo "3. Deploy with Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "4. Setup Nginx (see deploy/digitalocean.md for full config)"
echo ""
if [ -n "$DOMAIN" ]; then
    echo "5. Point your domain to: $DROPLET_IP"
fi
echo ""
echo "For full instructions, see deploy/digitalocean.md"
