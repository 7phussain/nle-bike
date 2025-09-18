#!/bin/bash

# NLE Bike - Production Deployment Script
# Author: MiniMax Agent

echo "🚀 Deploying NLE Bike to Production..."

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
  echo "⚠️  WARNING: Running as root is not recommended for production"
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Set production environment
export FLASK_ENV=production
export DEBUG=false

# Create production directories
sudo mkdir -p /var/log/nlebike
sudo mkdir -p /var/lib/nlebike
sudo chown $USER:$USER /var/log/nlebike
sudo chown $USER:$USER /var/lib/nlebike

# Copy application files
echo "📁 Copying application files..."
sudo cp -r . /opt/nlebike/
sudo chown -R $USER:$USER /opt/nlebike/

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd /opt/nlebike
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Setup database
echo "🗄️ Setting up production database..."
python3 backend/inventory_manager.py &
SCRAPER_PID=$!
sleep 10
kill $SCRAPER_PID

# Configure Supervisor
echo "⚙️ Configuring Supervisor..."
sudo tee /etc/supervisor/conf.d/nlebike.conf > /dev/null <<EOF
[program:nlebike-api]
command=/opt/nlebike/venv/bin/python /opt/nlebike/backend/api_server.py
directory=/opt/nlebike
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/nlebike/api_error.log
stdout_logfile=/var/log/nlebike/api_access.log
environment=PATH="/opt/nlebike/venv/bin"

[program:nlebike-inventory]
command=/opt/nlebike/venv/bin/python /opt/nlebike/backend/inventory_manager.py
directory=/opt/nlebike
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/nlebike/inventory_error.log
stdout_logfile=/var/log/nlebike/inventory.log
environment=PATH="/opt/nlebike/venv/bin"
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/nlebike > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (add your certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/javascript application/javascript application/json;
    
    # Static files
    location /static/ {
        alias /opt/nlebike/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/nlebike /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Setup log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/nlebike > /dev/null <<EOF
/var/log/nlebike/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        supervisorctl restart nlebike-api
        supervisorctl restart nlebike-inventory
    endscript
}
EOF

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw --force enable

# Start services
echo "🚀 Starting services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nlebike-api
sudo supervisorctl start nlebike-inventory
sudo systemctl restart nginx
sudo systemctl enable nginx
sudo systemctl enable supervisor

# Create backup script
echo "💾 Creating backup script..."
sudo tee /usr/local/bin/backup-nlebike > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/nlebike"
DATE=\$(date +"%Y%m%d_%H%M%S")

mkdir -p \$BACKUP_DIR

# Backup database
cp /opt/nlebike/data/inventory.db \$BACKUP_DIR/inventory_\$DATE.db

# Backup application files
tar -czf \$BACKUP_DIR/app_\$DATE.tar.gz -C /opt/nlebike .

# Keep only last 30 days of backups
find \$BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

sudo chmod +x /usr/local/bin/backup-nlebike

# Schedule daily backups
echo "🔄 Scheduling daily backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-nlebike") | crontab -

# Create maintenance script
sudo tee /usr/local/bin/nlebike-maintenance > /dev/null <<EOF
#!/bin/bash
echo "NLE Bike Maintenance"
echo "==========================="
echo "Status:"
supervisorctl status
echo ""
echo "Logs (last 20 lines):"
tail -20 /var/log/nlebike/api_access.log
echo ""
echo "Disk usage:"
df -h /opt/nlebike
echo ""
echo "Memory usage:"
free -h
EOF

sudo chmod +x /usr/local/bin/nlebike-maintenance

echo ""
echo "🎉 Production deployment complete!"
echo ""
echo "Next steps:"
echo "1. Update DNS to point to this server"
echo "2. Install SSL certificates (Let's Encrypt recommended)"
echo "3. Update yourdomain.com in Nginx config"
echo "4. Configure email settings in .env"
echo "5. Set up monitoring (optional)"
echo ""
echo "Useful commands:"
echo "  Status: supervisorctl status"
echo "  Logs: tail -f /var/log/nlebike/api_access.log"
echo "  Restart: supervisorctl restart nlebike-api"
echo "  Backup: /usr/local/bin/backup-nlebike"
echo "  Maintenance: /usr/local/bin/nlebike-maintenance"
echo ""
echo "Site should be accessible at: http://$(hostname -I | awk '{print $1}')"
echo "API docs: http://$(hostname -I | awk '{print $1}')/docs"
echo ""
echo "Production deployment successful! 🚀"