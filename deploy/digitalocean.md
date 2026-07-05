# DigitalOcean Deployment

This guide covers deploying the housing platform to DigitalOcean using App Platform or traditional Droplets.

## Option 1: DigitalOcean App Platform (Recommended)

**Easiest:** One-click deployment with auto-scaling, managed databases, and CI/CD integration.

### Prerequisites

1. DigitalOcean account at https://www.digitalocean.com
2. GitHub account with repository access
3. `doctl` CLI installed: https://docs.digitalocean.com/reference/doctl/how-to/install/

### Quick Deploy (One-Click)

1. Fork the repository to your GitHub account
2. Visit DigitalOcean Console → Apps
3. Click "Create App"
4. Select "GitHub" and authorize
5. Select your forked repository
6. Choose `.do/app.yaml` for MySQL or `.do/app-postgres.yaml` for PostgreSQL
7. Configure environment variables:
   - `WEB_JWT_SECRET`: Generate a strong random string (e.g., `openssl rand -base64 32`)
   - `WEB_ALLOWED_ORIGINS`: Your custom domain (e.g., `https://housing.example.com`)
8. Click "Deploy"

### Deploy via CLI

```bash
# Install doctl
# On macOS: brew install doctl
# On Windows: choco install doctl
# On Linux: https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate
doctl auth init

# Deploy with MySQL
doctl apps create --spec .do/app.yaml

# OR deploy with PostgreSQL
doctl apps create --spec .do/app-postgres.yaml
```

### Environment Variables

Set these in the DigitalOcean console under **Settings → App-level Environment Variables**:

```
WEB_JWT_SECRET=<generate-secure-random-string>
WEB_ALLOWED_ORIGINS=https://your-domain.com
```

Set these per service in **Settings → Components → Service Environment Variables**:

**Web Service:**
```
SEARCH_CITY=seattle
SEARCH_QUERY=studio apartment
AUTO_REFRESH_IN_WEB=false
```

**Worker Service:**
```
AUTO_REFRESH_ENABLED=true
AUTO_REFRESH_INTERVAL_SECONDS=900
AUTO_REFRESH_QUERY=apartment
AUTO_REFRESH_PROVIDERS=craigslist,rentals,padmapper,rightmove
```

### Custom Domain

1. In DigitalOcean Console, go to **Apps → Your App → Settings → Domain**
2. Add your custom domain (e.g., `housing.example.com`)
3. DigitalOcean provides an auto-renewing SSL certificate via Let's Encrypt

### Scaling

- **Web Service:** Default 2 instances, adjust under **Components → web → Instance Count**
- **Worker Service:** 1 dedicated instance (no scaling needed)
- **Database:** Managed MySQL with automated backups and replication

### Monitoring

- Logs: **Apps → Your App → Logs**
- Metrics: **Apps → Your App → Metrics** (CPU, memory, request rate)
- Database: **Databases → Your Database → Metrics**

### Backup & Recovery

- Automated daily backups (retained 30 days)
- Manual snapshots in DigitalOcean Console
- Point-in-time recovery via DigitalOcean Dashboard

---

## Option 2: DigitalOcean Droplet (Traditional VPS)

**More control** but requires manual setup. Recommended for advanced users.

### Prerequisites

1. DigitalOcean account
2. SSH key pair configured
3. Domain name with DNS pointing to Droplet IP

### Create Droplet

```bash
doctl compute droplet create housing-web \
  --region nyc3 \
  --image ubuntu-24-04-x64 \
  --size s-2vcpu-4gb \
  --enable-ipv6 \
  --ssh-keys <your-ssh-key-fingerprint>
```

### SSH Into Droplet

```bash
ssh root@<your-droplet-ip>
```

### Setup Environment

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.12 python3-pip git nginx mysql-server docker.io docker-compose

# Add user for app
useradd -m -s /bin/bash appuser

# Configure Docker without sudo
usermod -aG docker appuser

# Clone repository
su - appuser
git clone https://github.com/thenewchapter1785-tech/housing-program.git
cd housing-program
```

### Setup MySQL

```bash
# Create database
mysql -u root -p << EOF
CREATE DATABASE housing_app;
CREATE USER 'app'@'localhost' IDENTIFIED BY 'secure-password';
GRANT ALL PRIVILEGES ON housing_app.* TO 'app'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Configure Environment

