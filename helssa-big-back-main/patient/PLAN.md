# PLAN: اپلیکیشن مدیریت بیماران (Patient App)

## نمای کلی پروژه

### هدف اصلی
ایجاد سیستم جامع مدیریت بیماران که شامل مدیریت پروفایل‌ها، سوابق پزشکی، نسخه‌ها و رضایت‌نامه‌های پزشکی است.

### نوع اپلیکیشن
Backend Django App با API های RESTful

### هسته‌های فعال
- ✅ **API Ingress Core**: مدیریت درخواست‌ها و پاسخ‌ها
- ✅ **Text Processing Core**: پردازش متن‌های پزشکی  
- ✅ **Speech Processing Core**: رونویسی فایل‌های صوتی
- ✅ **Orchestration Core**: هماهنگی workflow ها

### اولویت: بالا
دلیل: زیرساخت اصلی برای تمام سایر اپلیکیشن‌ها

## تحلیل نیازمندی‌ها

### کاربران هدف
1. **بیماران**: مدیریت اطلاعات شخصی و دریافت خدمات
2. **پزشکان**: دسترسی به اطلاعات بیماران و ثبت سوابق
3. **ادمین‌ها**: مدیریت کلی سیستم

### ویژگی‌های کلیدی

#### 1. مدیریت پروفایل بیماران
- ثبت اطلاعات هویتی (نام، کد ملی، تاریخ تولد)
- اطلاعات تماس و آدرس
- اطلاعات پزشکی پایه (قد، وزن، گروه خونی)
- تولید خودکار شماره پرونده
- محاسبه خودکار سن و BMI
- اعتبارسنجی کد ملی

#### 2. مدیریت سوابق پزشکی  
- ثبت انواع سوابق (آلرژی، دارو، جراحی، بیماری)
- سطح‌بندی شدت
- تاریخ شروع و پایان
- وضعیت در حال ادامه
- پردازش هوشمند متن

#### 3. مدیریت نسخه‌ها
- ایجاد نسخه‌های دیجیتال
- اطلاعات دارو (نام، دوز، دفعات)
- پزشک تجویزکننده
- وضعیت نسخه (فعال، منقضی، لغو شده)
- امکان تکرار نسخه
- تولید شماره منحصر به فرد

#### 4. مدیریت رضایت‌نامه‌ها
- ایجاد انواع رضایت‌نامه
- امضای دیجیتال ایمن
- پیگیری وضعیت
- تاریخ انقضا
- حسابرسی و logging

#### 5. پردازش گفتار و متن
- رونویسی فایل‌های صوتی
- پردازش متن‌های پزشکی
- استخراج موجودیت‌ها
- تحلیل و خلاصه‌سازی

## معماری فنی

### مدل‌های داده

#### PatientProfile
```python
- id: UUIDField (Primary Key)
- user: ForeignKey(User)
- national_code: CharField(10, unique=True)
- first_name, last_name: CharField
- birth_date: DateField
- gender: CharField(choices)
- height, weight: FloatField
- blood_group: CharField
- emergency_contact_*: TextField
- address, city, province: TextField
- medical_record_number: CharField(unique)
- is_active: BooleanField
- metadata: JSONField
- created_at, updated_at: DateTimeField
```

#### MedicalRecord
```python
- id: UUIDField (Primary Key)
- patient: ForeignKey(PatientProfile)
- record_type: CharField(choices)
- title: CharField
- description: TextField
- severity: CharField(choices)
- start_date: DateField
- end_date: DateField (nullable)
- is_ongoing: BooleanField
- doctor: ForeignKey(User, nullable)
- metadata: JSONField
- created_at, updated_at: DateTimeField
```

#### PrescriptionHistory
```python
- id: UUIDField (Primary Key)
- patient: ForeignKey(PatientProfile)
- prescribed_by: ForeignKey(User)
- prescription_number: CharField(unique)
- medication_name: CharField
- dosage: CharField
- frequency: CharField
- duration: CharField
- diagnosis: TextField
- start_date, end_date: DateField
- status: CharField(choices)
- is_repeat_allowed: BooleanField
- max_repeats: IntegerField
- repeat_count: IntegerField
- metadata: JSONField
- created_at, updated_at: DateTimeField
```

#### MedicalConsent
```python
- id: UUIDField (Primary Key)
- patient: ForeignKey(PatientProfile)
- consent_type: CharField(choices)
- title: CharField
- description: TextField
- consent_text: TextField
- status: CharField(choices)
- consent_date: DateTimeField (nullable)
- expiry_date: DateField (nullable)
- digital_signature: TextField (nullable)
- ip_address: GenericIPAddressField (nullable)
- user_agent: TextField (nullable)
- metadata: JSONField
- created_at, updated_at: DateTimeField
```

### API Endpoints

#### پروفایل بیماران
```
POST   /api/patient/profile/create/           # ایجاد پروفایل [PatientOnly]
GET    /api/patient/profile/{id}/              # دریافت پروفایل [PatientOrDoctor]  
PUT    /api/patient/profile/{id}/update/       # بروزرسانی [PatientOrDoctor]
GET    /api/patient/profile/{id}/statistics/   # آمار [PatientOrDoctor]
POST   /api/patient/search/                    # جستجو [DoctorOnly]
```

#### سوابق پزشکی
```
POST   /api/patient/medical-records/           # ایجاد [DoctorOnly]
GET    /api/patient/{id}/medical-records/      # دریافت [MedicalRecordPermission]
```

#### نسخه‌ها
```
POST   /api/patient/prescriptions/             # ایجاد [DoctorOnly]
GET    /api/patient/{id}/prescriptions/        # دریافت [PrescriptionPermission]
POST   /api/patient/prescriptions/{id}/repeat/ # تکرار [DoctorOnly]
```

