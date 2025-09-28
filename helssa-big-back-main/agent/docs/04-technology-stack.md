# 🛠️ تکنولوژی و وابستگی‌های HELSSA

## 📋 فهرست مطالب

- [نمای کلی استک تکنولوژی](## 🎯 نمای کلی استک تکنولوژی)
- [Backend Technologies](## 💻 Backend Technologies)
- [Frontend Technologies](## 🎨 Frontend Technologies)
- [State Management & Data Fetching](## 📊 State Management & Data Fetching)
- [UI Components & Styling](## 🎨 UI Components & Styling)
- [Build Tools & Development](## 🛠️ Build Tools & Development)
- [AI/ML Stack](## 🤖 AI/ML Stack)
- [Infrastructure & DevOps](## 🏗️ Infrastructure & DevOps)

- [Web Server & Proxy](## 🌐 Web Server & Proxy)
- [Payment Gateways](## 💳 Payment Gateways)
- [Communication Services](## 📱 Communication Services)
- [Storage Services](## 📂 Storage Services)
- [Third-party Services](## 🔗 Third-party Services)
- [Development Tools](## 🛠️ Development Tools)
- [Security Stack](## 🔒 Security Stack)
- [Performance & Monitoring](## 📊 Performance & Monitoring)

---

## 🎯 نمای کلی استک تکنولوژی

```python
graph TB
    subgraph "Frontend Layer"
        REACT[React.js v18]
        NEXT[Next.js v14]
        RN[React Native]
        TS[TypeScript v5]
        MUI[Material-UI v5]
        REDUX[Redux Toolkit]
    end
    
    subgraph "Backend Layer"
        DJ[Django v4.2]
        DRF[DRF v3.14]
        CEL[Celery v5.3]
        FAST[FastAPI]
    end
    
    subgraph "AI/ML Layer"
        GPT[GPT-4 API]
        WHISP[Whisper API]
        LANG[LangChain]
        TORCH[PyTorch]
        TF[TensorFlow]
    end
    
    subgraph "Data Layer"
        MYSQL[MySQL v8.0]
        REDIS[Redis v7.0]
        MINIO[MinIO S3]
        ELASTIC[ElasticSearch]
    end
    
    subgraph "Infrastructure"
        DOCKER[Docker v24]
        K8S[Kubernetes]
        NGINX[Nginx v1.24]
        GITHUB[GitHub Actions]
    end
    
    subgraph "Services"
        AWS[AWS Services]
        BITPAY[BitPay.ir]
        KAVE[Kavenegar SMS]
        SENTRY[Sentry]
    end
    
    Frontend --> Backend
    Backend --> AI/ML
    Backend --> Data
    All --> Infrastructure
    Backend --> Services
```

## 💻 Backend Technologies

### Django Framework

```python
# Core Django Stack
Django==4.2.7                    # Web framework
djangorestframework==3.14.0      # REST API framework
django-cors-headers==4.3.0       # CORS handling
django-environ==0.11.2           # Environment management
django-extensions==3.2.3         # Developer tools
django-debug-toolbar==4.2.0      # Debug toolbar

# Django Enhancements
django-filter==23.3              # Queryset filtering
django-guardian==2.4.0           # Per-object permissions
django-import-export==3.3.1      # Data import/export
django-celery-beat==2.5.0        # Periodic tasks
django-celery-results==2.5.1     # Task results backend
```

### Authentication & Security

```python
# Authentication
djangorestframework-simplejwt==5.3.0  # JWT authentication
python-jose==3.3.0                    # JOSE implementation
cryptography==41.0.5                  # Cryptographic recipes
django-otp==1.3.0                     # One-time passwords
pyotp==2.9.0                          # OTP implementation

# Security
django-ratelimit==4.1.0          # Rate limiting
django-csp==3.7                  # Content Security Policy
django-defender==0.9.7           # Brute force protection
```

### 📊 Database & ORM

```python
# Database Drivers
mysqlclient==2.2.0               # MySQL connector
psycopg2-binary==2.9.9          # PostgreSQL adapter

# ORM Enhancements
django-model-utils==4.3.1        # Model utilities
django-mptt==0.15.0             # Tree structures
django-taggit==5.0.1            # Tagging
django-simple-history==3.4.0     # Model history
```

### 🔒 Authentication & Security

```python
# Authentication
djangorestframework-simplejwt==5.3.0  # JWT authentication
python-jose==3.3.0                    # JOSE implementation
cryptography==41.0.5                  # Cryptographic recipes
django-otp==1.3.0                     # One-time passwords
pyotp==2.9.0                          # OTP implementation

# Security
django-ratelimit==4.1.0          # Rate limiting
django-csp==3.7                  # Content Security Policy
django-defender==0.9.7           # Brute force protection
```

### 🔗 Async & Task Processing

```python
# Celery Stack
celery==5.3.4                    # Distributed task queue
redis==5.0.1                     # Redis client
kombu==5.3.4                     # Messaging library
amqp==5.2.0                      # AMQP client
billiard==4.2.0                  # Process pool



# Async Support
channels==4.0.0                  # WebSocket support
channels-redis==4.1.0            # Redis channel layer
daphne==4.0.0                    # ASGI server
```

## 🎨 Frontend Technologies

### React Ecosystem

```python
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.2.0",
    "@mui/material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0"
  }
}
```

### State Management & Data Fetching

```python
{
  "dependencies": {
    "@reduxjs/toolkit": "^1.9.7",
    "react-redux": "^8.1.3",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "swr": "^2.2.4"
  }
}
```

### UI Components & Styling

```python
{
  "dependencies": {
    "@mui/icons-material": "^5.14.0",
    "@mui/x-data-grid": "^6.18.0",
    "@mui/x-date-pickers": "^6.18.0",
    "tailwindcss": "^3.3.0",
    "framer-motion": "^10.16.0",
    "react-hook-form": "^7.47.0",
    "yup": "^1.3.0"
  }
}
```

### Build Tools & Development

```python
{
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^14.0.0",
    "cypress": "^13.0.0"
  }
}
```

## 🤖 AI/ML Stack

### OpenAI Integration

```python
# OpenAI/GapGPT
openai==1.3.0                    # OpenAI Python client
tiktoken==0.5.1                  # Token counting
langchain==0.0.340               # LLM framework
langchain-openai==0.0.5          # OpenAI integration
# OpenAI/GapGPT
openai==1.3.0                    # OpenAI Python client
tiktoken==0.5.1                  # Token counting
langchain==0.0.340               # LLM framework
langchain-openai==0.0.5          # OpenAI integration

# Configuration
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY'),
    'organization': os.getenv('OPENAI_ORG_ID'),
    'base_url': 'https://api.openai.com/v1',  # or GapGPT URL
    'models': {
        'chat': 'gpt-4-turbo-preview',
        'embedding': 'text-embedding-3-small',
        'whisper': 'whisper-1',
        'vision': 'gpt-4-vision-preview'
    }
}
```

### Speech Processing

```python
# Audio Processing
whisper==1.1.10                  # OpenAI Whisper
pydub==0.25.1                    # Audio manipulation
librosa==0.10.1                  # Audio analysis
soundfile==0.12.1                # Audio I/O
ffmpeg-python==0.2.0             # FFmpeg wrapper
```

### NLP & Text Processing

```python
# NLP Libraries
spacy==3.7.2                     # Industrial NLP
nltk==3.8.1                      # Natural Language Toolkit
transformers==4.35.0             # Hugging Face models
sentence-transformers==2.2.2     # Sentence embeddings

# Persian NLP
hazm==0.7.0                      # Persian text processing
parsivar==0.2.3                  # Persian text preprocessing
```

### Machine Learning

```python
# Core ML
numpy==1.24.3                    # Numerical computing
pandas==2.0.3                    # Data manipulation
scikit-learn==1.3.2              # Machine learning
scipy==1.11.4                    # Scientific computing

# Deep Learning
torch==2.1.0                     # PyTorch
torchvision==0.16.0              # Computer vision
tensorflow==2.14.0               # TensorFlow (optional)
```

## 🏗️ Infrastructure & DevOps

### Containerization

```python
# dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run migrations and collect static
RUN python manage.py collectstatic --noinput

# Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "medogram.wsgi:application"]
```

### 🚀 Orchestration

```python yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helssa-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: helssa-web
  template:
    metadata:
      labels:
        app: helssa-web
    spec:
      containers:
      - name: web
        image: helssa/web:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: helssa-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Web Server & Proxy

```python
# nginx/conf.d/helssa.conf
upstream helssa_backend {
    server web:8000;
}

server {
    listen 80;
    server_name helssa.com www.helssa.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name helssa.com www.helssa.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/helssa.crt;
    ssl_certificate_key /etc/ssl/private/helssa.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Locations
    location / {
        proxy_pass http://helssa_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/static/;
        expires 30d;
    }
    
    location /media/ {
        alias /app/media/;
        expires 7d;
    }
    
    location /ws/ {
        proxy_pass http://helssa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔗 Third-party Services

### Payment Gateways

```python
# Iranian Payment Gateways
PAYMENT_GATEWAYS = {
    'bitpay': {
        'api_key': os.getenv('BITPAY_API_KEY'),
        'endpoint': 'https://bitpay.ir/payment/',
        'callback': 'https://helssa.com/payment/callback/'
    },
    'zarinpal': {
        'merchant_id': os.getenv('ZARINPAL_MERCHANT'),
        'endpoint': 'https://api.zarinpal.com/pg/v4/',
        'callback': 'https://helssa.com/payment/zarinpal/verify/'
    },
    'idpay': {
        'api_key': os.getenv('IDPAY_API_KEY'),
        'endpoint': 'https://api.idpay.ir/v1.1/',
        'callback': 'https://helssa.com/payment/idpay/callback/'
    }
}

# International Payment
stripe==7.1.0                    # Stripe payments
paypal-checkout-serversdk==2.0.0 # PayPal SDK
```

### Communication Services

```python
# SMS Service
KAVENEGAR_CONFIG = {
    'api_key': os.getenv('KAVENEGAR_API_KEY'),
    'sender': '10008663',
    'templates': {
        'otp': 'verify',
        'appointment': 'appointment-reminder',
        'report': 'report-ready'
    }
}

# Email Service
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Push Notifications
FIREBASE_CONFIG = {
    'credentials': 'path/to/firebase-credentials.json',
    'project_id': 'helssa-app'
}
```

### Storage Services

```python
# MinIO/S3 Configuration
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = 'helssa-storage'
AWS_S3_ENDPOINT_URL = 'http://minio:9000'
AWS_S3_USE_SSL = False
AWS_QUERYSTRING_AUTH = False

# Storage Classes
STORAGE_CLASSES = {
    'default': 'STANDARD',
    'medical_images': 'GLACIER',
    'audio_files': 'STANDARD_IA',
    'documents': 'INTELLIGENT_TIERING'
}
```

## 🛠️ Development Tools

### Code Quality

```python
# Linting & Formatting
black==23.11.0                   # Code formatter
flake8==6.1.0                    # Style guide
isort==5.12.0                    # Import sorting
mypy==1.7.0                      # Type checking
pylint==3.0.2                    # Code analysis

# Pre-commit hooks
pre-commit==3.5.0                # Git hook framework
```

### Testing

```python
# Testing Framework
pytest==7.4.3                    # Test framework
pytest-django==4.7.0             # Django integration
pytest-cov==4.1.0                # Coverage plugin
pytest-asyncio==0.21.1           # Async testing
factory-boy==3.3.0               # Test fixtures
faker==20.0.0                    # Fake data

# API Testing
httpx==0.25.2                    # Async HTTP client
responses==0.24.1                # Mock HTTP responses
```

### Documentation

```python
# Documentation
sphinx==7.2.6                    # Documentation builder
sphinx-rtd-theme==2.0.0          # ReadTheDocs theme
drf-spectacular==0.26.5          # OpenAPI 3.0 schema
```

## 🔒 Security Stack

### Security Libraries

```python
# Security
python-decouple==3.8             # Env var management
argon2-cffi==23.1.0              # Password hashing
pyotp==2.9.0                     # 2FA/TOTP
qrcode==7.4.2                    # QR code generation

# Vulnerability Scanning
safety==2.3.5                    # Dependency checker
bandit==1.7.5                    # Security linter
```

### Encryption & Certificates

```bash
# SSL/TLS Certificates
certbot                          # Let's Encrypt
openssl                          # Certificate management

# Environment Encryption
ansible-vault                    # Secure secrets
mozilla-sops                     # Encrypted files
```

## 📊 Performance & Monitoring

### Monitoring Stack

```python
# APM & Monitoring
sentry-sdk==1.38.0               # Error tracking
prometheus-client==0.19.0        # Metrics
django-prometheus==2.3.1         # Django metrics
elastic-apm==6.19.0              # Elastic APM

# Logging
python-json-logger==2.0.7        # JSON logging
loguru==0.7.2                    # Advanced logging
```

### Performance Tools

```python
# Caching
django-redis==5.4.0              # Redis cache backend
django-cachalot==2.6.1           # ORM cache
django-cache-memoize==0.1.10     # Function memoization

# Optimization
django-silk==5.0.4               # Request profiling
django-debug-toolbar==4.2.0      # Debug toolbar
line-profiler==4.1.1             # Line profiling
memory-profiler==0.61.0          # Memory profiling
```

### Analytics

```python
# Analytics Integration
google-analytics-data==0.17.1    # Google Analytics
mixpanel==4.10.0                 # Mixpanel
segment-analytics-python==2.2.3  # Segment.io
```

---

[ELEMENT: div align="center"]

[→ قبلی: نمودار درختی پروژه](03-project-tree.md) | [بعدی: احراز هویت یکپارچه ←](05-authentication.md)

</div>
