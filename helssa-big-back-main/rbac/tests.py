"""
تست‌های اپلیکیشن RBAC
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    PatientProfile, DoctorProfile, Role, Permission,
    UserRole, UserSession, AuthAuditLog
)

User = get_user_model()


class UnifiedUserModelTest(TestCase):
    """تست‌های مدل کاربر یکپارچه"""
    
    def setUp(self):
        """
        یک‌خطی: مقداردهی اولیه‌ی داده‌های نمونه کاربر برای استفاده در تست‌ها.
        
        شرح: یک دیکشنری نمونه در self.user_data ایجاد می‌کند که شامل فیلدهای متداول کاربر است: phone_number (شماره موبایل معتبر)، first_name، last_name، email و password. این داده‌ها به‌عنوان ورودی یکنواخت برای ایجاد کاربران عادی و ادمین در تست‌های این ماژول استفاده می‌شوند و فرض می‌شود مقادیر برای اعتبارسنجی‌های مدل (مانند فرمت شماره موبایل و یکتایی در موارد مربوطه) مناسب باشند.
        """
        self.user_data = {
            'phone_number': '09123456789',
            'first_name': 'علی',
            'last_name': 'محمدی',
            'email': 'ali@example.com',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """تست ایجاد کاربر عادی"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.phone_number, '09123456789')
        self.assertEqual(user.first_name, 'علی')
        self.assertEqual(user.last_name, 'محمدی')
        self.assertEqual(user.user_type, 'patient')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """تست ایجاد کاربر ادمین"""
        admin = User.objects.create_superuser(**self.user_data)
        
        self.assertEqual(admin.user_type, 'admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_verified)
    
    def test_phone_number_uniqueness(self):
        """تست یکتایی شماره تلفن"""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**self.user_data)
    
    def test_phone_number_validation(self):
        """تست اعتبارسنجی شماره تلفن"""
        invalid_phones = ['091234567', '9123456789', '0812345678']
        
        for phone in invalid_phones:
            with self.assertRaises(Exception):
                user = User(
                    phone_number=phone,
                    first_name='تست',
                    last_name='تستی'
                )
                user.full_clean()
    
    def test_user_properties(self):
        """تست property های کاربر"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.get_full_name(), 'علی محمدی')
        self.assertEqual(user.get_short_name(), 'علی')
        self.assertTrue(user.is_patient)
        self.assertFalse(user.is_doctor)
        self.assertFalse(user.is_admin)


class PatientProfileTest(TestCase):
    """تست‌های پروفایل بیمار"""
    
    def setUp(self):
        """
        ایجاد پیش‌شرط‌های تست: دو کاربر نمونه در پایگاه‌داده می‌سازد و به ویژگی‌های نمونه‌ی تست اختصاص می‌دهد.
        
        این متد قبل از اجرای هر تست فراخوانی می‌شود و دو نمونه کاربر را ایجاد می‌کند:
        - self.patient_user: کاربر از نوع 'patient' با شماره تلفن '09123456789' و نام 'رضا احمدی'.
        - self.doctor_user: کاربر از نوع 'doctor' با شماره تلفن '09123456788' و نام 'دکتر حسینی'.
        
        این نمونه‌ها توسط سایر تست‌ها برای بررسی پروفایل‌ها، نقش‌ها و مجوزها مورد استفاده قرار می‌گیرند. کاربران با استفاده از User.objects.create_user ساخته می‌شوند و در پایگاه‌داده ثبت می‌گردند.
        """
        self.patient_user = User.objects.create_user(
            phone_number='09123456789',
            first_name='رضا',
            last_name='احمدی',
            user_type='patient'
        )
        
        self.doctor_user = User.objects.create_user(
            phone_number='09123456788',
            first_name='دکتر',
            last_name='حسینی',
            user_type='doctor'
        )
    
    def test_create_patient_profile(self):
        """تست ایجاد پروفایل بیمار"""
        profile = PatientProfile.objects.create(
            user=self.patient_user,
            medical_record_number='MRN123456',
            blood_type='A+',
            height=Decimal('175.5'),
            weight=Decimal('70.0')
        )
        
        self.assertEqual(profile.user, self.patient_user)
        self.assertEqual(profile.medical_record_number, 'MRN123456')
        self.assertEqual(profile.blood_type, 'A+')
    
    def test_bmi_calculation(self):
        """تست محاسبه BMI"""
        profile = PatientProfile.objects.create(
            user=self.patient_user,
            medical_record_number='MRN123456',
            height=Decimal('175'),
            weight=Decimal('70')
        )
        
        bmi = profile.bmi
        self.assertIsNotNone(bmi)
        self.assertAlmostEqual(bmi, 22.86, places=2)
    
    def test_bmi_with_zero_height(self):
        """تست BMI با قد صفر"""
        profile = PatientProfile.objects.create(
            user=self.patient_user,
            medical_record_number='MRN123456',
            height=Decimal('0'),
            weight=Decimal('70')
        )
        
        self.assertIsNone(profile.bmi)
    
    def test_bmi_with_missing_data(self):
        """تست BMI با داده‌های ناقص"""
        profile = PatientProfile.objects.create(
            user=self.patient_user,
            medical_record_number='MRN123456'
        )
        
        self.assertIsNone(profile.bmi)
    
    def test_medical_record_number_uniqueness(self):
        """
        تأیید می‌کند که فیلد `medical_record_number` در مدل `PatientProfile` یکتا است و تلاش برای ایجاد دو پروفایل با همان شماره پرونده منجر به خطای بانک اطلاعاتی می‌شود.
        
        شرح:
        - ابتدا یک PatientProfile با `medical_record_number='MRN123456'` برای کاربر نمونه ایجاد می‌شود.
        - سپس یک کاربر بیمار دیگر ساخته می‌شود.
        - تلاش برای ایجاد PatientProfile دوم با همان `medical_record_number` درون بلوک `assertRaises(IntegrityError)` انجام می‌شود تا از بروز `IntegrityError` (قید یکتایی در سطح پایگاه‌داده) اطمینان حاصل شود.
        
        تأثیرات جانبی:
        - دو ردیف کاربر در جدول کاربران و یک یا صفر ردیف در جدول PatientProfile بسته به اجرای آزمون در پایگاه‌داده ایجاد می‌شود.
        """
        PatientProfile.objects.create(
            user=self.patient_user,
            medical_record_number='MRN123456'
        )
        
        another_patient = User.objects.create_user(
            phone_number='09123456787',
            first_name='محمد',
            last_name='کریمی',
            user_type='patient'
        )
        
        with self.assertRaises(IntegrityError):
            PatientProfile.objects.create(
                user=another_patient,
                medical_record_number='MRN123456'
            )


class DoctorProfileTest(TestCase):
    """تست‌های پروفایل پزشک"""
    
    def setUp(self):
        """
        یک کاربر با نقش دکتر در پایگاه‌دادهٔ تست ایجاد می‌کند و آن را در self.doctor_user قرار می‌دهد.
        
        این متد در آغاز هر تست اجرا می‌شود تا یک کاربر نمونه با فیلدهای phone_number، first_name، last_name و user_type='doctor' در دیتابیس تست ساخته شود؛ تست‌ها می‌توانند از self.doctor_user برای بررسی ارتباطات، پروفایل‌ها و مجوزها استفاده کنند.
        """
        self.doctor_user = User.objects.create_user(
            phone_number='09123456789',
            first_name='دکتر',
            last_name='رضایی',
            user_type='doctor'
        )
    
    def test_create_doctor_profile(self):
        """تست ایجاد پروفایل پزشک"""
        profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_license_number='ML123456',
            medical_council_number='MC123456',
            specialty='قلب و عروق',
            consultation_fee=Decimal('500000'),
            experience_years=10
        )
        
        self.assertEqual(profile.user, self.doctor_user)
        self.assertEqual(profile.specialty, 'قلب و عروق')
        self.assertEqual(profile.consultation_fee, 500000)
    
    def test_success_rate_calculation(self):
        """
        آزمایشی که نرخ موفقیت پزشک را بررسی می‌کند.
        
        توضیحات:
        این تست یک نمونه DoctorProfile با 100 مشاوره کلی و 95 مشاوره موفق ایجاد می‌کند و انتظار دارد صفت `success_rate` درصد موفقیت را به‌صورت عدد اعشاری (95.0) بازگرداند. این تست تضمین می‌کند محاسبه نرخ موفقیت به‌درستی به‌عنوان (successful_consultations / total_consultations * 100) گزارش می‌شود.
        """
        profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_license_number='ML123456',
            medical_council_number='MC123456',
            specialty='پزشک عمومی',
            consultation_fee=Decimal('300000'),
            total_consultations=100,
            successful_consultations=95
        )
        
        self.assertEqual(profile.success_rate, 95.0)
    
    def test_success_rate_with_zero_consultations(self):
        """تست نرخ موفقیت بدون ویزیت"""
        profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_license_number='ML123456',
            medical_council_number='MC123456',
            specialty='پزشک عمومی',
            consultation_fee=Decimal('300000')
        )
        
        self.assertEqual(profile.success_rate, 0.0)


class RolePermissionTest(TestCase):
    """تست‌های نقش‌ها و مجوزها"""
    
    def setUp(self):
        """
        یک‌بار اجرا می‌شود تا داده‌های مورد نیاز هر تست را در پایگاه‌داده آماده کند.
        
        این متد یک کاربر نمونه (در self.user)، یک نقش نمونه (در self.role) و یک مجوز نمونه (در self.permission) ایجاد و ذخیره می‌کند که برای تست‌های واحد در همان کلاس قابل استفاده هستند. مقادیر فیلدهای ایجادشده به‌صورت صریح تعیین شده‌اند:
        - کاربر: phone_number='09123456789', first_name='تست', last_name='کاربر'
        - نقش: name='test_role', display_name='نقش تست', description='نقش برای تست'
        - مجوز: name='تست خواندن', codename='test_read', resource='test_resource', action='read'
        
        این متد تغییرات را در پایگاه‌داده پایدار می‌کند و تست‌ها می‌توانند با ارجاع به self.user، self.role و self.permission به این نمونه‌ها دسترسی داشته باشند.
        """
        self.user = User.objects.create_user(
            phone_number='09123456789',
            first_name='تست',
            last_name='کاربر'
        )
        
        # ایجاد نقش
        self.role = Role.objects.create(
            name='test_role',
            display_name='نقش تست',
            description='نقش برای تست'
        )
        
        # ایجاد مجوز
        self.permission = Permission.objects.create(
            name='تست خواندن',
            codename='test_read',
            resource='test_resource',
            action='read'
        )
    
    def test_assign_role_to_user(self):
        """تست اختصاص نقش به کاربر"""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            reason='تست اختصاص نقش'
        )
        
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertTrue(user_role.is_active)
        self.assertFalse(user_role.is_expired)
    
    def test_role_expiration(self):
        """
        یک مورد آزمایشی که صحت محاسبهٔ وضعیت انقضای یک UserRole را بررسی می‌کند.
        
        این تست یک UserRole را با مقدار `expires_at` در گذشته ایجاد می‌کند و بررسی می‌کند که پراپرتی محاسبه‌شدهٔ `is_expired` برابر با True باشد. این عملکرد به‌صورت مستقیم در دیتابیس یک رکورد ایجاد می‌کند و برای اعتبارسنجی منطق مدل مربوط به انقضاء نقش استفاده می‌شود.
        """
        past_time = timezone.now() - timedelta(days=1)
        
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            expires_at=past_time
        )
        
        self.assertTrue(user_role.is_expired)
    
    def test_unique_active_user_role(self):
        """تست یکتایی نقش فعال برای کاربر"""
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            is_active=True
        )
        
        # تلاش برای ایجاد نقش فعال تکراری باید خطا دهد
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(
                user=self.user,
                role=self.role,
                is_active=True
            )
        
        # اما ایجاد نقش غیرفعال باید موفق باشد
        inactive_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            is_active=False
        )
        self.assertIsNotNone(inactive_role)
    
    def test_permission_uniqueness(self):
        """تست یکتایی ترکیب resource و action"""
        with self.assertRaises(IntegrityError):
            Permission.objects.create(
                name='تست خواندن دیگر',
                codename='test_read_2',
                resource='test_resource',
                action='read'
            )


class UserSessionTest(TestCase):
    """تست‌های نشست کاربر"""
    
    def setUp(self):
        """
        یک‌خطی:
        یک نمونه‌ی کاربر تستی در پایگاه‌داده ایجاد و در self.user قرار می‌دهد.
        
        توضیح مفصل:
        این متد پیش‌نیاز مشترک تست‌ها را فراهم می‌کند: با فراخوانی User.objects.create_user یک کاربر جدید با شمارهٔ تلفن '09123456789' و نام و نام‌خانوادگی مشخص ایجاد می‌کند و شیء کاربر ایجادشده را در self.user ذخیره می‌کند تا در متدهای تستی بعدی قابل استفاده باشد. متد پس از اجرا هیچ مقدار بازگشتی ندارد و برای تنظیم وضعیت اولیهٔ تست‌ها استفاده می‌شود.
        """
        self.user = User.objects.create_user(
            phone_number='09123456789',
            first_name='تست',
            last_name='کاربر'
        )
    
    def test_create_session(self):
        """تست ایجاد نشست"""
        expires_at = timezone.now() + timedelta(hours=2)
        
        session = UserSession.objects.create(
            user=self.user,
            access_token_hash='hashed_access_token',
            refresh_token_hash='hashed_refresh_token',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            device_type='web',
            expires_at=expires_at
        )
        
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)
        self.assertFalse(session.is_expired)
    
    def test_session_expiration(self):
        """
        یک واحدتستی که بررسی می‌کند یک UserSession با تاریخ انقضای گذشته در وضعیت منقضی‌شده (is_expired == True) قرار می‌گیرد.
        
        توضیحات بیشتر:
        - شیء UserSession با فیلد expires_at در گذشته ساخته می‌شود.
        - انتظار می‌رود ویژگی کمکی `is_expired` آن جلسه مقدار True بازگرداند.
        """
        past_time = timezone.now() - timedelta(hours=1)
        
        session = UserSession.objects.create(
            user=self.user,
            access_token_hash='hashed_access_token',
            refresh_token_hash='hashed_refresh_token',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            device_type='web',
            expires_at=past_time
        )
        
        self.assertTrue(session.is_expired)


class AuthAuditLogTest(TestCase):
    """تست‌های لاگ امنیتی"""
    
    def setUp(self):
        """
        یک‌خطی:
        یک نمونه‌ی کاربر تستی در پایگاه‌داده ایجاد و در self.user قرار می‌دهد.
        
        توضیح مفصل:
        این متد پیش‌نیاز مشترک تست‌ها را فراهم می‌کند: با فراخوانی User.objects.create_user یک کاربر جدید با شمارهٔ تلفن '09123456789' و نام و نام‌خانوادگی مشخص ایجاد می‌کند و شیء کاربر ایجادشده را در self.user ذخیره می‌کند تا در متدهای تستی بعدی قابل استفاده باشد. متد پس از اجرا هیچ مقدار بازگشتی ندارد و برای تنظیم وضعیت اولیهٔ تست‌ها استفاده می‌شود.
        """
        self.user = User.objects.create_user(
            phone_number='09123456789',
            first_name='تست',
            last_name='کاربر'
        )
    
    def test_create_audit_log(self):
        """تست ایجاد لاگ امنیتی"""
        log = AuthAuditLog.objects.create(
            user=self.user,
            event_type='login_success',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True,
            metadata={'device': 'desktop'}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, 'login_success')
        self.assertTrue(log.success)
        self.assertEqual(log.metadata['device'], 'desktop')
    
    def test_audit_log_without_user(self):
        """تست لاگ امنیتی بدون کاربر (برای تلاش‌های ناموفق)"""
        log = AuthAuditLog.objects.create(
            user=None,
            event_type='login_failed',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            error_message='Invalid credentials'
        )
        
        self.assertIsNone(log.user)
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, 'Invalid credentials')


class DataMigrationTest(TestCase):
    """تست‌های migration داده‌های اولیه"""
    
    def test_default_roles_created(self):
        """
        بررسی وجود نقش‌های پیش‌فرض پس از اجرای مهاجرت‌ها.
        
        این تست تأیید می‌کند که مجموعه نقش‌های پیش‌فرض مورد انتظار در مدل Role موجود هستند. فرض تست این است که مایگریشن‌های مربوط به دادهٔ اولیه (seeded defaults) پیش از اجرای تست اعمال شده‌اند. اگر هر یک از نقش‌های زیر وجود نداشته باشد، تست شکست می‌خورد:
        - patient_basic
        - patient_premium
        - doctor_basic
        - doctor_specialist
        - admin
        - staff
        """
        # این تست فرض می‌کند که migration اجرا شده
        expected_roles = [
            'patient_basic', 'patient_premium',
            'doctor_basic', 'doctor_specialist',
            'admin', 'staff'
        ]
        
        for role_name in expected_roles:
            exists = Role.objects.filter(name=role_name).exists()
            self.assertTrue(
                exists,
                f"نقش {role_name} باید وجود داشته باشد"
            )
    
    def test_default_permissions_created(self):
        """
        بررسی می‌کند که مجوزهای پیش‌فرض مورد انتظار پس از اجرای مایگریشن‌ها/بارگذاری داده‌ها در جدول Permission وجود داشته باشند.
        
        این تست برای هر کدنام مجوز در لیست مورد انتظار (`view_own_profile`, `edit_own_profile`, `view_medical_records`, `book_appointment`, `view_patients_list`, `write_prescription`) یک پرس‌وجو انجام می‌دهد و با assertTrue اطمینان می‌دهد که رکورد متناظر در پایگاه‌داده موجود است. در صورت نبود هر یک از مجوزها، تست نام آن را در پیام خطا نمایش می‌دهد.
        """
        expected_permissions = [
            'view_own_profile', 'edit_own_profile',
            'view_medical_records', 'book_appointment',
            'view_patients_list', 'write_prescription'
        ]
        
        for perm_codename in expected_permissions:
            exists = Permission.objects.filter(
                codename=perm_codename
            ).exists()
            self.assertTrue(
                exists,
                f"مجوز {perm_codename} باید وجود داشته باشد"
            )
    
    def test_admin_role_has_all_permissions(self):
        """
        اطمینان می‌دهد که نقش 'admin' به همهٔ مجوزهای تعریف‌شده در سیستم دسترسی دارد.
        
        در این تست، اگر یک نقش با نام 'admin' وجود داشته باشد، تعداد مجوزهای مرتبط با آن نقش با تعداد کل مجوزهای مدل Permission مقایسه می‌شود و باید برابر باشند. در صورت عدم برابری، آزمون با پیام خطای مشخص شده رد می‌شود. اگر نقش 'admin' وجود نداشته باشد، آزمون از مقایسه صرف‌نظر می‌کند (هیچ ادعایی دربارهٔ ایجاد خودکار نقش انجام نمی‌دهد).
        """
        admin_role = Role.objects.filter(name='admin').first()
        if admin_role:
            # admin باید به همه مجوزها دسترسی داشته باشد
            all_permissions_count = Permission.objects.count()
            admin_permissions_count = admin_role.permissions.count()
            
            self.assertEqual(
                admin_permissions_count,
                all_permissions_count,
                "نقش admin باید به همه مجوزها دسترسی داشته باشد"
            )