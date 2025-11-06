# ========================================
# PRODUCTION DEPLOYMENT GUIDE
# Azure D8s v3 VM Setup
# ========================================

## OVERVIEW
This guide walks through deploying the NLP API to Azure VM with production-ready configuration.

---

## PREREQUISITES

- [x] Azure VM: Standard D8s v3 (8 vCPU, 32GB RAM, 128GB SSD)
- [x] Ubuntu 20.04 LTS or later
- [x] Docker & Docker Compose installed
- [x] Domain name configured (DNS pointing to VM IP)
- [x] SSH access to VM
- [x] Upstash Redis account created

---

## STEP 1: PREPARE ENVIRONMENT FILE

### 1.1 Copy Production Template
```bash
cp .env.production .env
```

### 1.2 Generate Strong API Keys
```bash
# Generate API Key (32+ characters)
openssl rand -base64 48

# Generate JWT Secret
openssl rand -base64 48
```

### 1.3 Update .env File
Edit `.env` and replace:

```env
# CRITICAL SETTINGS
WORKERS=2

# SECURITY - Replace with generated keys
API_KEY=<paste_generated_api_key_here>
JWT_SECRET_KEY=<paste_generated_jwt_secret_here>

# CORS - Replace with your actual domain
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# UPSTASH REDIS - Get from https://console.upstash.com
UPSTASH_REDIS_REST_URL=https://your-instance.upstash.io
UPSTASH_REDIS_REST_TOKEN=<your_upstash_token>
```

---

## STEP 2: CONFIGURE UPSTASH REDIS

### 2.1 Create Upstash Account
1. Go to https://console.upstash.com/
2. Sign up / Log in
3. Click "Create Database"

### 2.2 Configure Database
- **Name**: nlp-api-cache
- **Region**: Choose closest to your Azure region
- **Type**: Regional (or Global for multi-region)

### 2.3 Get Credentials
1. Click on your database
2. Scroll to "REST API" section
3. Copy:
   - **UPSTASH_REDIS_REST_URL**: The REST URL
   - **UPSTASH_REDIS_REST_TOKEN**: The REST Token

### 2.4 Test Connection
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "YOUR_REST_URL/ping"

# Should return: {"result":"PONG"}
```

---

## STEP 3: UPDATE NGINX CONFIGURATION

### 3.1 Edit nginx.conf
Replace placeholders:
```nginx
server_name yourdomain.com www.yourdomain.com api.yourdomain.com;
```

### 3.2 SSL Certificate Paths
Update certificate paths based on your setup:

**Option A: Let's Encrypt**
```nginx
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

**Option B: Custom Certificates**
```nginx
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

---

## STEP 4: SETUP SSL CERTIFICATES

### Option A: Let's Encrypt (Recommended - Free)

```bash
# Make script executable
chmod +x setup-ssl.sh

# Edit script to add your domain and email
nano setup-ssl.sh
# Update: DOMAIN="yourdomain.com"
# Update: EMAIL="admin@yourdomain.com"

# Run setup script
sudo ./setup-ssl.sh
```

### Option B: Manual Let's Encrypt Setup

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Stop services temporarily
docker-compose down

# Obtain certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Certificates will be in: /etc/letsencrypt/live/yourdomain.com/
```

### Option C: Upload Custom Certificates

```bash
# Create SSL directory
mkdir -p ssl

# Upload your certificates
# cert.pem - Your SSL certificate
# key.pem - Your private key

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem
```

---

## STEP 5: SETUP AZURE MONITORING

### 5.1 Enable Application Insights

```bash
# Install Azure CLI (if not installed)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create Application Insights
az monitor app-insights component create \
  --app nlp-api-insights \
  --location eastus \
  --resource-group YOUR_RESOURCE_GROUP \
  --application-type web

# Get connection string
az monitor app-insights component show \
  --app nlp-api-insights \
  --resource-group YOUR_RESOURCE_GROUP \
  --query connectionString
```

### 5.2 Add Connection String to .env
```env
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://...
```

### 5.3 Create Alert Rules

See `azure-monitor-alerts.json` for detailed alert configurations.

**Quick Setup:**
```bash
# Create action group for notifications
az monitor action-group create \
  --name NLP-API-Alerts \
  --resource-group YOUR_RESOURCE_GROUP \
  --short-name nlp-alert \
  --email-receiver name=admin email=admin@yourdomain.com

# Create high memory alert
az monitor metrics alert create \
  --name HighMemoryUsage \
  --resource-group YOUR_RESOURCE_GROUP \
  --scopes /subscriptions/YOUR_SUBSCRIPTION/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.Compute/virtualMachines/YOUR_VM_NAME \
  --condition "avg Percentage Memory > 85" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action NLP-API-Alerts \
  --severity 1
```

---

## STEP 6: DEPLOY APPLICATION

### 6.1 Build and Start Containers
```bash
# Build images
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f api
docker-compose logs -f nginx
```

### 6.2 Verify Deployment
```bash
# Check container status
docker-compose ps

# Test health endpoint (HTTP)
curl http://localhost/health

# Test health endpoint (HTTPS)
curl https://yourdomain.com/health

# Check Redis connection
docker-compose exec api python -c "from redis_cache import redis_cache; print(redis_cache.health_check())"
```

### 6.3 Test API Endpoints
```bash
# Test with API key
curl -X POST https://yourdomain.com/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message", "compact": true}'
```

---

## STEP 7: SECURITY HARDENING

### 7.1 Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Verify rules
sudo ufw status
```

### 7.2 Fail2Ban (Prevent Brute Force)
```bash
# Install fail2ban
sudo apt-get install fail2ban