```bash
cp .env.example .env
nano .env
```

Update:
```
MYSQL_HOST=localhost
MYSQL_USER=app
MYSQL_PASSWORD=secure-password
MYSQL_DATABASE=housing_app
WEB_JWT_SECRET=<generate-random-string>
WEB_ALLOWED_ORIGINS=https://your-domain.com
AUTO_REFRESH_ENABLED=true
```

### Deploy with Docker Compose

```bash
docker-compose up -d
```

### Setup Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/housing
```

```nginx
server {
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/housing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Setup SSL with Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl enable certbot.timer
```

### Systemd Service

Create `/etc/systemd/system/housing-web.service`:

```ini
[Unit]
Description=Housing Web Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/home/appuser/housing-program
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
RemainAfterExit=yes
User=appuser

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable housing-web.service
sudo systemctl start housing-web.service
```

### Monitor Logs

```bash
docker-compose logs -f web
docker-compose logs -f worker
```

---

## Option 3: DigitalOcean Kubernetes (Advanced)

**Auto-scaling, load balancing, and high availability.**

### Create Cluster

```bash
doctl kubernetes cluster create housing-k8s \
  --region nyc3 \
  --node-pool name=web-pool,size=s-2vcpu-4gb,count=2 \
  --version latest

# Get kubeconfig
doctl kubernetes cluster kubeconfig save housing-k8s
```

### Deploy with Helm

Create `deploy/housing-helm/Chart.yaml` and deploy:

```bash
helm install housing ./deploy/housing-helm \
  --set mysql.password=secure \
  --set jwt.secret=<random-secret>
```

---

## Monitoring & Maintenance

### Health Checks

- Web service health: `curl https://your-domain.com/healthz`
- Worker logs: Check DigitalOcean App Logs or Droplet logs

### Database Backups

**App Platform:**
- Automatic daily backups in DigitalOcean console
- Manual backup via Dashboard → Databases → Your DB → Backups

**Droplet:**
```bash
# Manual backup
mysqldump -u app -p housing_app > backup.sql
# Restore
mysql -u app -p housing_app < backup.sql
```

### Auto-Updates

**App Platform:**
- Rebuilds and redeploys on every GitHub push to `master`
- No manual action needed

**Droplet:**
```bash
# Set up auto-pull and redeploy
cd /home/appuser/housing-program
0 2 * * * git pull && docker-compose up -d
```

### Scaling Up

**App Platform:**
- Web: Increase instance count in console (horizontal) or instance size (vertical)
- Auto-scaling rules via App Platform settings

**Droplet:**
- Create new Droplet and add to load balancer
- Use DigitalOcean Droplet manager for resizing

---

## Troubleshooting

### App won't start

```bash
# Check logs
doctl apps logs <app-id>

# Or on Droplet:
docker-compose logs web
```

### Database connection errors

```bash
# Test connection
mysql -h <mysql-host> -u app -p housing_app -e "SELECT 1;"

# Check env vars in console
```

### Disk space full

**Droplet:**
```bash
df -h
# Resize Droplet in DigitalOcean console
```

---

## Cost Estimation

### App Platform
- **Web Services:** ~$12/month (basic-s, 2 instances)
- **Worker:** ~$6/month (basic-xs, 1 instance)
- **MySQL 8GB:** ~$30/month
- **Total:** ~$48/month

### Droplet
- **Single 2vCPU/4GB:** ~$24/month
- **MySQL:** Included
- **Backups:** ~$5/month
- **Total:** ~$29/month

### Kubernetes (Advanced)
- **Cluster management:** Free
- **Nodes:** ~$12/month each (2 minimum)
- **Load Balancer:** ~$10/month
- **MySQL:** ~$30/month
- **Total:** ~$64/month

---

## Next Steps

1. Generate secure JWT secret: `openssl rand -base64 32`
2. Choose deployment option (App Platform recommended for simplicity)
3. Deploy and test health endpoint
4. Configure custom domain with SSL
5. Monitor logs and metrics
6. Set up backups and disaster recovery

For support, see the main README.md or GitHub Issues.
