# 🎤 Simple Voice Chat Application

یک برنامه ساده برای ضبط صدا، تبدیل به متن با Whisper و چت با هوش مصنوعی.

## ✨ ویژگی‌ها

- 🎙️ ضبط صدا از مرورگر
- 🔄 تبدیل صوت به متن با OpenAI Whisper
- 🤖 چت با هوش مصنوعی (GPT-3.5-turbo)
- 📱 رابط کاربری React ساده و زیبا
- 🐳 راه‌اندازی آسان با Docker
- 🌐 پشتیبانی از زبان فارسی

## 🚀 راه‌اندازی سریع

### پیش‌نیازها

- Docker و Docker Compose
- کلید API OpenAI

### نصب و اجرا

1. کلون کردن پروژه:
```bash
git clone <repository-url>
cd simple-voice-chat
```

2. تنظیم متغیرهای محیطی:
```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کنید و کلید API خود را وارد کنید:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

3. اجرا با Docker:
```bash
docker-compose up --build
```

4. دسترسی به برنامه:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## 🛠️ معماری

### Backend (Flask)
- **Port:** 8000
- **Endpoints:**
  - `GET /health` - بررسی سلامت سرویس
  - `POST /api/speech-to-text` - تبدیل صوت به متن
  - `POST /api/chat` - چت با هوش مصنوعی
  - `POST /api/chat/clear` - پاک کردن تاریخچه چت

### Frontend (React)
- **Port:** 3000
- **Features:**
  - ضبط صدا از مرورگر
  - نمایش تاریخچه چت
  - رابط کاربری فارسی و زیبا

## 📝 نحوه استفاده

1. روی دکمه "شروع ضبط" کلیک کنید
2. صحبت کنید
3. روی "توقف ضبط" کلیک کنید
4. متن به طور خودکار تبدیل شده و به چت ارسال می‌شود
5. پاسخ هوش مصنوعی را دریافت کنید

همچنین می‌توانید مستقیماً متن تایپ کنید و ارسال کنید.

## ⚙️ تنظیمات

### متغیرهای محیطی

| متغیر | توضیحات | پیش‌فرض |
|-------|---------|---------|
| `OPENAI_API_KEY` | کلید API OpenAI | ضروری |
| `CHAT_API_URL` | URL API چت | `https://api.openai.com/v1/chat/completions` |
| `REACT_APP_API_URL` | URL Backend | `http://localhost:8000` |

### تنظیم برای production

برای استفاده در محیط تولید:

1. تغییر URL های API در فایل `.env`
2. تنظیم HTTPS
3. اضافه کردن authentication و rate limiting

## 🔧 توسعه

### اجرا بدون Docker

#### Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### Frontend:
```bash
cd frontend
npm install
npm start
```

## 📋 API Documentation

### POST /api/speech-to-text
**Request:**
- `audio`: فایل صوتی (multipart/form-data)

**Response:**
```json
{
  "text": "متن تبدیل شده",
  "status": "success"
}
```

### POST /api/chat
**Request:**
```json
{
  "message": "پیام کاربر",
  "session_id": "شناسه جلسه (اختیاری)"
}
```

**Response:**
```json
{
  "response": "پاسخ هوش مصنوعی",
  "session_id": "شناسه جلسه",
  "status": "success"
}
```

## 🐛 رفع مشکل

### مشکلات رایج:

1. **خطای دسترسی به میکروفون:** اطمینان حاصل کنید که از HTTPS استفاده می‌کنید
2. **خطای API Key:** بررسی کنید که کلید OpenAI معتبر باشد
3. **مشکل CORS:** Backend به طور پیش‌فرض CORS را فعال کرده

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.