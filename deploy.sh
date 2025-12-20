#!/bin/bash

################################################################################
# Sajborg.com Deployment Script
# This script automates the deployment of the Flask application on Ubuntu
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/Sajborg"
APP_USER="www-data"
APP_GROUP="www-data"
DOMAIN="sajborg.com"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sajborg.com Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: Update system packages
echo -e "${YELLOW}[1/12] Updating system packages...${NC}"
apt update
apt upgrade -y

# Step 2: Install required system packages
echo -e "${YELLOW}[2/12] Installing required system packages...${NC}"
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# Step 3: Install Gunicorn if not already installed
echo -e "${YELLOW}[3/12] Checking for Gunicorn...${NC}"
if [ ! -d "$APP_DIR/venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $APP_DIR/venv
fi

# Step 4: Activate virtual environment and install dependencies
echo -e "${YELLOW}[4/12] Installing Python dependencies...${NC}"
source $APP_DIR/venv/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
pip install gunicorn
deactivate

# Step 5: Create .env file if it doesn't exist
echo -e "${YELLOW}[5/12] Setting up environment variables...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp $APP_DIR/.env.example $APP_DIR/.env

    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" $APP_DIR/.env

    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit $APP_DIR/.env and configure your settings!${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Step 6: Create instance directory and set permissions
echo -e "${YELLOW}[6/12] Creating instance directory...${NC}"
mkdir -p $APP_DIR/instance
mkdir -p $APP_DIR/uploads
mkdir -p /var/log/gunicorn

# Step 7: Initialize database
echo -e "${YELLOW}[7/12] Initializing database...${NC}"
cd $APP_DIR
source venv/bin/activate
export FLASK_APP=app.py

# Check if migrations directory exists
if [ ! -d "$APP_DIR/migrations" ]; then
    echo -e "${YELLOW}Initializing Flask-Migrate...${NC}"
    flask db init
fi

echo -e "${YELLOW}Running database migrations...${NC}"
flask db migrate -m "Deployment migration" || true
flask db upgrade

deactivate

# Step 8: Set proper permissions
echo -e "${YELLOW}[8/12] Setting file permissions...${NC}"
chown -R $APP_USER:$APP_GROUP $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/instance
chmod -R 775 $APP_DIR/uploads
chmod -R 775 /var/log/gunicorn

# If database exists, set proper permissions
if [ -f "$APP_DIR/instance/pcshop.db" ]; then
    chmod 660 $APP_DIR/instance/pcshop.db
    chown $APP_USER:$APP_GROUP $APP_DIR/instance/pcshop.db
fi

# Step 9: Install systemd service
echo -e "${YELLOW}[9/12] Installing systemd service...${NC}"
cp $APP_DIR/sajborg.service /etc/systemd/system/sajborg.service
systemctl daemon-reload
systemctl enable sajborg.service
systemctl restart sajborg.service

# Check service status
if systemctl is-active --quiet sajborg.service; then
    echo -e "${GREEN}✓ Gunicorn service started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start Gunicorn service${NC}"
    systemctl status sajborg.service
    exit 1
fi

# Step 10: Configure Nginx
echo -e "${YELLOW}[10/12] Configuring Nginx...${NC}"
cp $APP_DIR/nginx_sajborg.conf /etc/nginx/sites-available/sajborg

# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Create symlink if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/sajborg ]; then
    ln -s /etc/nginx/sites-available/sajborg /etc/nginx/sites-enabled/
fi

# Test nginx configuration
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    systemctl restart nginx
else
    echo -e "${RED}✗ Nginx configuration is invalid${NC}"
    exit 1
fi

# Step 11: Setup SSL with Let's Encrypt
echo -e "${YELLOW}[11/12] Setting up SSL certificate...${NC}"
read -p "Do you want to set up SSL with Let's Encrypt? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || \
    echo -e "${YELLOW}⚠ SSL setup skipped or failed. You can run 'certbot --nginx -d $DOMAIN -d www.$DOMAIN' manually later.${NC}"
else
    echo -e "${YELLOW}⚠ Skipping SSL setup. Remember to uncomment the HTTPS redirect in /etc/nginx/sites-available/sajborg after setting up SSL.${NC}"
fi

# Step 12: Final checks
echo -e "${YELLOW}[12/12] Running final checks...${NC}"

# Check if Gunicorn is running
if systemctl is-active --quiet sajborg.service; then
    echo -e "${GREEN}✓ Gunicorn service is running${NC}"
else
    echo -e "${RED}✗ Gunicorn service is not running${NC}"
fi

# Check if Nginx is running
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
fi

# Display service status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Application Directory: ${YELLOW}$APP_DIR${NC}"
echo -e "Domain: ${YELLOW}$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Edit $APP_DIR/.env with your configuration"
echo "2. Check Gunicorn logs: sudo journalctl -u sajborg.service -f"
echo "3. Check Nginx logs: sudo tail -f /var/log/nginx/sajborg_error.log"
echo "4. Visit http://$DOMAIN to test your application"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  Restart Gunicorn: sudo systemctl restart sajborg.service"
echo "  Restart Nginx: sudo systemctl restart nginx"
echo "  View Gunicorn status: sudo systemctl status sajborg.service"
echo "  View Nginx status: sudo systemctl status nginx"
echo ""
