#!/bin/bash

# ========================================
# SSL Certificate Setup Script
# For Azure VM Production Deployment
# ========================================

set -e

echo "================================================"
echo "SSL Certificate Setup for NLP API"
echo "================================================"

# Configuration
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"

echo ""
echo "Please update the following variables:"
echo "DOMAIN: $DOMAIN"
echo "EMAIL: $EMAIL"
echo ""
read -p "Have you updated the domain and email? (yes/no): " CONFIRMED

if [ "$CONFIRMED" != "yes" ]; then
    echo "Please edit this script and update DOMAIN and EMAIL variables."
    exit 1
fi

# ========================================
# Option 1: Let's Encrypt (Recommended)
# ========================================
echo ""
echo "Setting up Let's Encrypt SSL certificate..."
echo ""

# Install Certbot
echo "Installing Certbot..."
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "Stopping nginx..."
docker-compose down nginx || true

# Obtain certificate
echo "Obtaining SSL certificate for $DOMAIN..."
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN \
    -d api.$DOMAIN

# Create directory for certificates in project
echo "Creating certificate directory..."
mkdir -p ./ssl/letsencrypt

# Copy certificates
echo "Copying certificates..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./ssl/letsencrypt/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./ssl/letsencrypt/
sudo cp /etc/letsencrypt/live/$DOMAIN/chain.pem ./ssl/letsencrypt/
sudo chmod 644 ./ssl/letsencrypt/*.pem

# Update docker-compose.yml volume mount
echo ""
echo "================================================"
echo "Manual Step Required:"
echo "================================================"
echo "Update docker-compose.yml nginx service to mount certificates:"
echo ""
echo "  nginx:"
echo "    volumes:"
echo "      - ./nginx.conf:/etc/nginx/nginx.conf:ro"
echo "      - ./ssl/letsencrypt:/etc/letsencrypt/live/$DOMAIN:ro"
echo ""

# Set up auto-renewal
echo "Setting up auto-renewal..."
sudo certbot renew --dry-run

# Create renewal hook
cat > /tmp/renewal-hook.sh << 'EOF'
#!/bin/bash
# Copy renewed certificates to project
DOMAIN="yourdomain.com"
PROJECT_PATH="/path/to/your/project"

cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $PROJECT_PATH/ssl/letsencrypt/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $PROJECT_PATH/ssl/letsencrypt/
cp /etc/letsencrypt/live/$DOMAIN/chain.pem $PROJECT_PATH/ssl/letsencrypt/

# Reload nginx
cd $PROJECT_PATH
docker-compose exec nginx nginx -s reload
EOF

sudo mv /tmp/renewal-hook.sh /etc/letsencrypt/renewal-hooks/post/copy-certs.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/copy-certs.sh

# Add cron job for auto-renewal
echo "Adding auto-renewal cron job..."
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --deploy-hook '/etc/letsencrypt/renewal-hooks/post/copy-certs.sh'") | sudo crontab -

echo ""
echo "================================================"
echo "SSL Certificate Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Update nginx.conf with your actual domain name"
echo "2. Update docker-compose.yml to mount certificates"
echo "3. Restart containers: docker-compose up -d"
echo "4. Test HTTPS: https://$DOMAIN/health"
echo ""
echo "Certificate will auto-renew every 60 days via cron job."
echo ""

# ========================================
# Alternative: Generate Self-Signed Certificate (Development/Testing Only)
# ========================================
generate_self_signed() {
    echo ""
    echo "Generating self-signed certificate (NOT for production)..."
    
    mkdir -p ./ssl/self-signed
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ./ssl/self-signed/key.pem \
        -out ./ssl/self-signed/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    
    echo ""
    echo "Self-signed certificate generated at ./ssl/self-signed/"
    echo "Update nginx.conf to use these certificates."
    echo ""
    echo "WARNING: Browsers will show security warnings with self-signed certificates."
    echo "Use Let's Encrypt for production!"
    echo ""
}

# Uncomment to generate self-signed certificate instead
# generate_self_signed

