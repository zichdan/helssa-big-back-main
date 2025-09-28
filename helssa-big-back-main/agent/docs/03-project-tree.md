# 🌳 نمودار درختی کامل پروژه HELSSA

## 📋 فهرست مطالب

- [ساختار کلی پروژه](## 🏗️ ساختار کلی پروژه)
- [شرح دقیق پوشه‌ها](## 📁 شرح دقیق پوشه‌ها)
- [نقشه‌برداری مراکز به پوشه‌ها](## 🗺️ نقشه‌برداری مراکز به پوشه‌ها)
- [فایل‌های کلیدی پروژه](## 📄 فایل‌های کلیدی پروژه)
- [ساختار پیشنهادی برای توسعه](## 🚀 ساختار پیشنهادی برای توسعه)

---

## 🏗️ ساختار کلی پروژه

```python
HELSSA/
├── 📁 unified_services/          # سرویس‌های یکپارچه و مشترک
│   ├── unified_auth/            # احراز هویت یکپارچه
│   ├── unified_billing/         # سیستم مالی یکپارچه
│   ├── unified_ai/              # هوش مصنوعی مرکزی
│   └── unified_access/          # دسترسی یکپارچه
│
├── 📁 patient_apps/             # اپلیکیشن‌های بیمار (Medogram)
│   ├── telemedicine/            # پزشکی از راه دور
│   ├── chatbot/                 # چت‌بات پزشکی
│   ├── certificate/             # گواهی‌های پزشکی
│   ├── doctor_online/           # پزشکان آنلاین
│   └── sub/                     # اشتراک‌ها
│
├── 📁 doctor_apps/              # اپلیکیشن‌های پزشک (SOAPify)
│   ├── encounters/              # ملاقات‌های پزشکی
│   ├── stt/                     # تبدیل گفتار به متن
│   ├── nlp/                     # پردازش زبان طبیعی
│   ├── outputs/                 # تولید گزارش‌ها
│   └── accounts/                # حساب‌های پزشکان
│
├── 📁 core_infrastructure/      # زیرساخت اصلی
│   ├── adminplus/               # پنل ادمین پیشرفته
│   ├── analytics/               # تحلیل‌های آماری
│   ├── billing/                 # صورتحساب (Legacy)
│   ├── infra/                   # ابزارهای زیرساختی
│   ├── uploads/                 # مدیریت فایل‌ها
│   └── worker/                  # Celery Workers
│
├── 📁 integrations/             # یکپارچه‌سازی‌ها
│   ├── clients/                 # کلاینت‌های API
│   │   ├── gpt_client.py        # OpenAI/GapGPT
│   │   ├── sms_client.py        # Kavenegar
│   │   └── payment_clients.py   # BitPay/ZarinPal
│   └── webhooks/                # Webhook handlers
│
├── 📁 project_settings/         # تنظیمات پروژه‌ها
│   ├── medogram/                # تنظیمات Medogram
│   │   ├── settings/            # Django settings
│   │   └── urls.py              # URL routing
│   └── soapify/                 # تنظیمات SOAPify
│       ├── settings/            # Django settings
│       └── urls.py              # URL routing
│
├── 📁 deployment/               # استقرار و DevOps
│   ├── docker/                  # Docker configs
│   ├── kubernetes/              # K8s manifests
│   ├── nginx/                   # Nginx configs
│   └── scripts/                 # Deployment scripts
│
├── 📁 documentation/            # مستندات
│   ├── api/                     # API docs
│   ├── architecture/            # معماری
│   ├── guides/                  # راهنماها
│   └── examples/                # نمونه کدها
│
├── 📁 tests/                    # تست‌ها
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end tests
│   └── fixtures/                # Test data
│
├── 📁 static/                   # فایل‌های استاتیک
├── 📁 media/                    # فایل‌های آپلود شده
├── 📁 templates/                # قالب‌های Django
├── 📁 locale/                   # فایل‌های ترجمه
│
├── 📄 docker-compose.yml        # Docker Compose config
├── 📄 Dockerfile                # Docker image
├── 📄 requirements.txt          # Python dependencies
├── 📄 package.json              # Frontend dependencies
├── 📄 manage.py                 # Django management
├── 📄 Makefile                  # Build automation
├── 📄 .env.example              # Environment template
└── 📄 README.md                 # Project documentation
```

## 📁 شرح دقیق پوشه‌ها

### 🔐 unified_services/ - سرویس‌های یکپارچه

#### unified_auth/ - احراز هویت یکپارچه

```python
unified_auth/
├── models.py               # UnifiedUser, UserRole, UserSession
├── serializers.py          # DRF Serializers
├── views/
│   ├── auth_views.py       # Login, Register, Logout
│   ├── otp_views.py        # OTP generation/verification
│   └── profile_views.py    # User profile management
├── services/
│   ├── jwt_service.py      # JWT token management
│   ├── otp_service.py      # OTP service (SMS)
│   └── rbac_service.py     # Role-based access control
├── middleware/
│   ├── auth_middleware.py  # Authentication middleware
│   └── cors_middleware.py  # CORS handling
└── migrations/
```

#### unified_billing/ - سیستم مالی یکپارچه

```python
unified_billing/
├── models.py               # Wallet, Transaction, Subscription
├── services/
│   ├── wallet_service.py   # Wallet operations
│   ├── payment_service.py  # Payment processing
│   └── subscription_service.py  # Subscription management
├── gateways/
│   ├── bitpay.py          # BitPay.ir integration
│   ├── zarinpal.py        # ZarinPal integration
│   └── stripe.py          # Stripe (international)
├── tasks.py               # Celery tasks for billing
└── webhooks/              # Payment gateway webhooks
```

#### unified_ai/ - هوش مصنوعی مرکزی

```python
unified_ai/
├── models.py              # AIChat, AIConfig, UsageLog
├── services/
│   ├── chatbot_service.py # Medical chatbot
│   ├── stt_service.py     # Speech-to-text
│   ├── nlp_service.py     # NLP processing
│   └── vision_service.py  # Image analysis
├── providers/
│   ├── openai_provider.py # OpenAI/GapGPT
│   ├── whisper_provider.py # Whisper STT
│   └── azure_provider.py  # Azure services
├── prompts/
│   ├── medical_prompts.py # Medical AI prompts
│   └── soap_prompts.py    # SOAP generation prompts
└── rate_limiting/         # AI usage limits
```

### 👤 patient_apps/ - اپلیکیشن‌های بیمار

#### telemedicine/ - پزشکی از راه دور

```python
telemedicine/
├── models.py              # Visit, Payment, Order
├── views/
│   ├── visit_views.py     # Visit booking/management
│   ├── payment_views.py   # Payment handling
│   └── doctor_views.py    # Doctor listings
├── services/
│   ├── booking_service.py # Visit booking logic
│   └── video_service.py   # Video call integration
└── signals.py             # Django signals
```

#### chatbot/ - چت‌بات پزشکی

```python
chatbot/
├── models.py              # ChatSession, ChatMessage
├── views.py               # Chat API endpoints
├── services/
│   ├── chat_service.py    # Chat logic
│   ├── summary_service.py # Conversation summary
│   └── share_service.py   # Share with doctor
└── consumers.py           # WebSocket consumers
```

### 👨‍⚕️ doctor_apps/ - اپلیکیشن‌های پزشک

#### encounters/ - ملاقات‌های پزشکی

```python
encounters/
├── models.py              # Encounter, AudioChunk, Transcript
├── views/
│   ├── encounter_views.py # Encounter CRUD
│   ├── audio_views.py     # Audio upload/process
│   └── transcript_views.py # Transcript management
├── services/
│   ├── audio_service.py   # Audio processing
│   └── soap_service.py    # SOAP generation
└── tasks.py               # Async processing tasks
```

#### stt/ - تبدیل گفتار به متن

```python
stt/
├── models.py              # STTJob, STTResult
├── services/
│   ├── whisper_service.py # Whisper integration
│   ├── chunk_service.py   # Audio chunking
│   └── merge_service.py   # Transcript merging
├── tasks.py               # Celery STT tasks
└── utils/                 # Audio utilities
```

### 🛠️ core_infrastructure/ - زیرساخت اصلی

#### infra/ - ابزارهای زیرساختی

```python
infra/
├── middleware/
│   ├── rate_limit.py      # Rate limiting
│   ├── hmac_auth.py       # HMAC authentication
│   └── audit_log.py       # Audit logging
├── utils/
│   ├── cache_utils.py     # Cache helpers
│   ├── storage_utils.py   # Storage helpers
│   └── crypto_utils.py    # Encryption utilities
└── monitoring/            # Monitoring tools
```

## 🗺️ نقشه‌برداری مراکز به پوشه‌ها

```python
graph LR
    subgraph "Control Centers"
        ACC[Account Center]
        AIC[AI Center]
        BIL[Billing Center]
        VIS[Visit Center]
        AXS[Access Center]
    end
    
    subgraph "Project Folders"
        UA[unified_auth/]
        UAI[unified_ai/]
        UB[unified_billing/]
        ENC[encounters/]
        UAC[unified_access/]
    end
    
    ACC --> UA
    AIC --> UAI
    BIL --> UB
    VIS --> ENC
    AXS --> UAC
```

| مرکز کنترل | پوشه‌های مرتبط | مسئولیت اصلی |
|------------|---------------|--------------|
| 🏦 Account Center | `unified_auth/`, `accounts/` | احراز هویت و مدیریت کاربران |
| 🧠 AI Center | `unified_ai/`, `nlp/`, `stt/` | سرویس‌های هوش مصنوعی |
| 💰 Billing Center | `unified_billing/`, `billing/`, `sub/` | مالی و اشتراک‌ها |
| 🏥 Visit Center | `encounters/`, `telemedicine/` | ویزیت‌ها و ملاقات‌ها |
| 🔑 Access Center | `unified_access/` | کنترل دسترسی |
| 🤖 Chatbot Center | `chatbot/`, `unified_ai/` | چت‌بات پزشکی |
| 📧 Comm Center | `infra/messaging/`, `certificate/` | ارتباطات و نوتیفیکیشن |
| ⚙️ Task Center | `worker/`, همه `tasks.py` ها | وظایف پس‌زمینه |
| 🕴️ Agent Center | `unified_ai/agents/` | ایجنت‌های هوشمند |

## 📄 فایل‌های کلیدی پروژه

### فایل‌های پیکربندی اصلی

#### docker-compose.yml

```python
version: '3.8'

services:
  # Database
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: helssa_db
    volumes:
      - mysql_data:/var/lib/mysql
    
  # Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    
  # Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    
  # Web Application
  web:
    build: .
    command: gunicorn medogram.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    depends_on:
      - mysql
      - redis
      - minio
    environment:
      - DATABASE_URL=mysql://root:${DB_PASSWORD}@mysql:3306/helssa_db
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      
  # Celery Worker
  worker:
    build: .
    command: celery -A worker.celery_app worker -l info
    volumes:
      - .:/app
    depends_on:
      - mysql
      - redis
      
  # Celery Beat
  beat:
    build: .
    command: celery -A worker.celery_app beat -l info
    volumes:
      - .:/app
    depends_on:
      - mysql
      - redis
      
  # Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./static:/static
      - ./media:/media
    depends_on:
      - web

volumes:
  mysql_data:
  minio_data:
  redis_data:
```

#### requirements.txt (مهم‌ترین‌ها)

```python
# Django Core
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.0
django-environ==0.11.2

# Database
mysqlclient==2.2.0
django-redis==5.4.0

# Authentication
djangorestframework-simplejwt==5.3.0
python-jose==3.3.0

# AI/ML
openai==1.3.0
whisper==1.1.10
langchain==0.0.340
numpy==1.24.3
pandas==2.0.3

# Storage
django-storages==1.14.2
boto3==1.29.0
minio==7.2.0

# Async Tasks
celery==5.3.4
redis==5.0.1
flower==2.0.1

# Payment
stripe==7.1.0
requests==2.31.0

# Utils
python-decouple==3.8
Pillow==10.1.0
python-magic==0.4.27
```

## 🚀 ساختار پیشنهادی برای توسعه

### اضافه کردن مرکز جدید

```python
new_center/
├── __init__.py
├── apps.py                # Django app config
├── models.py              # Data models
├── serializers.py         # API serializers
├── views/                 # API views
│   ├── __init__.py
│   └── main_views.py
├── services/              # Business logic
│   ├── __init__.py
│   └── core_service.py
├── tasks.py               # Celery tasks
├── urls.py                # URL routing
├── middleware/            # Custom middleware
├── utils/                 # Utilities
├── tests/                 # Tests
└── migrations/            # DB migrations
```

### قوانین نام‌گذاری

- **Models**: PascalCase (e.g., `UserProfile`)
- **Functions**: snake_case (e.g., `get_user_profile`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_FILE_SIZE`)
- **URLs**: kebab-case (e.g., `/api/user-profile/`)

### بهترین شیوه‌ها

1. **هر مرکز = یک Django App**
2. **Business Logic در services/**
3. **API Views نازک، Services چاق**
4. **تست برای هر سرویس**
5. **مستندسازی در کد**

---

[ELEMENT: div align="center"]

[→ قبلی: معماری متمرکز](02-centralized-architecture.md) | [بعدی: تکنولوژی و وابستگی‌ها ←](04-technology-stack.md)

</div>