# Configure for nginx
sudo nano /etc/fail2ban/jail.local

# Add:
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

# Restart
sudo systemctl restart fail2ban
```

### 7.3 Secure .env File
```bash
# Set restrictive permissions
chmod 600 .env

# Never commit to git
echo ".env" >> .gitignore
echo ".env.production" >> .gitignore
```

---

## STEP 8: MONITORING & LOGGING

### 8.1 Setup Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/nlp-api

# Add:
/path/to/project/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose exec nginx nginx -s reopen
    endscript
}
```

### 8.2 Monitor Resource Usage
```bash
# Install monitoring tools
sudo apt-get install htop iotop nethogs

# Real-time monitoring
htop                    # CPU & Memory
docker stats            # Container stats
sudo iotop              # Disk I/O
sudo nethogs            # Network usage
```

### 8.3 Application Logs
```bash
# View live logs
docker-compose logs -f api

# View specific container
docker-compose logs -f nginx

# Save logs to file
docker-compose logs api > api-logs-$(date +%Y%m%d).log
```

---

## STEP 9: BACKUP STRATEGY

### 9.1 Data Backup
```bash
# Create backup script
nano backup.sh

#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/nlp-api"

mkdir -p $BACKUP_DIR

# Backup volumes
docker run --rm \
  -v nlp-api_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/data-$DATE.tar.gz /data

# Backup logs
tar czf $BACKUP_DIR/logs-$DATE.tar.gz logs/

# Backup adaptive learning data
tar czf $BACKUP_DIR/adaptive-learning-$DATE.tar.gz adaptive_learning/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Make executable
chmod +x backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /path/to/project/backup.sh
```

---

## STEP 10: PERFORMANCE TUNING

### 10.1 Verify Worker Configuration
```bash
# Check number of workers
docker-compose exec api ps aux | grep gunicorn

# Should show 2-3 worker processes (not 17!)
```

### 10.2 Monitor Cache Performance
```bash
# Check Redis cache hit rate
docker-compose exec api python -c "
from adaptive_learning import get_learning_statistics
stats = get_learning_statistics()
print(f'Cache Hit Rate: {stats.get(\"cache_hit_rate\", 0):.2%}')
"
```

### 10.3 Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -p test-request.json \
  https://yourdomain.com/analyze

# Create test-request.json
echo '{"text": "Test message", "compact": true}' > test-request.json
```

---

## TROUBLESHOOTING

### Issue: High Memory Usage
```bash
# Check memory
free -h

# Check container memory
docker stats

# Reduce workers if needed
# Edit .env: WORKERS=2
docker-compose restart api
```

### Issue: SSL Certificate Errors
```bash
# Test certificate
openssl s_client -connect yourdomain.com:443

# Check nginx config
docker-compose exec nginx nginx -t

# Renew Let's Encrypt
sudo certbot renew --force-renewal
```

### Issue: Redis Connection Failed
```bash
# Test Redis from container
docker-compose exec api python -c "
from redis_cache import redis_cache
print(redis_cache.health_check())
"

# Check environment variables
docker-compose exec api env | grep REDIS
```

### Issue: 502 Bad Gateway
```bash
# Check API container
docker-compose logs api

# Check if API is running
docker-compose ps

# Restart services
docker-compose restart api nginx
```

---

## MAINTENANCE

### Regular Tasks

**Daily:**
- Monitor Azure alerts dashboard
- Check error logs: `docker-compose logs api | grep ERROR`

**Weekly:**
- Review disk usage: `df -h`
- Check SSL expiry: `sudo certbot certificates`
- Review performance metrics in Azure Portal

**Monthly:**
- Update dependencies: `docker-compose pull && docker-compose up -d`
- Review and optimize cache settings
- Analyze slow queries in logs
- Security updates: `sudo apt-get update && sudo apt-get upgrade`

---

## SCALING GUIDE

### Vertical Scaling (Increase VM Size)
```bash
# Stop containers
docker-compose down

# In Azure Portal: Resize VM to D16s v3

# Update .env
WORKERS=4  # Can increase with more resources

# Restart
docker-compose up -d
```

### Horizontal Scaling (Multiple Instances)
1. Deploy same setup to multiple VMs
2. Configure Azure Load Balancer
3. All instances share same Upstash Redis
4. Update DNS to point to Load Balancer

---

## ROLLBACK PROCEDURE

```bash
# If deployment fails, rollback:

# Stop containers
docker-compose down

# Restore from backup
cd /backups/nlp-api
tar xzf data-YYYYMMDD-HHMMSS.tar.gz -C /path/to/project/

# Start previous version
git checkout previous-commit
docker-compose up -d

# Verify
curl https://yourdomain.com/health
```

---

## SUPPORT & CONTACTS

- **Azure Support**: Portal > Help + Support
- **Upstash Support**: https://upstash.com/docs
- **API Documentation**: https://yourdomain.com/docs

---

## CHECKLIST

Before going live:

- [ ] WORKERS=2 in .env
- [ ] Strong API_KEY set (32+ chars)
- [ ] Strong JWT_SECRET_KEY set
- [ ] ALLOWED_ORIGINS updated with actual domain
- [ ] Upstash Redis configured and tested
- [ ] SSL certificates installed and valid
- [ ] Nginx configuration updated with domain
- [ ] Azure Monitor alerts configured
- [ ] Firewall rules configured
- [ ] Fail2ban installed
- [ ] Log rotation configured
- [ ] Backup script scheduled
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on monitoring/troubleshooting
- [ ] Rollback procedure tested

---

**Deployment Date**: _________________
**Deployed By**: _________________
**Production URL**: https://yourdomain.com
