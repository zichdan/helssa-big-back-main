# 🚀 راهنمای شروع سریع HELSSA

## 📋 فهرست مطالب

- [نصب سریع با Docker](## 🐳 نصب سریع با Docker)
- [نصب محلی برای توسعه](## 💻 نصب محلی برای توسعه)
- [اولین گام‌ها](## 🎯 اولین گام‌ها)
- [تست عملکرد](## 🧪 تست عملکرد)
- [استفاده از API](## 🔌 استفاده از API)
- [توسعه Frontend](## ⚛️ توسعه Frontend)
- [نکات مهم](## ⚡ نکات مهم)
- [منابع مفید](## 📚 منابع مفید)

---

## 🐳 نصب سریع با Docker

### پیش‌نیازها

- Docker نسخه 20.10+
- Docker Compose نسخه 1.29+
- Git
- 4GB RAM حداقل
- 10GB فضای دیسک

### مراحل نصب (5 دقیقه)

#### 1️⃣ کلون کردن پروژه

```bash
# کلون کردن ریپازیتوری
git clone https://github.com/helssa/platform.git helssa
cd helssa

# یا دانلود مستقیم
wget https://github.com/helssa/platform/archive/main.zip
unzip main.zip
cd helssa-platform-main
```

#### 2️⃣ تنظیم Environment

```bash
# کپی فایل نمونه
cp .env.example .env

# ویرایش تنظیمات ضروری
nano .env

# حداقل تنظیمات مورد نیاز:
DJANGO_SECRET_KEY=your-secret-key-here
DB_PASSWORD=strong-password
REDIS_PASSWORD=redis-password
MINIO_ACCESS_KEY=minio-access
MINIO_SECRET_KEY=minio-secret
```

#### 3️⃣ راه‌اندازی با Docker Compose

```bash
# Build و راه‌اندازی تمام سرویس‌ها
docker-compose up -d

# مشاهده وضعیت
docker-compose ps

# مشاهده لاگ‌ها
docker-compose logs -f
```

#### 4️⃣ اجرای Migration و Setup اولیه

```bash
# اجرای migrations
docker-compose exec web python manage.py migrate

# ایجاد superuser
docker-compose exec web python manage.py createsuperuser

# جمع‌آوری فایل‌های استاتیک
docker-compose exec web python manage.py collectstatic --noinput

# بارگذاری داده‌های نمونه (اختیاری)
docker-compose exec web python manage.py loaddata initial_data
```

#### 5️⃣ دسترسی به سیستم

```bash
# URLs:
- Web Interface: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001
- Grafana: http://localhost:3000
```

## 💻 نصب محلی برای توسعه

### Backend Setup

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 7+
- MinIO (یا S3 compatible)

#### 1️⃣ ایجاد Virtual Environment

```bash
# ایجاد venv
python3 -m venv venv

# فعال‌سازی (Linux/Mac)
source venv/bin/activate

# فعال‌سازی (Windows)
venv\Scripts\activate
```

#### 2️⃣ نصب Dependencies

```bash
# به‌روزرسانی pip
pip install --upgrade pip

# نصب requirements
pip install -r requirements.txt

# نصب development dependencies
pip install -r requirements-dev.txt
```

#### 3️⃣ تنظیم Database

```bash
# ایجاد دیتابیس MySQL
mysql -u root -p

CREATE DATABASE helssa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'helssa_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON helssa_db.* TO 'helssa_user'@'localhost';
FLUSH PRIVILEGES;
exit;
```

#### 4️⃣ تنظیم Redis

```bash
# نصب Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# شروع Redis
sudo systemctl start redis-server

# تست اتصال
redis-cli ping
# باید PONG برگردد
```

#### 5️⃣ تنظیم MinIO

```bash
# دانلود MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio

# اجرای MinIO
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin
./minio server ./data --console-address ":9001"
```

#### 6️⃣ Migration و راه‌اندازی

```bash
# تنظیم environment variables
export DJANGO_SETTINGS_MODULE=helssa.settings.development

# اجرای migrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# جمع‌آوری static files
python manage.py collectstatic

# اجرای development server
python manage.py runserver
```

### Frontend Setup

#### 1️⃣ نصب Dependencies

```bash
# رفتن به دایرکتوری frontend
cd frontend

# نصب packages
npm install
# یا
yarn install
```

#### 2️⃣  Environment

```javascript
// frontend/.env.local
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
```

#### 3️⃣ اجرای Development Server

```bash
# شروع development server
npm start
# یا
yarn start

# Build برای production
npm run build
# یا
yarn build
```

## 🎯 اولین گام‌ها

### 1. ورود به پنل مدیریت

```bash
# URL: http://localhost:8000/admin
# Username: superuser که ایجاد کردید
# Password: رمز عبور تعیین شده
```

### 2. ایجاد کاربر تست

```python
# Django shell
docker-compose exec web python manage.py shell

from unified_auth.models import UnifiedUser

# ایجاد بیمار
patient = UnifiedUser.objects.create_user(
    phone_number='+989121234567',
    first_name='علی',
    last_name='محمدی',
    role='patient'
)

# ایجاد پزشک
doctor = UnifiedUser.objects.create_user(
    phone_number='+989123456789',
    first_name='دکتر سارا',
    last_name='احمدی',
    role='doctor',
    specialty='general_practitioner'
)

print("Users created successfully!")
```

### 3. تست SMS با کاوه‌نگار

```python
# تست ارسال SMS
from unified_auth.services import SMSService

sms = SMSService()
result = sms.send_otp('+989121234567', '123456')
print(f"SMS sent: {result}")
```

### 4. تست AI Service

```python
# تست سرویس AI
from unified_ai.services import AIService

ai = AIService()
response = ai.chat_completion(
    messages=[
        {"role": "user", "content": "سلام، درد سر دارم"}
    ]
)
print(response)
```

## 🧪 تست عملکرد

### Health Check

```bash
# بررسی سلامت سیستم
curl http://localhost:8000/health/

# Response مورد انتظار:
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "minio": "connected"
  }
}
```

### تست‌های اتوماتیک

```bash
# اجرای تمام تست‌ها
docker-compose exec web python manage.py test

# تست یک app خاص
docker-compose exec web python manage.py test unified_auth

# تست با coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Performance Testing

```bash
# نصب locust
pip install locust

# ایجاد فایل تست
cat > locustfile.py << EOF
from locust import HttpUser, task, between

class HelssaUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health/")
    
    @task(3)
    def api_doctors(self):
        self.client.get("/api/v1/doctors/")
    
    @task(2)
    def api_login(self):
        self.client.post("/api/v1/auth/login/otp/", json={
            "phone_number": "+989121234567"
        })
EOF

# اجرای load test
locust -f locustfile.py --host=http://localhost:8000
# باز کردن http://localhost:8089
```

## 🔌 استفاده از API

### احراز هویت

```bash
# 1. درخواست OTP
curl -X POST http://localhost:8000/api/v1/auth/login/otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+989121234567"
  }'

# 2. تایید OTP
curl -X POST http://localhost:8000/api/v1/auth/verify/otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+989121234567",
    "otp_code": "123456"
  }'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "phone_number": "+989121234567",
    "role": "patient"
  }
}
```

### استفاده از Token

```bash
# ذخیره token
export TOKEN="your-access-token"

# استفاده در درخواست‌ها
curl -X GET http://localhost:8000/api/v1/patients/profile/ \
  -H "Authorization: Bearer $TOKEN"
```

### Python Client

```python
import requests

class HelssaClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.token = None
        
    def login(self, phone_number, otp_code):
        """ورود به سیستم"""
        response = requests.post(
            f'{self.base_url}/api/v1/auth/verify/otp/',
            json={
                'phone_number': phone_number,
                'otp_code': otp_code
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data['access']
            return data
        return None
        
    def get_profile(self):
        """دریافت پروفایل"""
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f'{self.base_url}/api/v1/patients/profile/',
            headers=headers
        )
        return response.json()

# استفاده
client = HelssaClient()
client.login('+989121234567', '123456')
profile = client.get_profile()
print(profile)
```

## ⚛️ توسعه Frontend

### ساختار پروژه React

```PYTHON
frontend/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/       # کامپوننت‌های قابل استفاده مجدد
│   ├── pages/           # صفحات اصلی
│   ├── services/        # API services
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # توابع کمکی
│   ├── styles/          # استایل‌های global
│   ├── App.js
│   └── index.js
├── package.json
└── .env.local
```

### نمونه Component

```jsx
// src/components/LoginForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

const LoginForm = () => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone');
  const { login, sendOtp } = useAuth();

  const handleSendOtp = async (e) => {
    e.preventDefault();
    const result = await sendOtp(phoneNumber);
    if (result.success) {
      setStep('otp');
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    const result = await login(phoneNumber, otp);
    if (result.success) {
      window.location.href = '/dashboard';
    }
  };

  return (
    <div className="login-form">
      {step === 'phone' ? (
        <form onSubmit={handleSendOtp}>
          <input
            type="tel"
            placeholder="شماره موبایل"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            pattern="^(\+98|0)?9\d{9}$"
            required
          />
          <button type="submit">ارسال کد</button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp}>
          <input
            type="text"
            placeholder="کد تایید"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            pattern="\d{6}"
            required
          />
          <button type="submit">ورود</button>
        </form>
      )}
    </div>
  );
};

export default LoginForm;
```

### API Service

```javascript
// src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ایجاد axios instance
const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor برای افزودن token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor برای مدیریت خطاها
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await api.post('/auth/refresh/', {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access);
          // Retry original request
          return api(error.config);
        } catch {
          // Refresh failed, redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

## ⚡ نکات مهم

### 1. بهینه‌سازی Performance

```python
# settings/production.py

# فعال‌سازی Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# استفاده از Cache در Views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def doctor_list(request):
    doctors = Doctor.objects.select_related('user').all()
    return render(request, 'doctors/list.html', {'doctors': doctors})
```

### 2. امنیت

```python
# همیشه در production
DEBUG = False
ALLOWED_HOSTS = ['helssa.ir', 'www.helssa.ir']

# HTTPS اجباری
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 3. Logging مناسب

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/helssa/app.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'helssa': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 4. مدیریت خطاها

```python
# utils/error_handler.py
import logging
from django.http import JsonResponse

logger = logging.getLogger('helssa')

def handle_api_error(func):
    """Decorator برای مدیریت خطاهای API"""
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return JsonResponse({
                'error': 'VALIDATION_ERROR',
                'message': str(e),
                'details': e.message_dict if hasattr(e, 'message_dict') else {}
            }, status=400)
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {e}")
            return JsonResponse({
                'error': 'PERMISSION_DENIED',
                'message': 'شما دسترسی به این بخش ندارید'
            }, status=403)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return JsonResponse({
                'error': 'INTERNAL_ERROR',
                'message': 'خطایی رخ داده است'
            }, status=500)
    return wrapper
```

## 📚 منابع مفید

### مستندات رسمی

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)

### ابزارهای توسعه

- **Postman**: تست API
- **DBeaver**: مدیریت دیتابیس
- **Redis Desktop Manager**: مشاهده Redis
- **VS Code Extensions**:
  - Python
  - Django
  - ESLint
  - Prettier

### دستورات مفید

```bash
# Docker
docker-compose logs -f web          # لاگ‌های web service
docker-compose exec web bash        # ورود به shell کانتینر
docker-compose restart web          # ری‌استارت سرویس
docker system prune -a              # پاکسازی Docker

# Django
python manage.py showmigrations     # نمایش migrations
python manage.py shell_plus         # Django shell پیشرفته
python manage.py dbshell           # MySQL shell
python manage.py check --deploy     # بررسی production

# Git
git status                         # وضعیت تغییرات
git add .                          # افزودن تغییرات
git commit -m "message"            # کامیت
git push origin main               # پوش به ریموت
```

### Troubleshooting سریع

```bash
# مشکل: Container ها بالا نمی‌آیند
docker-compose down
docker-compose up -d --build

# مشکل: Permission denied
sudo chown -R $USER:$USER .

# مشکل: Port already in use
sudo lsof -i :8000
sudo kill -9 <PID>

# مشکل: Database connection refused
docker-compose restart mysql
docker-compose exec mysql mysql -u root -p

# مشکل: Static files not found
docker-compose exec web python manage.py collectstatic --noinput
```

---

[ELEMENT: div align="center"]

🎉 **تبریک! شما با موفقیت HELSSA را نصب کردید**

برای سوالات و مشکلات به [GitHub Issues](https://github.com/helssa/platform/issues) مراجعه کنید

[→ قبلی: راهنمای Deployment](16-deployment-guide.md) | [بعدی: نمونه‌های کد ←](18-examples.md)

</div>
