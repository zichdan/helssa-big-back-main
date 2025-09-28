# 🚀 راهنمای Deployment در HELSSA

## 📋 فهرست مطالب

- [پیش‌نیازها](## 📦 پیش‌نیازها)
- [آماده‌سازی محیط](## 📦 آماده‌سازی محیط)
- [Deployment محلی](## 📦 Deployment محلی)
- [Deployment در Production](## 📦 Deployment در production)
- [پیکربندی سرور](## 📦 پیکربندی سرور)
- [مدیریت SSL و دامنه](## 📦 مدیریت ssl و دامنه)
- [مانیتورینگ و نگهداری](## 📦 مانیتورینگ و نگهداری)
- [Scaling و بهینه‌سازی](## 📦 Scaling و بهینه‌سازی)

---

## 📦 پیش‌نیازها

### سیستم عامل و نرم‌افزارها

- **OS**: Ubuntu 20.04 LTS یا بالاتر
- **Docker**: نسخه 20.10.0+
- **Docker Compose**: نسخه 1.29.0+
- **Git**: نسخه 2.25.0+
- **Python**: نسخه 3.11+
- **Node.js**: نسخه 18.0+ (برای frontend)

### منابع سخت‌افزاری

#### حداقل منابع (Development)

```yaml
CPU: 2 cores
RAM: 4 GB
Storage: 20 GB SSD
Network: 100 Mbps
```

#### منابع توصیه شده (Production)

```yaml
CPU: 8 cores
RAM: 16 GB
Storage: 100 GB SSD (RAID 10)
Network: 1 Gbps
Database: Dedicated MySQL server
Cache: Dedicated Redis server
```

### دسترسی‌ها و کلیدها

```bash
# فایل‌های مورد نیاز
.env                    # متغیرهای محیطی
ssl/cert.pem           # گواهی SSL
ssl/key.pem            # کلید خصوصی SSL
secrets/               # کلیدهای API و رمزنگاری
```

## 🔧 آماده‌سازی محیط

### 1. نصب Dependencies سیستم

```bash
#!/bin/bash
# install-dependencies.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    net-tools \
    ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
docker --version
docker-compose --version
node --version
npm --version
python3 --version
```

### 2. تنظیمات Firewall

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow custom ports if needed
sudo ufw allow 8000/tcp  # Django dev server
sudo ufw allow 3000/tcp  # React dev server
sudo ufw allow 9000/tcp  # MinIO

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 3. ایجاد ساختار دایرکتوری

```bash
# Create project structure
mkdir -p /opt/helssa
cd /opt/helssa

# Clone repository
git clone https://github.com/helssa/platform.git .

# Create necessary directories
mkdir -p \
    logs \
    backups \
    media \
    static \
    ssl \
    secrets \
    data/mysql \
    data/redis \
    data/minio

# Set permissions
sudo chown -R $USER:$USER /opt/helssa
chmod -R 755 /opt/helssa
chmod -R 700 /opt/helssa/secrets
```

### 4. پیکربندی Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit environment variables
nano .env
```

```env
# .env file
# Django Settings
DJANGO_SECRET_KEY=your-very-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=helssa.ir,www.helssa.ir,api.helssa.ir
DJANGO_SETTINGS_MODULE=helssa.settings.production

# Database
DB_ENGINE=django.db.backends.mysql
DB_NAME=helssa_db
DB_USER=helssa_user
DB_PASSWORD=strong-database-password
DB_HOST=mysql
DB_PORT=3306

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=strong-redis-password

# MinIO
MINIO_ACCESS_KEY=helssa-access-key
MINIO_SECRET_KEY=helssa-secret-key
MINIO_ENDPOINT=minio:9000
MINIO_USE_SSL=False

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@helssa.ir
EMAIL_HOST_PASSWORD=email-password
EMAIL_USE_TLS=True

# SMS (Kavenegar)
KAVENEGAR_API_KEY=your-kavenegar-api-key
KAVENEGAR_SENDER=10004346

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Payment Gateways
ZARINPAL_MERCHANT_ID=your-zarinpal-merchant
IDPAY_API_KEY=your-idpay-key
BITPAYIR_API_KEY=your-bitpay-key

# Security
CORS_ALLOWED_ORIGINS=https://helssa.ir,https://app.helssa.ir
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=True
GRAFANA_ADMIN_PASSWORD=strong-grafana-password
```

## 🏠 Deployment محلی

### 1. Build و راه‌اندازی

```bash
# Build images
docker-compose -f docker-compose.yml build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 2. تست‌های اولیه

```bash
# Health check
curl http://localhost:8000/health/

# API test
curl http://localhost:8000/api/v1/

# Database connection test
docker-compose exec web python manage.py dbshell

# Redis test
docker-compose exec redis redis-cli ping

# MinIO test
curl http://localhost:9000/minio/health/live
```

## 🌐 Deployment در Production

### 1. آماده‌سازی Production

```bash
#!/bin/bash
# production-setup.sh

# Set production environment
export DJANGO_SETTINGS_MODULE=helssa.settings.production

# Create production compose file
cat > docker-compose.prod.yml << 'EOF'
version: '3.9'

services:
  web:
    image: helssa/web:latest
    restart: always
    environment:
      - DJANGO_SETTINGS_MODULE=helssa.settings.production
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    depends_on:
      - mysql
      - redis
      - minio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  nginx:
    image: helssa/nginx:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - web

  mysql:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql-init:/docker-entrypoint-initdb.d
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  worker:
    image: helssa/web:latest
    restart: always
    command: celery -A helssa worker -l info -Q default,stt,ai,billing
    environment:
      - DJANGO_SETTINGS_MODULE=helssa.settings.production
    depends_on:
      - redis
      - mysql
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G

  beat:
    image: helssa/web:latest
    restart: always
    command: celery -A helssa beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=helssa.settings.production
    depends_on:
      - redis
      - mysql

volumes:
  mysql_data:
  redis_data:
  minio_data:
  static_volume:
  media_volume:
  nginx_logs:
EOF
```

### 2. CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
          
      - name: Run tests
        run: |
          python manage.py test
          
      - name: Run security checks
        run: |
          python manage.py check --deploy
          safety check
          bandit -r . -f json

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker build -t helssa/web:latest -f Dockerfile .
          docker build -t helssa/nginx:latest -f nginx/Dockerfile .
          
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push helssa/web:latest
          docker push helssa/nginx:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/helssa
            git pull origin main
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker system prune -f
```

### 3. Database Migration Strategy

```bash
#!/bin/bash
# migrate-production.sh

# Create backup before migration
echo "Creating database backup..."
docker-compose exec mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} helssa_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Put site in maintenance mode
echo "Enabling maintenance mode..."
docker-compose exec web python manage.py maintenance_mode on

# Run migrations
echo "Running migrations..."
docker-compose exec web python manage.py migrate --noinput

# Verify migrations
docker-compose exec web python manage.py showmigrations

# Disable maintenance mode
echo "Disabling maintenance mode..."
docker-compose exec web python manage.py maintenance_mode off

echo "Migration completed successfully!"
```

## ⚙️ پیکربندی سرور

### 1. Nginx Production Config

```nginx
# /etc/nginx/sites-available/helssa
upstream helssa_backend {
    least_conn;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

# HTTP redirect
server {
    listen 80;
    server_name helssa.ir www.helssa.ir api.helssa.ir;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name helssa.ir www.helssa.ir;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/helssa.ir.crt;
    ssl_certificate_key /etc/nginx/ssl/helssa.ir.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.helssa.ir wss://ws.helssa.ir" always;

    # Logging
    access_log /var/log/nginx/helssa.access.log;
    error_log /var/log/nginx/helssa.error.log;

    # Root location
    root /var/www/helssa/frontend/build;
    index index.html;

    # Static files
    location /static/ {
        alias /var/www/helssa/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /media/ {
        alias /var/www/helssa/media/;
        expires 1h;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options "nosniff";
    }

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://helssa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check
    location /health/ {
        access_log off;
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
    }

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security
    location ~ /\. {
        deny all;
    }

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml application/atom+xml image/svg+xml;
}
```

### 2. Systemd Services

```ini
# /etc/systemd/system/helssa-web.service
[Unit]
Description=HELSSA Web Service
After=network.target mysql.service redis.service

[Service]
Type=simple
User=helssa
Group=helssa
WorkingDirectory=/opt/helssa
Environment="DJANGO_SETTINGS_MODULE=helssa.settings.production"
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up web
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/helssa-worker.service
[Unit]
Description=HELSSA Celery Worker
After=network.target mysql.service redis.service

[Service]
Type=simple
User=helssa
Group=helssa
WorkingDirectory=/opt/helssa
Environment="DJANGO_SETTINGS_MODULE=helssa.settings.production"
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Backup Configuration

```bash
#!/bin/bash
# /opt/helssa/scripts/backup.sh

# Configuration
BACKUP_DIR="/opt/helssa/backups"
RETENTION_DAYS=30
S3_BUCKET="helssa-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup MySQL
echo "Backing up MySQL..."
docker-compose exec -T mysql mysqldump \
    -u root -p${MYSQL_ROOT_PASSWORD} \
    --single-transaction \
    --routines \
    --triggers \
    helssa_db | gzip > ${BACKUP_DIR}/mysql_${DATE}.sql.gz

# Backup Redis
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli \
    --rdb ${BACKUP_DIR}/redis_${DATE}.rdb \
    BGSAVE

# Backup MinIO data
echo "Backing up MinIO..."
docker-compose exec -T minio mc mirror \
    minio/media ${BACKUP_DIR}/minio_media_${DATE}

# Backup configurations
echo "Backing up configurations..."
tar -czf ${BACKUP_DIR}/config_${DATE}.tar.gz \
    .env \
    docker-compose.yml \
    docker-compose.prod.yml \
    nginx/

# Upload to S3
echo "Uploading to S3..."
aws s3 sync ${BACKUP_DIR} s3://${S3_BUCKET}/

# Clean old backups
echo "Cleaning old backups..."
find ${BACKUP_DIR} -type f -mtime +${RETENTION_DAYS} -delete

echo "Backup completed successfully!"
```

## 🔒 مدیریت SSL و دامنه

### 1. تنظیم SSL با Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d helssa.ir -d www.helssa.ir -d api.helssa.ir

# Test renewal
sudo certbot renew --dry-run

# Setup auto-renewal
sudo crontab -e
# Add this line:
0 3 * * * /usr/bin/certbot renew --quiet
```

### 2. تنظیمات DNS

```bash
# DNS Records needed:
A     @          1.2.3.4         # Main domain
A     www        1.2.3.4         # WWW subdomain
A     api        1.2.3.4         # API subdomain
A     app        1.2.3.4         # App subdomain
CNAME ws         helssa.ir       # WebSocket
MX    @          mail.helssa.ir  # Email
TXT   @          "v=spf1 ..."    # SPF record
TXT   _dmarc     "v=DMARC1..."   # DMARC record
```

### 3. CDN Configuration

```javascript
// Cloudflare settings
{
  "ssl": {
    "mode": "full_strict",
    "min_version": "1.2"
  },
  "security": {
    "level": "high",
    "challenge_ttl": 1800,
    "browser_check": "on"
  },
  "performance": {
    "cache_level": "standard",
    "browser_cache_ttl": 14400,
    "always_online": "on"
  },
  "firewall_rules": [
    {
      "expression": "(ip.geoip.country ne \"IR\")",
      "action": "challenge"
    },
    {
      "expression": "(http.request.uri.path contains \"/admin\")",
      "action": "challenge"
    }
  ]
}
```

## 📊 مانیتورینگ و نگهداری

### 1. Prometheus Configuration

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-exporter:9104']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts/*.yml'
```

### 2. Alert Rules

```yaml
# prometheus/alerts/helssa.yml
groups:
  - name: helssa_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(django_http_responses_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: DatabaseDown
        expr: mysql_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MySQL database is down"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"

      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
```

### 3. Health Check Script

```bash
#!/bin/bash
# health-check.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🏥 HELSSA Health Check"
echo "======================"

# Check Docker services
echo -n "Docker Services: "
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Some services are down${NC}"
    docker-compose ps
fi

# Check web server
echo -n "Web Server: "
if curl -s http://localhost/health/ > /dev/null; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Check database
echo -n "Database: "
if docker-compose exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Connection failed${NC}"
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Connection failed${NC}"
fi

# Check disk space
echo -n "Disk Space: "
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo -e "${GREEN}✓ ${DISK_USAGE}% used${NC}"
elif [ $DISK_USAGE -lt 90 ]; then
    echo -e "${YELLOW}⚠ ${DISK_USAGE}% used${NC}"
else
    echo -e "${RED}✗ ${DISK_USAGE}% used${NC}"
fi

# Check memory
echo -n "Memory: "
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEM_USAGE -lt 80 ]; then
    echo -e "${GREEN}✓ ${MEM_USAGE}% used${NC}"
elif [ $MEM_USAGE -lt 90 ]; then
    echo -e "${YELLOW}⚠ ${MEM_USAGE}% used${NC}"
else
    echo -e "${RED}✗ ${MEM_USAGE}% used${NC}"
fi

# Check SSL certificate
echo -n "SSL Certificate: "
CERT_DAYS=$(echo | openssl s_client -servername helssa.ir -connect helssa.ir:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2 | xargs -I {} date -d {} +%s)
CURRENT_DATE=$(date +%s)
DAYS_LEFT=$(( ($CERT_DAYS - $CURRENT_DATE) / 86400 ))

if [ $DAYS_LEFT -gt 30 ]; then
    echo -e "${GREEN}✓ Valid for ${DAYS_LEFT} days${NC}"
elif [ $DAYS_LEFT -gt 7 ]; then
    echo -e "${YELLOW}⚠ Expires in ${DAYS_LEFT} days${NC}"
else
    echo -e "${RED}✗ Expires in ${DAYS_LEFT} days${NC}"
fi

echo "======================"
```

## 📈 Scaling و بهینه‌سازی

### 1. Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.9'

services:
  web:
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
        order: start-first
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
        window: 120s

  worker:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G

  mysql:
    deploy:
      endpoint_mode: dnsrr
      replicas: 1
      placement:
        constraints:
          - node.labels.db == true
```

### 2. Performance Optimization

```python
# helssa/settings/production.py

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 100,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
        'KEY_PREFIX': 'helssa',
        'TIMEOUT': 300,
    }
}

# Database Connection Pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
}

# Static Files CDN
STATIC_URL = 'https://cdn.helssa.ir/static/'
MEDIA_URL = 'https://cdn.helssa.ir/media/'

# Security & Performance Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Compression
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 3. Database Optimization

```sql
-- Optimize MySQL for production
-- /opt/helssa/mysql-init/optimize.sql

-- Set optimal buffer sizes
SET GLOBAL innodb_buffer_pool_size = 8G;
SET GLOBAL innodb_log_file_size = 1G;
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL innodb_flush_method = O_DIRECT;

-- Query cache
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_size = 256M;
SET GLOBAL query_cache_limit = 2M;

-- Connection settings
SET GLOBAL max_connections = 500;
SET GLOBAL thread_cache_size = 50;

-- Create indexes for better performance
CREATE INDEX idx_encounter_date ON encounters(scheduled_at);
CREATE INDEX idx_user_phone ON unified_users(phone_number);
CREATE INDEX idx_transaction_user ON transactions(user_id, created_at);
CREATE INDEX idx_chat_session ON chat_messages(session_id, created_at);

-- Partition large tables
ALTER TABLE audit_logs PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p_2023 VALUES LESS THAN (2024),
    PARTITION p_2024 VALUES LESS THAN (2025),
    PARTITION p_2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

---

[ELEMENT: div align="center"]  

[→ قبلی: امنیت و Compliance](15-security-compliance.md) | [بعدی: راهنمای شروع سریع ←](17-quick-start.md)

</div>
