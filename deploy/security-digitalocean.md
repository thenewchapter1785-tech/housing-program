# Security Guide for DigitalOcean Deployment

This guide covers security best practices for deploying the housing platform to DigitalOcean.

## Environment Variables & Secrets Management

### DigitalOcean App Platform

1. **Secure Secret Storage**:
   - Use DigitalOcean's built-in secret management, not plaintext env vars
   - Go to: Console → Apps → Your App → Settings → App-level Environment Variables
   - Prefix sensitive vars with underscore (e.g., `_WEB_JWT_SECRET`)

2. **Required Secrets**:
   ```
   WEB_JWT_SECRET: Generate with: openssl rand -base64 32
   MYSQL_PASSWORD: Strong random password (20+ chars, mixed case/numbers/symbols)
   ```

3. **Rotation Policy**:
   - Rotate `WEB_JWT_SECRET` monthly
   - Rotate database passwords every 90 days
   - Use DigitalOcean console to update without redeploying

### GitHub Actions Secrets

Add to your GitHub repository settings → Secrets:

```
DIGITALOCEAN_TOKEN: Personal Access Token from DO console
WEB_JWT_SECRET: Copy from DigitalOcean App Platform
MYSQL_PASSWORD: Database password
```

Generate tokens:
```bash
# DigitalOcean Personal Access Token
# Visit: https://cloud.digitalocean.com/account/api/tokens
# Create new token with read+write scope
```

## Network Security

### Firewall Rules

**App Platform** (automatic):
- Ingress: Only port 80/443 exposed
- Egress: All outbound allowed (for web scraping)
- Database: Only accessible to app services

**Droplet Deployment**:

```bash
# Create firewall in DigitalOcean
doctl compute firewall create --name housing-fw \
  --inbound-rules "protocol:tcp,ports:22,sources:addresses:YOUR_IP" \
  --inbound-rules "protocol:tcp,ports:80,sources:addresses:0.0.0.0/0" \
  --inbound-rules "protocol:tcp,ports:443,sources:addresses:0.0.0.0/0" \
  --outbound-rules "protocol:tcp,ports:all,destinations:addresses:0.0.0.0/0" \
  --outbound-rules "protocol:udp,ports:all,destinations:addresses:0.0.0.0/0"

# Assign to Droplet
doctl compute firewall assign <firewall-id> --droplet-ids <droplet-id>
```

**SSH Access** (Droplets only):
- Use SSH keys, never password authentication
- Restrict SSH to your IP address only
- Disable root login:
  ```bash
  sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  ```

### TLS/SSL Certificates

**App Platform** (automatic):
- Let's Encrypt certificates auto-renewed
- HTTP → HTTPS redirect enforced
- HSTS headers enabled

**Droplet** (manual setup):

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Verify
sudo certbot renew --dry-run
```

Nginx configuration:
```nginx
# Force HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}

