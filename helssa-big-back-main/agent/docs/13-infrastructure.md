# 🔧 زیرساخت و Docker در HELSSA

## 📋 فهرست مطالب

- [معرفی زیرساخت](## 🎯 معرفی زیرساخت)
- [معماری Docker](## 🐳 معماری Docker)
- [Docker Compose](## 📦 Docker Compose)
- [پایگاه داده MySQL](## 📦 پایگاه داده MySQL)
- [Redis Cache & Queue](## 📦 Redis Cache & Queue)
- [MinIO Object Storage](## 📦 MinIO Object Storage)
- [Nginx Reverse Proxy](## 🔐 Nginx Reverse Proxy)
- [مانیتورینگ و لاگینگ](## 📈 مانیتورینگ و لاگینگ)

---

## 🎯 معرفی زیرساخت

زیرساخت HELSSA بر پایه معماری میکروسرویس و کانتینرها طراحی شده و از تکنولوژی‌های مدرن برای اطمینان از کارایی، مقیاس‌پذیری و قابلیت اطمینان بالا استفاده می‌کند.

### ویژگی‌های کلیدی زیرساخت

- 🐳 **Containerized Architecture** با Docker
- 🔄 **Service Orchestration** با Docker Compose
- 📊 **High Performance Database** با MySQL 8
- ⚡ **In-Memory Cache** با Redis
- 📦 **Object Storage** با MinIO (S3 Compatible)
- 🔐 **Reverse Proxy & SSL** با Nginx
- 📈 **Monitoring** با Prometheus & Grafana
- 📝 **Centralized Logging** با ELK Stack

## 🏗️ معماری Docker

```mermaid
graph TB
    subgraph "External Layer"
        CLIENT[Clients]
        CDN[CDN/CloudFlare]
    end
    
    subgraph "Edge Layer"
        NGINX[Nginx<br/>Reverse Proxy]
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        WEB[Web Container<br/>Django/Gunicorn]
        API1[API Container 1]
        API2[API Container 2]
        WORKER[Celery Workers]
        BEAT[Celery Beat]
    end
    
    subgraph "Service Layer"
        AUTH[Auth Service]
        AI[AI Service]
        BILL[Billing Service]
        STT[STT Service]
    end
    
    subgraph "Data Layer"
        MYSQL[(MySQL 8<br/>Master)]
        MYSQL_R[(MySQL<br/>Read Replica)]
        REDIS[(Redis<br/>Cache/Queue)]
        MINIO[(MinIO<br/>Object Storage)]
    end
    
    subgraph "Infrastructure Layer"
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
    end
    
    CLIENT --> CDN
    CDN --> NGINX
    NGINX --> LB
    
    LB --> WEB
    LB --> API1
    LB --> API2
    
    WEB --> AUTH
    WEB --> AI
    WEB --> BILL
    
    WORKER --> REDIS
    WORKER --> STT
    
    API1 --> MYSQL
    API2 --> MYSQL_R
    
    WEB --> MINIO
    WORKER --> MINIO
    
    PROM --> GRAF
    ALL --> ELK
```

### ساختار پروژه زیرساخت

```python
infra/
├── docker/
│   ├── web/
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh
│   │   └── requirements.txt
│   ├── worker/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── ssl/
│   └── services/
│       ├── mysql/
│       ├── redis/
│       └── minio/
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose.dev.yml
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── health-check.sh
│   └── deploy.sh
├── configs/
│   ├── env.example
│   ├── secrets/
│   └── ssl/
└── monitoring/
    ├── prometheus/
    ├── grafana/
    └── elk/
```

## 🐳 Docker Compose

### Production Docker Compose

```yaml
# docker-compose.yml
version: '3.9'

x-common-variables: &common-variables
  DJANGO_SETTINGS_MODULE: helssa.settings.production
  REDIS_URL: redis://redis:6379/0
  DATABASE_URL: mysql://helssa:${DB_PASSWORD}@mysql:3306/helssa_db
  MINIO_URL: http://minio:9000
  CELERY_BROKER_URL: redis://redis:6379/1
  CELERY_RESULT_BACKEND: redis://redis:6379/2

services:
  # ===================
  # Web Application
  # ===================
  web:
    build:
      context: .
      dockerfile: ./infra/docker/web/Dockerfile
    container_name: helssa_web
    restart: unless-stopped
    volumes:
      - ./:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      <<: *common-variables
      DJANGO_SUPERUSER_USERNAME: ${DJANGO_SUPERUSER_USERNAME}
      DJANGO_SUPERUSER_EMAIL: ${DJANGO_SUPERUSER_EMAIL}
      DJANGO_SUPERUSER_PASSWORD: ${DJANGO_SUPERUSER_PASSWORD}
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=web"
      - "com.helssa.tier=application"

  # ===================
  # Celery Worker
  # ===================
  worker:
    build:
      context: .
      dockerfile: ./infra/docker/worker/Dockerfile
    container_name: helssa_worker
    restart: unless-stopped
    command: celery -A helssa worker -l info -Q default,stt,ai,billing
    volumes:
      - ./:/app
      - media_volume:/app/media
    environment:
      <<: *common-variables
      C_FORCE_ROOT: 'true'
    depends_on:
      - mysql
      - redis
      - minio
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=worker"
      - "com.helssa.tier=processing"

  # ===================
  # Celery Beat (Scheduler)
  # ===================
  beat:
    build:
      context: .
      dockerfile: ./infra/docker/worker/Dockerfile
    container_name: helssa_beat
    restart: unless-stopped
    command: celery -A helssa beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./:/app
    environment:
      <<: *common-variables
    depends_on:
      - mysql
      - redis
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=beat"
      - "com.helssa.tier=scheduling"

  # ===================
  # MySQL Database
  # ===================
  mysql:
    image: mysql:8.0
    container_name: helssa_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: helssa_db
      MYSQL_USER: helssa
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
      - ./infra/docker/services/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./infra/docker/services/mysql/my.cnf:/etc/mysql/conf.d/my.cnf
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=mysql"
      - "com.helssa.tier=database"

  # ===================
  # Redis Cache & Queue
  # ===================
  redis:
    image: redis:7-alpine
    container_name: helssa_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=redis"
      - "com.helssa.tier=cache"

  # ===================
  # MinIO Object Storage
  # ===================
  minio:
    image: minio/minio:latest
    container_name: helssa_minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      MINIO_BROWSER: "on"
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=minio"
      - "com.helssa.tier=storage"

  # ===================
  # Nginx Reverse Proxy
  # ===================
  nginx:
    build:
      context: .
      dockerfile: ./infra/docker/nginx/Dockerfile
    container_name: helssa_nginx
    restart: unless-stopped
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./infra/docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./infra/docker/nginx/conf.d:/etc/nginx/conf.d
      - ./infra/docker/nginx/ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=nginx"
      - "com.helssa.tier=edge"

  # ===================
  # Prometheus Monitoring
  # ===================
  prometheus:
    image: prom/prometheus:latest
    container_name: helssa_prometheus
    restart: unless-stopped
    volumes:
      - ./infra/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=prometheus"
      - "com.helssa.tier=monitoring"

  # ===================
  # Grafana Dashboard
  # ===================
  grafana:
    image: grafana/grafana:latest
    container_name: helssa_grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-clock-panel,grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - helssa_network
    labels:
      - "com.helssa.service=grafana"
      - "com.helssa.tier=monitoring"

# ===================
# Networks
# ===================
networks:
  helssa_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# ===================
# Volumes
# ===================
volumes:
  mysql_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
  static_volume:
    driver: local
  media_volume:
    driver: local
  nginx_logs:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### Web Dockerfile

```dockerfile
# infra/docker/web/Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    curl \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Copy and set permissions for entrypoint
COPY ./infra/docker/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 helssa && chown -R helssa:helssa /app
USER helssa

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120", "helssa.wsgi:application"]
```

### Entrypoint Script

```bash
#!/bin/bash
# infra/docker/web/entrypoint.sh

set -e

echo "Waiting for database..."
while ! nc -z mysql 3306; do
  sleep 0.1
done
echo "Database is ready!"

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis is ready!"

echo "Waiting for MinIO..."
while ! nc -z minio 9000; do
  sleep 0.1
done
echo "MinIO is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

# Create MinIO buckets
echo "Creating MinIO buckets..."
python manage.py shell -c "
from django.conf import settings
from minio import Minio
from minio.error import S3Error

client = Minio(
    'minio:9000',
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

buckets = ['media', 'static', 'backups', 'temp']
for bucket_name in buckets:
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f'Bucket {bucket_name} created.')
        else:
            print(f'Bucket {bucket_name} already exists.')
    except S3Error as e:
        print(f'Error creating bucket {bucket_name}: {e}')
"

# Execute the main command
exec "$@"
```

## 💾 پایگاه داده MySQL

### MySQL Configuration

```ini
# infra/docker/services/mysql/my.cnf
[mysqld]
# Character Set
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# InnoDB Settings
innodb_buffer_pool_size=2G
innodb_log_file_size=512M
innodb_flush_log_at_trx_commit=2
innodb_flush_method=O_DIRECT
innodb_file_per_table=1

# Performance
max_connections=200
thread_cache_size=50
query_cache_type=1
query_cache_size=256M
query_cache_limit=2M
tmp_table_size=256M
max_heap_table_size=256M

# Slow Query Log
slow_query_log=1
slow_query_log_file=/var/log/mysql/slow-query.log
long_query_time=2

# Binary Logging (for replication)
log_bin=mysql-bin
binlog_format=ROW
expire_logs_days=7
max_binlog_size=100M

# Security
skip-name-resolve
bind-address=0.0.0.0

[client]
default-character-set=utf8mb4
```

### Database Initialization

```sql
-- infra/docker/services/mysql/init.sql

-- Create database with proper charset
CREATE DATABASE IF NOT EXISTS helssa_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create read-only user for replicas
CREATE USER IF NOT EXISTS 'helssa_read'@'%' IDENTIFIED BY 'ReadOnlyPassword123!';
GRANT SELECT ON helssa_db.* TO 'helssa_read'@'%';

-- Create backup user
CREATE USER IF NOT EXISTS 'helssa_backup'@'%' IDENTIFIED BY 'BackupPassword123!';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON helssa_db.* TO 'helssa_backup'@'%';

-- Performance schema settings
UPDATE performance_schema.setup_instruments 
SET ENABLED = 'YES', TIMED = 'YES' 
WHERE NAME LIKE 'wait/io/file/%';

-- Create indexes for better performance
-- These will be created after Django migrations
```

### Database Backup Script

```bash
#!/bin/bash
# infra/scripts/backup.sh

# Configuration
BACKUP_DIR="/backups/mysql"
RETENTION_DAYS=7
DB_NAME="helssa_db"
DB_USER="helssa_backup"
DB_PASS="${MYSQL_BACKUP_PASSWORD}"
DB_HOST="mysql"
MINIO_BUCKET="backups"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Generate backup filename
BACKUP_FILE="${BACKUP_DIR}/helssa_db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Perform backup
echo "Starting database backup..."
mysqldump \
    --host=${DB_HOST} \
    --user=${DB_USER} \
    --password=${DB_PASS} \
    --single-transaction \
    --routines \
    --triggers \
    --add-drop-database \
    --databases ${DB_NAME} | gzip > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Database backup completed: ${BACKUP_FILE}"
    
    # Upload to MinIO
    echo "Uploading to MinIO..."
    mc alias set minio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
    mc cp ${BACKUP_FILE} minio/${MINIO_BUCKET}/mysql/
    
    # Clean old backups
    echo "Cleaning old backups..."
    find ${BACKUP_DIR} -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    # Clean old MinIO backups
    mc rm --recursive --force --older-than ${RETENTION_DAYS}d minio/${MINIO_BUCKET}/mysql/
    
    echo "Backup process completed successfully"
else
    echo "Database backup failed!"
    exit 1
fi
```

## 🚀 Redis Cache & Queue

### Redis Configuration for Django

```python
# helssa/settings/production.py

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'helssa',
        'TIMEOUT': 300,  # 5 minutes default
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,  # 24 hours
    },
    'api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'api',
        'TIMEOUT': 60,  # 1 minute
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# Celery Configuration
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/3'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/4'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-sessions': {
        'task': 'core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-subscription-status': {
        'task': 'billing.tasks.update_subscription_status',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'process-pending-transcripts': {
        'task': 'stt.tasks.process_pending_transcripts',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### Redis Health Check

```python
# core/utils/redis_health.py

import redis
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class RedisHealthCheck:
    """Redis health check utility"""
    
    @staticmethod
    def check_connection():
        """Check Redis connection"""
        try:
            # Test cache
            cache.set('health_check', 'OK', 10)
            value = cache.get('health_check')
            cache.delete('health_check')
            
            if value != 'OK':
                return False, "Cache test failed"
            
            # Test direct connection
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )
            r.ping()
            
            # Get info
            info = r.info()
            
            return True, {
                'connected': True,
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False, str(e)
```

## 📦 MinIO Object Storage

### MinIO Service Configuration

```python
# core/services/storage.py

from minio import Minio
from minio.error import S3Error
from django.conf import settings
import io
from typing import Optional, Dict
import hashlib

class MinIOStorageService:
    """MinIO storage service for file management"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self._ensure_buckets()
        
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        buckets = ['media', 'static', 'backups', 'temp', 'audio', 'documents']
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    
                    # Set bucket policy
                    if bucket in ['media', 'static']:
                        self._set_public_policy(bucket)
                        
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {str(e)}")
                
    def _set_public_policy(self, bucket_name: str):
        """Set public read policy for bucket"""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        self.client.set_bucket_policy(bucket_name, json.dumps(policy))
        
    async def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Upload file to MinIO"""
        
        try:
            # Calculate file hash
            file_hash = hashlib.md5(file_data).hexdigest()
            
            # Add metadata
            if metadata is None:
                metadata = {}
            metadata['md5'] = file_hash
            metadata['uploaded_by'] = 'helssa'
            
            # Upload
            result = self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
                metadata=metadata
            )
            
            # Generate URL
            url = self.get_presigned_url(bucket, object_name)
            
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
            
    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: int = 3600
    ) -> str:
        """Generate presigned URL for object"""
        
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(seconds=expires)
            )
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
```

### MinIO Backup Strategy

```python
# core/tasks/backup_tasks.py

@shared_task
def backup_to_minio():
    """Backup important data to MinIO"""
    
    storage = MinIOStorageService()
    backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup database
    db_backup_file = f"/tmp/db_backup_{backup_date}.sql.gz"
    os.system(f"mysqldump helssa_db | gzip > {db_backup_file}")
    
    with open(db_backup_file, 'rb') as f:
        storage.upload_file(
            bucket='backups',
            object_name=f'database/db_backup_{backup_date}.sql.gz',
            file_data=f.read(),
            content_type='application/gzip'
        )
        
    # Backup media files
    media_backup = f"/tmp/media_backup_{backup_date}.tar.gz"
    os.system(f"tar -czf {media_backup} /app/media")
    
    with open(media_backup, 'rb') as f:
        storage.upload_file(
            bucket='backups',
            object_name=f'media/media_backup_{backup_date}.tar.gz',
            file_data=f.read(),
            content_type='application/gzip'
        )
        
    # Clean old backups (keep last 7 days)
    cleanup_old_backups.delay()
```

## 🔐 Nginx Reverse Proxy

### Nginx Configuration

```nginx
# infra/docker/nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml application/atom+xml image/svg+xml;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    # Upstream
    upstream helssa_backend {
        least_conn;
        server web:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### Site Configuration

```nginx
# infra/docker/nginx/conf.d/helssa.conf

server {
    listen 80;
    server_name helssa.ir www.helssa.ir;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name helssa.ir www.helssa.ir;

    # SSL
    ssl_certificate /etc/nginx/ssl/helssa.crt;
    ssl_certificate_key /etc/nginx/ssl/helssa.key;

    # Logging
    access_log /var/log/nginx/helssa.access.log main;
    error_log /var/log/nginx/helssa.error.log;

    # Security
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 1h;
        add_header Cache-Control "public";
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Auth endpoints with stricter rate limiting
    location ~ ^/(auth|login|register)/ {
        limit_req zone=auth burst=5 nodelay;
        
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://helssa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for WebSocket
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
    }

    # Default location
    location / {
        limit_req zone=general burst=10 nodelay;
        
        proxy_pass http://helssa_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

## 📊 مانیتورینگ و لاگینگ

### Prometheus Configuration

```yaml
# infra/monitoring/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  # Django metrics
  - job_name: 'django'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'

  # MySQL exporter
  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-exporter:9104']

  # Redis exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node exporter
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Nginx exporter
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Health Check Endpoint

```python
# core/views/health.py

from django.http import JsonResponse
from django.views import View
from core.utils.redis_health import RedisHealthCheck
from django.db import connection
from minio import Minio
import time

class HealthCheckView(View):
    """System health check endpoint"""
    
    def get(self, request):
        start_time = time.time()
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        # Check Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status['services']['database'] = {
                'status': 'healthy',
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
            
        # Check Redis
        redis_start = time.time()
        redis_healthy, redis_info = RedisHealthCheck.check_connection()
        health_status['services']['redis'] = {
            'status': 'healthy' if redis_healthy else 'unhealthy',
            'info': redis_info,
            'response_time': f"{(time.time() - redis_start) * 1000:.2f}ms"
        }
        
        # Check MinIO
        try:
            minio_start = time.time()
            client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            buckets = client.list_buckets()
            health_status['services']['minio'] = {
                'status': 'healthy',
                'buckets': len(buckets),
                'response_time': f"{(time.time() - minio_start) * 1000:.2f}ms"
            }
        except Exception as e:
            health_status['services']['minio'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
            
        # Overall response time
        health_status['response_time'] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)
```

### Deployment Script

```bash
#!/bin/bash
# infra/scripts/deploy.sh

set -e

echo "🚀 Starting HELSSA deployment..."

# Load environment variables
source .env

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build and start services
echo "🏗️ Building Docker images..."
docker-compose -f docker-compose.yml build

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose run --rm web python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
./infra/scripts/health-check.sh

# Run post-deployment tasks
echo "✅ Running post-deployment tasks..."
docker-compose run --rm web python manage.py check --deploy

echo "✨ Deployment completed successfully!"

# Show service status
docker-compose ps
```

---

[ELEMENT: div align="center"]

[→ قبلی: تولید گزارش‌ها](12-output-generation.md) | [بعدی: API Reference ←](14-api-reference.md)

</div>
