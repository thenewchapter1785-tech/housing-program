# Quick Reference: DigitalOcean Deployment

## Pre-Deployment Checklist

- [ ] DigitalOcean account created
- [ ] GitHub repository forked to your account
- [ ] JWT secret generated: `openssl rand -base64 32`
- [ ] Custom domain configured (or using *.ondigitalocean.app)

## Option 1: One-Click App Platform (Easiest)

```bash
# 1. Create app in DigitalOcean console
# https://cloud.digitalocean.com/apps

# 2. Connect GitHub repo
# 3. Select .do/app.yaml config file
# 4. Set environment variables:
#    - WEB_JWT_SECRET: your-random-secret
#    - WEB_ALLOWED_ORIGINS: https://your-domain.com

# 5. Click Deploy
```

**Cost**: ~$48/month (2 web instances + MySQL)

## Option 2: Droplet with Docker Compose

```bash
# 1. Create account & authenticate
doctl auth init

# 2. Deploy Droplet
./scripts/deploy_digitalocean_droplet.sh housing-web nyc3 s-2vcpu-4gb

# 3. SSH into Droplet
ssh appuser@<droplet-ip>

# 4. Configure environment
cd housing-program
cp .env.example .env
nano .env  # Update credentials

# 5. Deploy
docker-compose -f docker-compose.digitalocean.yml up -d

# 6. Setup Nginx & SSL
# See deploy/digitalocean.md for detailed instructions
```

**Cost**: ~$29/month (single Droplet)

## Post-Deployment

### Health Check
```bash
# App Platform
curl https://your-domain.com/healthz

# Droplet
curl http://localhost/healthz
```

### View Logs

**App Platform**:
```bash
doctl apps logs <app-id>
```

**Droplet**:
```bash
ssh appuser@<ip>
docker-compose logs -f web
```

### Monitor Database

**App Platform**:
- Console → Databases → Your DB → Metrics

**Droplet**:
```bash
mysql -h localhost -u app -p housing_app -e "SHOW STATUS;"
```

### Update Configuration

**App Platform**:
1. Console → Apps → Your App → Settings
2. Update environment variables
3. Trigger redeploy

**Droplet**:
1. SSH into server
2. Edit `.env` file
3. `docker-compose down && docker-compose -f docker-compose.digitalocean.yml up -d`

## GitHub Auto-Deploy

```bash
# 1. Get DigitalOcean token from console
# 2. Add to GitHub repo secrets:
#    - DIGITALOCEAN_TOKEN

# 3. Every push to master auto-deploys via .github/workflows/deploy-digitalocean.yml
```

## Scaling

### Horizontal (Add More Instances)

**App Platform**:
- Console → Components → web → Instance Count

**Droplet**:
- Create new Droplet
- Add to load balancer
- DigitalOcean Load Balancer: $10-15/month

### Vertical (Upgrade Server)

**App Platform**:
- Console → Components → web → Instance Size

**Droplet**:
```bash
# Resize Droplet
doctl compute droplet-action resize <droplet-id> --size s-4vcpu-8gb --wait
```

## Backup & Recovery

**App Platform**:
- Automatic daily MySQL backups
- Console → Databases → Backups
- Point-in-time recovery: 30 days

**Droplet**:
```bash
# Manual backup
mysqldump -u app -p housing_app > backup.sql

# Restore
mysql -u app -p housing_app < backup.sql
```

## Troubleshooting

### App won't start
```bash
doctl apps logs <app-id> --follow
# Check for: database connection, missing env vars, syntax errors
```

### Database connection timeout
```bash
# Check database is accessible
mysql -h <db-host> -u app -p -e "SELECT 1;"

# Check environment variables in console
doctl apps describe <app-id>
```

### High CPU/Memory
```bash
# Check what's consuming resources
docker stats  # On Droplet

# Scale up
# App Platform: increase instance size
# Droplet: resize or add load balancer
```

## Security

1. **Generate secure JWT secret**:
   ```bash
   openssl rand -base64 32
   ```

2. **Use HTTPS only**:
   - App Platform: automatic
   - Droplet: run certbot for Let's Encrypt

3. **Restrict database access**:
   ```bash
   # Only app server can connect to database
   ```

4. **Rotate secrets every 90 days**:
   - Update in DigitalOcean console
   - No redeploy needed

## Cost Estimation

| Service | App Platform | Droplet |
|---------|-------------|---------|
| Web Server | $12 | Included |
| Worker | $6 | Included |
| MySQL (8GB) | $30 | Included |
| **Monthly Total** | **~$48** | **~$29** |

## Documentation

- Full deployment guide: [deploy/digitalocean.md](../deploy/digitalocean.md)
- Security best practices: [deploy/security-digitalocean.md](../deploy/security-digitalocean.md)
- App Platform docs: https://docs.digitalocean.com/products/app-platform/
- DigitalOcean support: https://support.digitalocean.com/

## Next Steps

1. Choose deployment option (App Platform or Droplet)
2. Follow Option 1 or 2 above
3. Test health endpoint
4. Configure custom domain
5. Set up monitoring and backups
6. Deploy code changes via GitHub push

**Questions?** See deploy/digitalocean.md or open a GitHub issue.