# TLS security
server {
    listen 443 ssl http2;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

## Database Security

### MySQL Configuration

1. **Access Control**:
   ```bash
   mysql> CREATE USER 'app'@'localhost' IDENTIFIED BY 'strong-password';
   mysql> GRANT SELECT, INSERT, UPDATE ON housing_app.* TO 'app'@'localhost';
   mysql> REVOKE ALL ON *.* FROM 'app'@'localhost';
   ```

2. **Remove Default Accounts**:
   ```bash
   mysql> DROP USER 'root'@'127.0.0.1';
   mysql> DROP USER 'root'@'::1';
   mysql> DROP USER ''@'localhost';
   ```

3. **Backup Security**:
   ```bash
   # Encrypted backups
   mysqldump --all-databases | gzip | openssl enc -aes-256-cbc > backup.sql.gz.enc
   
   # Store in DigitalOcean Spaces (S3-compatible)
   aws s3 cp backup.sql.gz.enc s3://your-bucket/ \
     --sse AES256 --region nyc3
   ```

### DigitalOcean Managed Database

- Automatic daily backups (30-day retention)
- Point-in-time recovery available
- Automatic SSL connections enforced
- Private network isolation (app-only access)

Check backup status:
```bash
doctl databases backups list <cluster-id>
```

## Application Security

### JWT Token Handling

1. **Secure Token Storage** (browser):
   ```javascript
   // Store in httpOnly cookie (safer than localStorage)
   document.cookie = `access_token=${token}; HttpOnly; Secure; SameSite=Strict`;
   ```

2. **Token Rotation**:
   - Access tokens: 30 minutes TTL
   - Refresh tokens: 14 days TTL
   - Implement refresh token rotation (issue new refresh on each use)

3. **Token Revocation** (if needed):
   ```python
   # Add to database
   CREATE TABLE token_blacklist (
       token_jti VARCHAR(255) PRIMARY KEY,
       revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

### Rate Limiting

Add to your web server:

```python
# src/web/server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(credentials: LoginRequest):
    # Login endpoint
    pass

@app.post("/auth/register/searcher")
@limiter.limit("3/hour")
async def register(data: RegisterRequest):
    # Registration endpoint
    pass
```

### Input Validation

1. **SQL Injection Prevention**:
   - Always use parameterized queries (already implemented in storage.py)
   - Validate and sanitize all inputs

2. **CORS Security**:
   ```python
   # Whitelist allowed origins only
   CORSMiddleware(
       app,
       allow_origins=os.getenv("WEB_ALLOWED_ORIGINS", "").split(","),
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["Authorization", "Content-Type"],
   )
   ```

3. **Request Size Limits**:
   ```python
   # Prevent DoS attacks
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

## Monitoring & Alerting

### DigitalOcean Monitoring

1. **App Platform Monitoring**:
   - View logs: Console → Apps → Your App → Logs
   - Set alerts: Create Monitoring Policies in DigitalOcean dashboard
   - Alert on: High memory, high CPU, failed health checks

2. **Database Monitoring**:
   - View metrics: Databases → Your DB → Metrics
   - Alert on: Connection count, query latency, replication lag

### Application Logging

1. **Structured Logging** (already implemented):
   ```python
   from housing_scraper.observability import StructuredLogger
   
   logger = StructuredLogger("housing-web")
   logger.info("User login", user_id=123, ip_address="1.2.3.4")
   ```

2. **Centralized Log Aggregation** (optional):
   ```bash
   # Send logs to DigitalOcean Spaces (S3) or external service
   # Example: Papertrail, Splunk, ELK stack
   ```

3. **Log Retention**:
   - Keep logs for 30 days minimum
   - Archive to cold storage after 90 days
   - Delete after 2 years per privacy policy

## Compliance & Auditing

### GDPR Compliance (if applicable)

1. **Data Minimization**:
   - Only store necessary user data
   - Implement data deletion on user request (right to be forgotten)

2. **Data Processing Agreement**:
   - Review DigitalOcean's DPA at https://www.digitalocean.com/legal/data-processing-agreement/
   - Sign if handling EU user data

3. **Audit Trail**:
   - Log all admin actions (already implemented in audit_logs table)
   - Implement GDPR audit endpoint

### Security Audit Checklist

```bash
# Before each production release
- [ ] All secrets rotated in last 90 days
- [ ] TLS certificates valid and auto-renewal configured
- [ ] Database backups tested and restorable
- [ ] Firewall rules reviewed and minimal
- [ ] SSH access restricted to known IPs
- [ ] Security patches applied
- [ ] Logs being collected and monitored
- [ ] Health checks passing on all services
- [ ] No hardcoded credentials in code
- [ ] CORS origins whitelisted (not "*")
```

## Incident Response

### If Credentials Are Exposed

1. **Immediate Actions** (< 5 minutes):
   - Rotate all exposed secrets in DigitalOcean console
   - Check GitHub Actions logs for secret leaks

2. **Investigation** (< 30 minutes):
   - Review access logs for unauthorized access
   - Check database audit_logs table for suspicious activity
   - Review recent deployments and changes

3. **Notification** (< 1 hour):
   - Alert users if their data was accessed
   - Document incident timeline
   - Notify DigitalOcean support if their infrastructure was compromised

### If Database Is Breached

1. **Containment**:
   - Disable app access to database
   - Create read-only snapshot for forensics
   - Restore from clean backup

2. **Investigation**:
   - Check audit logs for access patterns
   - Identify what data was accessed
   - Determine exposure window

3. **Recovery**:
   - Restore from backup (point-in-time)
   - Reset all user passwords
   - Issue security advisory

## Resources

- DigitalOcean Security Best Practices: https://docs.digitalocean.com/products/app-platform/concepts/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- DigitalOcean Firewall Guide: https://docs.digitalocean.com/products/networking/firewalls/
- Mozilla SSL Configuration Generator: https://ssl-config.mozilla.org/

## Support

For security issues, email: security@your-domain.com

Do not open public issues for security vulnerabilities. Follow responsible disclosure practices.
