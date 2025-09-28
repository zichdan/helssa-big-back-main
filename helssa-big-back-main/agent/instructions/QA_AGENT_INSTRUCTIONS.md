# ایجنت QA نهایی - دستورالعمل بررسی یکپارچگی

## مأموریت QA Agent

ایجنت QA مسئول بررسی نهایی تمام اپلیکیشن‌های ساخته شده توسط ایجنت‌های فرعی است تا اطمینان حاصل شود که:

1. **یکنواختی کامل** در تمام اپ‌ها رعایت شده
2. **سیاست‌های امنیتی** بدون استثناء اجرا شده‌اند
3. **معماری چهار هسته‌ای** صحیح پیاده‌سازی شده
4. **تفکیک نقش‌های patient/doctor** در همه جا رعایت شده
5. **OTP/Kavenegar** طبق استانداردها پیکربندی شده
6. **مستندسازی** کامل و دقیق است

## چک‌لیست بررسی جامع

### 1. بررسی ساختار کلی

#### ✅ ساختار پوشه‌ها

- [ ] همه اپ‌ها دارای ساختار یکسان هستند
- [ ] فایل‌های الزامی موجود: PLAN.md, CHECKLIST.json, PROGRESS.json, LOG.md, README.md
- [ ] پوشه charts/ با progress_doughnut.svg موجود است
- [ ] پوشه app_code/ با ساختار صحیح موجود است
- [ ] پوشه deployment/ با فایل‌های پیکربندی موجود است

#### ✅ مستندسازی

- [ ] تمام فایل‌های README کامل و یکنواخت هستند
- [ ] API documentation در همه اپ‌ها موجود است
- [ ] نمونه requests/responses صحیح هستند
- [ ] راهنمای نصب و راه‌اندازی دقیق است

### 2. بررسی معماری

#### ✅ چهار هسته‌ای

- [ ] تمام اپ‌ها دارای پوشه cores/ هستند
- [ ] فایل‌های api_ingress.py, orchestrator.py در همه موجود
- [ ] text_processor.py در اپ‌های مرتبط موجود است
- [ ] speech_processor.py در اپ‌های مرتبط موجود است
- [ ] هسته‌ها مطابق الگوی CORE_ARCHITECTURE.md هستند

#### ✅ مدل‌های داده

- [ ] همه مدل‌ها از StandardModel ارث‌بری می‌کنند
- [ ] فیلدهای created_at, updated_at, created_by موجود
- [ ] روابط با UnifiedUser صحیح تعریف شده
- [ ] Migration فایل‌ها ایجاد شده‌اند

### 3. بررسی امنیت

#### ✅ احراز هویت یکپارچه

- [ ] همه اپ‌ها از unified_auth.UnifiedUser استفاده می‌کنند
- [ ] JWT authentication در همه views موجود است
- [ ] Permission classes صحیح تعریف شده
- [ ] کوکی و session security headers تنظیم شده

#### ✅ سیاست‌های OTP

- [ ] Kavenegar integration در اپ‌های مرتبط موجود
- [ ] Rate limiting مطابق سیاست‌ها (1/دقیقه، 5/ساعت)
- [ ] OTP expiry 3 دقیقه است
- [ ] حداکثر 3 تلاش مجاز

#### ✅ تفکیک نقش‌ها

- [ ] PatientOnlyPermission در endpoints مربوطه
- [ ] DoctorOnlyPermission در endpoints مربوطه  
- [ ] user_type checks در business logic
- [ ] Dashboard جداگانه برای پزشکان

### 4. بررسی یکپارچه‌سازی‌ها

#### ✅ Unified Auth

- [ ] imports صحیح از unified_auth
- [ ] User model reference به UnifiedUser
- [ ] JWT configuration درست
- [ ] Permission classes custom پیاده‌سازی شده

#### ✅ Unified Billing

- [ ] Check subscription limits پیاده‌سازی شده
- [ ] Usage logging برای منابع
- [ ] Payment gateway integration مستند شده
- [ ] Wallet integration (در صورت نیاز)

#### ✅ Unified Access

- [ ] Temporary access برای پزشکان
- [ ] Access code generation
- [ ] Session management
- [ ] Audit logging

#### ✅ Unified AI

- [ ] AI service integration در اپ‌های مرتبط
- [ ] Error handling برای AI failures
- [ ] Rate limiting برای AI requests
- [ ] Context management

### 5. بررسی API ها

#### ✅ Endpoint Consistency

- [ ] URL patterns یکنواخت (/api/[ELEMENT:app_name]/[ELEMENT:resource_name]/)
- [ ] HTTP methods مناسب (GET/POST/PUT/DELETE)
- [ ] Response format یکسان
- [ ] Error handling استاندارد

#### ✅ Serializers

- [ ] Input validation کامل
- [ ] Output serialization مناسب
- [ ] Custom field handling
- [ ] Nested serializers درست