#### رضایت‌نامه‌ها
```
POST   /api/patient/consents/                  # ایجاد [DoctorOnly]
POST   /api/patient/consents/{id}/grant/       # ثبت رضایت [PatientOnly]
```

#### پردازش صوت
```
POST   /api/patient/transcribe/                # رونویسی [DoctorOnly]
```

### سیستم مجوزها

#### Permission Classes
- `PatientOnlyPermission`: دسترسی فقط بیماران
- `DoctorOnlyPermission`: دسترسی فقط پزشکان  
- `PatientOrDoctorPermission`: دسترسی بیمار یا پزشک
- `MedicalRecordPermission`: مجوز ویژه سوابق
- `PrescriptionPermission`: مجوز ویژه نسخه‌ها
- `ConsentPermission`: مجوز ویژه رضایت‌نامه‌ها

#### Object Level Permissions
- بیماران فقط اطلاعات خود را می‌بینند
- پزشکان به بیماران تحت نظر دسترسی دارند
- دسترسی از طریق `unified_access.AccessControlService`

## یکپارچه‌سازی‌ها

### unified_auth
- استفاده از `UnifiedUser` model
- JWT authentication
- تفکیک نقش‌های patient/doctor

### unified_billing  
- بررسی محدودیت اشتراک
- ثبت استفاده از منابع
- Rate limiting based on subscription

### unified_access
- دسترسی موقت پزشک به بیمار
- کدهای دسترسی OTP
- Session management

### Kavenegar SMS
- ارسال کدهای تأیید
- اطلاع‌رسانی‌های پزشکی
- Rate limiting: 1/دقیقه، 5/ساعت

## امنیت

### احراز هویت
- JWT tokens با expiry کوتاه
- Refresh token rotation
- Token blacklisting

### مجوزها
- Permission classes سفارشی
- Object-level permissions  
- Access control با unified_access

### حفاظت از داده‌ها
- رمزنگاری اطلاعات حساس
- Masking در logs
- Input validation جامع
- SQL injection prevention

### Rate Limiting
- محدودیت درخواست بر endpoint
- محدودیت OTP
- محدودیت AI requests

## عملکرد و Cache

### Cache Strategy
- Patient profiles: 15 minutes
- Medical records: 10 minutes  
- Prescriptions: 5 minutes
- User permissions: 5 minutes

### Database Optimization
- Indexes on national_code, medical_record_number
- Indexes on patient, doctor foreign keys
- Indexes on created_at for time-based queries

## مراحل پیاده‌سازی

### Phase 1: Core Models ✅
- [x] PatientProfile model
- [x] MedicalRecord model  
- [x] PrescriptionHistory model
- [x] MedicalConsent model
- [x] Migrations

### Phase 2: API Infrastructure ✅
- [x] Serializers with validation
- [x] Permission system
- [x] Views with error handling
- [x] URL routing

### Phase 3: Core Architecture ✅
- [x] API Ingress Core
- [x] Text Processing Core
- [x] Speech Processing Core
- [x] Orchestration Core

### Phase 4: Services ✅
- [x] PatientService
- [x] MedicalRecordService
- [x] PrescriptionService  
- [x] ConsentService

### Phase 5: Testing 🚧
- [x] Model tests (basic)
- [ ] View tests
- [ ] Serializer tests
- [ ] Service tests
- [ ] Integration tests

### Phase 6: Documentation ✅
- [x] README.md
- [x] API documentation
- [ ] PLAN.md
- [ ] CHECKLIST.json

### Phase 7: Integration 🚧
- [x] Settings configuration
- [x] URL integration
- [ ] unified_auth integration
- [ ] unified_billing integration
- [ ] unified_access integration

## تست‌ها

### Unit Tests
- Model validation tests
- Service method tests
- Permission tests
- Serializer validation tests

### Integration Tests  
- API endpoint tests
- Authentication flow tests
- Permission integration tests
- Workflow tests

### Performance Tests
- Load testing for endpoints
- Database query optimization
- Cache effectiveness tests

## مستندات

### API Documentation
- OpenAPI/Swagger specs
- Request/response examples
- Error code documentation
- Authentication examples

### Developer Documentation
- Setup instructions
- Configuration guide
- Architecture overview
- Extension guidelines

## Monitoring و Logging

### Structured Logging
- Request/response logging
- Performance metrics
- Error tracking
- Security events

### Health Checks
- Database connectivity
- External service status
- Cache availability
- Permission service status

## مخاطرات و کاهش ریسک

### ریسک‌های فنی
- **دیتابیس**: Regular backups, replication
- **API Performance**: Caching, rate limiting
- **External Dependencies**: Circuit breakers, fallbacks

### ریسک‌های امنیتی  
- **Data Breach**: Encryption, access logs
- **Permission Bypass**: Thorough testing, reviews
- **DDoS**: Rate limiting, monitoring

### ریسک‌های Business
- **User Adoption**: Good UX, documentation
- **Compliance**: Security audits, policy compliance
- **Scalability**: Performance monitoring, optimization

## نتایج مورد انتظار

### Deliverables
1. ✅ Django app با architecture کامل
2. ✅ RESTful API های امن
3. ✅ Permission system جامع
4. 🚧 Test suite کامل
5. ✅ Documentation جامع

### Success Metrics
- API response time < 200ms
- 99.9% uptime
- Zero security incidents
- Code coverage > 80%
- User satisfaction > 90%

---

**وضعیت**: 85% تکمیل شده  
**آخرین بروزرسانی**: 2024-12-28  
**نسخه**: 1.0.0