#### ✅ Views

- [ ] الگوی standard_endpoint رعایت شده
- [ ] Exception handling جامع
- [ ] Logging مناسب
- [ ] Response codes صحیح

### 6. بررسی تست‌ها

#### ✅ تست‌های واحد

- [ ] test_models.py برای تمام models
- [ ] test_views.py برای تمام endpoints
- [ ] test_serializers.py برای validation
- [ ] test_cores.py برای business logic

#### ✅ تست‌های تلفیقی

- [ ] API integration tests
- [ ] Database integrity tests
- [ ] External service mocking
- [ ] Authentication flow tests

#### ✅ تست‌های E2E

- [ ] Complete user journeys
- [ ] Patient workflows
- [ ] Doctor workflows
- [ ] Cross-app interactions

### 7. بررسی عملکرد

#### ✅ Optimization

- [ ] Database query optimization
- [ ] Caching strategies implemented
- [ ] Rate limiting configured
- [ ] File upload restrictions

#### ✅ Monitoring

- [ ] Health check endpoints
- [ ] Logging configuration
- [ ] Metrics collection
- [ ] Error tracking

### 8. بررسی مستندسازی

#### ✅ Technical Documentation

- [ ] README files complete
- [ ] API specifications accurate
- [ ] Installation guides clear
- [ ] Configuration examples correct

#### ✅ User Documentation

- [ ] Patient user guides
- [ ] Doctor user guides
- [ ] Admin documentation
- [ ] Troubleshooting guides

## فرآیند بررسی

### مرحله 1: بررسی خودکار

```bash
# Script برای بررسی خودکار
python3 qa_automated_check.py
```

### مرحله 2: بررسی دستی

- مطالعه تمام مستندات
- بررسی کد key files
- تست manual API calls
- بررسی database migrations

### مرحله 3: تست یکپارچگی

- راه‌اندازی test environment
- اجرای integration tests
- تست real API calls
- بررسی logging و monitoring

### مرحله 4: گزارش نهایی

- تهیه FINAL_CHECKLIST.json
- نوشتن FINAL_REPORT.md
- ایجاد overall progress chart
- مستندسازی یافته‌ها

## خروجی‌های QA Agent

### 1. FINAL_CHECKLIST.json

```json
{
  "overall_status": "PASSED/FAILED",
  "total_apps": 8,
  "passed_apps": 8,
  "failed_apps": 0,
  "apps": {
    "patient_chatbot": {
      "status": "PASSED",
      "score": 95,
      "issues": []
    }
  },
  "critical_issues": [],
  "recommendations": []
}
```

### 2. FINAL_REPORT.md

- خلاصه اجرایی
- وضعیت هر اپ
- مسائل یافت شده
- پیشنهادات بهبود
- آمادگی برای انتشار

### 3. charts/overall_progress.svg

نمودار کلی پیشرفت تمام اپ‌ها

### 4. INTEGRATION_GUIDE.md

راهنمای ادغام در helssa-big_back

## معیارهای پذیرش

### ✅ Mandatory Criteria (باید 100% باشد)

- Security policies compliance
- Unified auth integration
- Core architecture adherence
- OTP/Kavenegar configuration

### ✅ Quality Criteria (باید >90% باشد)

- Documentation completeness
- Test coverage
- API consistency
- Error handling

### ✅ Performance Criteria (باید >80% باشد)

- Response time optimization
- Database query efficiency
- Caching implementation
- Resource usage

## اقدامات در صورت Failure

### Critical Issues

- **متوقف کردن فرآیند**: اگر security policy نقض شده
- **برگشت به ایجنت**: اگر architecture غلط است
- **Escalation**: اگر مسئله‌ای حل نشده

### Minor Issues

- **Documentation**: ثبت در گزارش نهایی
- **Future improvements**: اضافه به backlog
- **Workarounds**: ارائه راه‌حل موقت

## Timeline QA Process

### روز 1: Setup و بررسی خودکار

- راه‌اندازی QA environment
- اجرای automated checks
- تهیه لیست اولیه مسائل

### روز 2-3: بررسی دستی

- Review تمام apps
- تست API calls
- بررسی documentation

### روز 4: Integration testing

- تست یکپارچگی
- بررسی dependencies
- Performance testing

### روز 5: گزارش نهایی

- تهیه گزارش جامع
- ایجاد charts
- آماده‌سازی برای انتقال

## ابزارهای QA

### Automated Tools

- Code quality checkers
- Security scanners
- Documentation validators
- API testing tools

### Manual Tools

- Code review checklists
- Test case templates
- Documentation guidelines
- Performance benchmarks

---

**نکته مهم**: QA Agent نقش gate-keeper دارد. هیچ اپی نباید بدون تأیید QA به مرحله production برسد.

**معیار موفقیت**: تمام اپ‌ها باید از QA با score حداقل 85 و بدون critical issue عبور کنند.
