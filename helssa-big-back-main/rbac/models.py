"""
مدل‌های سیستم RBAC و مدیریت کاربران یکپارچه
Unified User Management and RBAC Models
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid
from typing import Optional


class UnifiedUserManager(BaseUserManager):
    """مدیر کاربر یکپارچه"""
    
    def create_user(
        self,
        phone_number: str,
        first_name: str,
        last_name: str,
        password: Optional[str] = None,
        **extra_fields
    ) -> "UnifiedUser":
        """
        ایجاد یک کاربر جدید و ذخیره آن در پایگاه‌داده.
        
        این متد یک نمونه‌ی UnifiedUser با مشخصات داده‌شده می‌سازد، در صورت داشتن مقدار برای password آن را هش و تنظیم می‌کند و در غیر این صورت رمز را غیرقابل‌استفاده قرار می‌دهد، سپس کاربر را با استفاده از همان اتصال پایگاه‌دادهٔ مدیر (manager) ذخیره می‌کند.
        
        Parameters:
            phone_number (str): شماره تلفن کاربر؛ الزامی است و در صورت نبودن مقدار، ValueError پرتاب می‌شود.
            first_name (str): نام کوچک کاربر.
            last_name (str): نام خانوادگی کاربر.
            password (Optional[str]): در صورت ارائه، به‌عنوان رمز عبور قرار می‌گیرد؛ در غیر این صورت رمز غیرقابل‌استفاده تنظیم می‌شود.
            **extra_fields: فیلدهای اختیاری مدل که مستقیماً به سازنده مدل پاس داده می‌شوند (مثلاً is_active، user_type و غیره).
        
        Returns:
            UnifiedUser: نمونهٔ ساخته‌شده و ذخیره‌شدهٔ کاربر.
        
        Raises:
            ValueError: اگر phone_number خالی باشد.
        """
        if not phone_number:
            raise ValueError('شماره تلفن الزامی است')
            
        user = self.model(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user
        
    def create_superuser(
        self,
        phone_number: str,
        first_name: str,
        last_name: str,
        password: str,
        **extra_fields
    ) -> "UnifiedUser":
        """
        یک سوپر‌یوزر (کاربر ادمین) جدید ایجاد و ذخیره می‌کند.
        
        این متد فیلدهای پیش‌فرض مورد نیاز برای سوپر‌یوزر را تنظیم می‌کند: `is_staff=True`، `is_superuser=True`، `is_active=True`، `is_verified=True` و `user_type='admin'`، سپس با اعتبارسنجی از درست بودن `is_staff` و `is_superuser`، ساخت کاربر را به `create_user` واگذار می‌کند.
        
        Parameters:
            phone_number: شماره تلفن کاربر (شناسه ورود).
            first_name: نام کوچک کاربر.
            last_name: نام خانوادگی کاربر.
            password: کلمهٔ عبور کاربر.
            **extra_fields: هر فیلد اضافی مدل که باید هنگام ایجاد کاربر تنظیم شود.
        
        Returns:
            UnifiedUser: نمونهٔ ایجادشدهٔ سوپر‌یوزر.
        
        Raises:
            ValueError: اگر `is_staff` یا `is_superuser` به True تنظیم نشده باشند.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(
            phone_number, 
            first_name, 
            last_name, 
            password,
            **extra_fields
        )


class UnifiedUser(AbstractBaseUser, PermissionsMixin):
    """
    مدل کاربر یکپارچه برای بیماران و پزشکان
    این مدل به عنوان کاربر مادر عمل می‌کند
    """
    
    # شناسه‌ها
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name='شناسه یکتا'
    )
    
    phone_number = models.CharField(
        max_length=11, 
        unique=True, 
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ],
        verbose_name='شماره موبایل'
    )
    
    email = models.EmailField(
        unique=True, 
        null=True, 
        blank=True, 
        db_index=True,
        verbose_name='ایمیل'
    )
    
    national_id = models.CharField(
        max_length=10, 
        unique=True, 
        null=True, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='کد ملی باید 10 رقم باشد'
            )
        ],
        verbose_name='کد ملی'
    )
    
    # اطلاعات پایه
    first_name = models.CharField(
        max_length=50,
        verbose_name='نام'
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name='نام خانوادگی'
    )
    
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='تاریخ تولد'
    )
    
    GENDER_CHOICES = [
        ('M', 'مرد'),
        ('F', 'زن'),
        ('O', 'سایر')
    ]
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name='جنسیت'
    )
    
    # نقش‌ها
    USER_TYPE_CHOICES = [
        ('patient', 'بیمار'),
        ('doctor', 'پزشک'),
        ('admin', 'مدیر سیستم'),
        ('staff', 'کارمند')
    ]
    
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='patient',
        db_index=True,
        verbose_name='نوع کاربر'
    )
    
    # وضعیت
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تایید شده'
    )
    
    verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='زمان تایید'
    )
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name='کارمند'
    )
    
    # تنظیمات امنیتی
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name='احراز هویت دو مرحله‌ای'
    )
    
    failed_login_attempts = models.IntegerField(
        default=0,
        verbose_name='تعداد تلاش‌های ناموفق'
    )
    
    last_login_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name='آخرین IP ورود'
    )
    
    last_login_device = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        verbose_name='آخرین دستگاه ورود'
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان به‌روزرسانی'
    )
    
    last_activity = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='آخرین فعالیت'
    )
    
    objects = UnifiedUserManager()
    
    class Meta:
        db_table = 'unified_users'
        verbose_name = 'کاربر یکپارچه'
        verbose_name_plural = 'کاربران یکپارچه'
        indexes = [
            models.Index(fields=['phone_number', 'is_active']),
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['user_type', 'is_active']),
            models.Index(fields=['national_id']),
        ]
        
    def __str__(self):
        """
        نمایش متنی کاربر شامل نام کامل و شماره تلفن.
        
        برمی‌گرداند یک رشته‌ی قابل خواندن برای نمایش‌های مدیریتی/لاگ‌ها که شامل نام و نام خانوادگی و شماره تلفن کاربر به صورت "First Last (09...)" است.
        """
        return f"{self.first_name} {self.last_name} ({self.phone_number})"
        
    def get_full_name(self) -> str:
        """
        بازگرداندن نام کامل کاربر به فرم "نام خانوادگی".
        
        شرح:
            این متد نام و نام‌خانوادگی شیء کاربر را با یک فاصله بین آن‌ها ترکیب کرده و به‌صورت یک رشته بازمی‌گرداند.
            در صورتی که یکی از فیلدها خالی باشد، رشتهٔ بازگشتی همچنان شامل یک فاصله خواهد بود (مثلاً "نام " یا " نام‌خانوادگی").
        
        Returns:
            str: نام کامل در قالب "FirstName LastName".
        """
        return f"{self.first_name} {self.last_name}"
        
    def get_short_name(self) -> str:
        """
        بازگرداندن نام کوتاه کاربر (معمولاً نام کوچک).
        
        این متد مقدار فیلد `first_name` را برمی‌گرداند. در صورت خالی بودن فیلد، رشتهٔ خالی بازگردانده خواهد شد.
        Returns:
            str: نام کوتاه کاربر (مقدار `first_name`).
        """
        return self.first_name
        
    @property
    def is_patient(self) -> bool:
        """
        بررسی می‌کند که کاربر از نوع 'patient' است یا خیر.
        
        این متد مقدار بولی برمی‌گرداند که نشان می‌دهد فیلد `user_type` برابر رشته‌ی `'patient'` است؛ بدون تغییر وضعیت شیء و بدون اثرات جانبی.
        """
        return self.user_type == 'patient'
        
    @property
    def is_doctor(self) -> bool:
        """
        بررسی می‌کند که کاربر از نوع پزشک است یا خیر.
        
        Returns:
        	bool: مقدار True در صورتی که فیلد `user_type` برابر با `'doctor'` باشد، در غیر این صورت False.
        """
        return self.user_type == 'doctor'
        
    @property
    def is_admin(self) -> bool:
        """
        بررسی می‌کند که کاربر از نوع مدیر (admin) باشد.
        
        این پراپرتی/متد مقدار بولی برمی‌گرداند که نشان می‌دهد فیلد user_type کاربر دقیقاً برابر رشته `'admin'` است یا خیر. هیچ اثر جانبی‌ای ندارد.
        Returns:
        	bool: True اگر user_type برابر `'admin'` باشد، در غیر این صورت False.
        """
        return self.user_type == 'admin'


class PatientProfile(models.Model):
    """
    پروفایل اختصاصی بیمار
    حاوی اطلاعات پزشکی و درمانی بیمار
    """
    
    user = models.OneToOneField(
        UnifiedUser,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='کاربر'
    )
    medical_record_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='شماره پرونده پزشکی'
    )
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    blood_type = models.CharField(
        max_length=5, 
        choices=BLOOD_TYPE_CHOICES,
        null=True, 
        blank=True,
        verbose_name='گروه خونی'
    )
    
    # اطلاعات پزشکی به صورت JSON
    allergies = models.JSONField(
        default=list,
        verbose_name='حساسیت‌ها',
        help_text='لیست حساسیت‌های دارویی و غذایی'
    )
    
    chronic_conditions = models.JSONField(
        default=list,
        verbose_name='بیماری‌های مزمن',
        help_text='لیست بیماری‌های مزمن و زمینه‌ای'
    )
    
    current_medications = models.JSONField(
        default=list,
        verbose_name='داروهای مصرفی',
        help_text='لیست داروهای در حال مصرف'
    )
    
    medical_history = models.JSONField(
        default=dict,
        verbose_name='سابقه پزشکی',
        help_text='سابقه بیماری‌ها، جراحی‌ها و بستری‌ها'
    )
    
    family_medical_history = models.JSONField(
        default=dict,
        verbose_name='سابقه پزشکی خانوادگی'
    )
    
    # اطلاعات تماس اضطراری
    emergency_contact = models.JSONField(
        default=dict,
        verbose_name='مخاطب اضطراری',
        help_text='اطلاعات تماس در مواقع اضطراری'
    )
    
    # اطلاعات بیمه
    insurance_info = models.JSONField(
        default=dict,
        verbose_name='اطلاعات بیمه',
        help_text='اطلاعات بیمه‌های درمانی'
    )
    
    # اطلاعات فیزیکی
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='قد (سانتی‌متر)'
    )
    
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='وزن (کیلوگرم)'
    )
    
    # تنظیمات
    preferred_language = models.CharField(
        max_length=5,
        default='fa',
        verbose_name='زبان ترجیحی'
    )
    
    notification_preferences = models.JSONField(
        default=dict,
        verbose_name='تنظیمات اعلان‌ها'
    )
    
    privacy_settings = models.JSONField(
        default=dict,
        verbose_name='تنظیمات حریم خصوصی'
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان به‌روزرسانی'
    )
    
    class Meta:
        db_table = 'patient_profiles'
        verbose_name = 'پروفایل بیمار'
        verbose_name_plural = 'پروفایل‌های بیماران'
        indexes = [
            models.Index(fields=['medical_record_number']),
        ]
        
    def __str__(self):
        """
        نمایش رشته‌ای (human-readable) پروفایل بیمار.
        
        این متد یک نمایش کوتاه و قابل‌خواندن برای نمونه‌ی PatientProfile بازمی‌گرداند که شامل عبارت «پروفایل بیمار:» به‌همراه نام کامل کاربر مرتبط است (از user.get_full_name() استفاده می‌کند). این مقدار معمولاً در رابط ادمین، لاگ‌ها و زمان نمایش نمونه‌ها به‌عنوان شناسه‌ی خوانا استفاده می‌شود.
        
        Returns:
            str: رشته نمایشی مانند "پروفایل بیمار: {نام کامل کاربر}"
        """
        return f"پروفایل بیمار: {self.user.get_full_name()}"
        
    @property
    def bmi(self) -> Optional[float]:
        """
        محاسبهٔ شاخص تودهٔ بدنی (BMI) بر اساس قد و وزن کاربر.
        
        اگر قد (height) و وزن (weight) موجود و معتبر باشند، قد را به متر تبدیل (از سانتی‌متر) کرده و مقدار BMI را برابر وزن به کیلوگرم تقسیم بر مجذور قد برحسب متر برمی‌گرداند. در صورت نبودن یا نامعتبر بودن هر یک از مقادیر (مثلاً قد صفر یا منفی) مقدار None بازگردانده می‌شود.
        
        Returns:
            Optional[float]: مقدار BMI به‌صورت عدد ممیز شناور یا None اگر محاسبه ممکن نباشد.
        """
        if self.height and self.weight:
            height_m = float(self.height) / 100
            if height_m > 0:
                return float(self.weight) / (height_m ** 2)
        return None


class DoctorProfile(models.Model):
    """
    پروفایل اختصاصی پزشک
    حاوی اطلاعات تخصصی و حرفه‌ای پزشک
    """
    
    user = models.OneToOneField(
        UnifiedUser,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'user_type': 'doctor'},
        verbose_name='کاربر'
    )
    medical_license_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='شماره پروانه پزشکی'
    )
    
    medical_council_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره نظام پزشکی'
    )
    
    # تخصص
    specialty = models.CharField(
        max_length=100,
        verbose_name='تخصص اصلی'
    )
    
    sub_specialty = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name='فوق تخصص'
    )
    
    # تحصیلات و تجربه
    education = models.JSONField(
        default=list,
        verbose_name='سوابق تحصیلی',
        help_text='لیست مدارک تحصیلی و دانشگاه‌ها'
    )
    
    certifications = models.JSONField(
        default=list,
        verbose_name='گواهینامه‌ها',
        help_text='گواهینامه‌ها و دوره‌های تخصصی'
    )
    
    experience_years = models.IntegerField(
        default=0,
        verbose_name='سال‌های تجربه'
    )
    
    # اطلاعات مالی
    consultation_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        verbose_name='هزینه ویزیت (تومان)'
    )
    
    emergency_fee = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name='هزینه ویزیت اورژانسی (تومان)'
    )
    
    # اطلاعات حرفه‌ای
    bio = models.TextField(
        null=True, 
        blank=True,
        verbose_name='بیوگرافی'
    )
    
    languages = models.JSONField(
        default=list,
        verbose_name='زبان‌های مسلط',
        help_text='لیست زبان‌هایی که پزشک به آن مسلط است'
    )
    
    services = models.JSONField(
        default=list,
        verbose_name='خدمات ارائه شده',
        help_text='لیست خدمات قابل ارائه توسط پزشک'
    )
    
    # ساعات کاری
    working_hours = models.JSONField(
        default=dict,
        verbose_name='ساعات کاری',
        help_text='برنامه کاری هفتگی پزشک'
    )
    
    consultation_duration = models.IntegerField(
        default=15,
        verbose_name='مدت زمان ویزیت (دقیقه)'
    )
    
    # تنظیمات
    accepts_insurance = models.BooleanField(
        default=True,
        verbose_name='پذیرش بیمه'
    )
    
    accepted_insurances = models.JSONField(
        default=list,
        verbose_name='بیمه‌های قابل پذیرش'
    )
    
    online_consultation = models.BooleanField(
        default=True,
        verbose_name='ویزیت آنلاین'
    )
    
    in_person_consultation = models.BooleanField(
        default=False,
        verbose_name='ویزیت حضوری'
    )
    
    # آمار و امتیازات
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        verbose_name='امتیاز'
    )
    
    total_consultations = models.IntegerField(
        default=0,
        verbose_name='تعداد کل ویزیت‌ها'
    )
    
    successful_consultations = models.IntegerField(
        default=0,
        verbose_name='ویزیت‌های موفق'
    )
    
    # وضعیت
    is_available = models.BooleanField(
        default=True,
        verbose_name='در دسترس'
    )
    
    vacation_mode = models.BooleanField(
        default=False,
        verbose_name='حالت مرخصی'
    )
    
    vacation_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='پیام مرخصی'
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان به‌روزرسانی'
    )
    
    class Meta:
        db_table = 'doctor_profiles'
        verbose_name = 'پروفایل پزشک'
        verbose_name_plural = 'پروفایل‌های پزشکان'
        indexes = [
         indexes = [
             models.Index(fields=['specialty']),
             models.Index(fields=['is_available', 'vacation_mode']),
         ]
        
    def __str__(self):
        """
        نمایش متنی پروفایل پزشک به صورت `{دکتر <نام کامل>} - {تخصص}`.
        
        شرح:
            مقدار بازگشتی رشته‌ای است که نام کامل کاربر مرتبط (با استفاده از `user.get_full_name()`)
            و مقدار فیلد `specialty` را ترکیب می‌کند تا نمایش کوتاهی از پزشک ارائه دهد.
        
        Returns:
            str: رشتهٔ نمایشی مانند: "دکتر علی رضایی - قلب و عروق".
        """
        return f"دکتر {self.user.get_full_name()} - {self.specialty}"
        
    @property
    def success_rate(self) -> float:
        """
        محاسبهٔ درصد موفقیت مشاوره‌ها بر اساس تعداد کل ویزیت‌ها و ویزیت‌های موفق.
        
        اگر total_consultations بزرگ‌تر از صفر باشد، مقدار (successful_consultations / total_consultations) * 100 را برمی‌گرداند (قابل تفسیر به‌عنوان درصد بین 0.0 تا 100.0). در غیر این صورت، 0.0 بازمی‌گرداند تا از تقسیم بر صفر جلوگیری شود.
        """
        if self.total_consultations > 0:
            return (self.successful_consultations / self.total_consultations) * 100
        return 0.0


# مدل‌های RBAC

class Role(models.Model):
    """
    نقش‌های سیستم
    برای مدیریت دسترسی‌ها بر اساس نقش
    """
    
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='نام نقش'
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name='نام نمایشی'
    )
    
    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name='توضیحات'
    )
    
    permissions = models.ManyToManyField(
        'Permission', 
        related_name='roles',
        blank=True,
        verbose_name='مجوزها'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    is_system = models.BooleanField(
        default=False,
        verbose_name='نقش سیستمی',
        help_text='نقش‌های سیستمی قابل حذف نیستند'
    )
    
    priority = models.IntegerField(
        default=0,
        verbose_name='اولویت',
        help_text='نقش‌ها بر اساس اولویت مرتب می‌شوند'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان به‌روزرسانی'
    )
    
    class Meta:
        db_table = 'auth_roles'
        verbose_name = 'نقش'
        verbose_name_plural = 'نقش‌ها'
        ordering = ['-priority', 'name']
        
    def __str__(self):
        """
        نمایش رشته‌ای شیء Role با استفاده از فیلد display_name.
        
        برمی‌گرداند:
            str: نام نمایشی نقش (display_name) که برای نمایش در رابط مدیریت و لاگ‌ها استفاده می‌شود.
        """
        return self.display_name


class Permission(models.Model):
    """
    مجوزهای سیستم
    برای کنترل دسترسی به منابع و عملیات
    """
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='نام مجوز'
    )
    
    codename = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='کد مجوز'
    )
    
    resource = models.CharField(
        max_length=50,
        verbose_name='منبع',
        help_text='مثال: patient_record, prescription'
    )
    
    action = models.CharField(
        max_length=50,
        verbose_name='عملیات',
        help_text='مثال: read, write, delete'
    )
    
    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name='توضیحات'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    class Meta:
        db_table = 'auth_permissions'
        verbose_name = 'مجوز'
        verbose_name_plural = 'مجوزها'
        unique_together = [['resource', 'action']]
        ordering = ['resource', 'action']
        
    def __str__(self):
        """
        نمایش متنی دسترسی با ترکیب عنوان منبع، عمل و نام.
        
        برمی‌گرداند رشته‌ای خوانا به صورت "{resource}:{action} - {name}" که برای لاگ‌زدن، نمایش در رابط کاربری و تشخیص سریع مجوزها استفاده می‌شود.
        """
        return f"{self.resource}:{self.action} - {self.name}"


class UserRole(models.Model):
    """
    ارتباط کاربر و نقش
    برای اختصاص نقش‌ها به کاربران
    """
    
    user = models.ForeignKey(
        UnifiedUser, 
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name='کاربر'
    )
    
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE,
        related_name='user_assignments',
        verbose_name='نقش'
    )
    
    assigned_by = models.ForeignKey(
        UnifiedUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name='اختصاص دهنده'
    )
    
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان اختصاص'
    )
    
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='زمان انقضا'
    )
    
    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='دلیل اختصاص'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        db_table = 'user_roles'
        verbose_name = 'نقش کاربر'
        verbose_name_plural = 'نقش‌های کاربران'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role'],
                condition=models.Q(is_active=True),
                name='uniq_active_user_role'
            ),
        ]
        
    def __str__(self):
        """
        نمایشی متنی از انتساب نقش به کاربر.
        
        برمی‌گرداند یک رشته متشکل از نام کامل کاربر و عنوان قابل‌نمایش نقش به صورت "{نام کامل کاربر} - {عنوان نقش}"، که برای نمایش خلاصه‌ای از رابطه UserRole در رابط‌های مدیریتی و لاگ‌ها مناسب است.
        
        Returns:
            str: رشتهٔ نمایشی ترکیبی از نام کامل کاربر و نمایش نقش.
        """
        return f"{self.user.get_full_name()} - {self.role.display_name}"
        
    @property
    def is_expired(self) -> bool:
        """
        بررسی می‌کند که نقش کاربر منقضی شده است یا خیر.
        
        اگر فیلد `expires_at` مقداردهی شده باشد، زمان فعلی (به‌صورت timezone-aware) با `expires_at` مقایسه می‌شود و در صورت گذشته بودن زمان انقضا مقدار `True` بازگردانده می‌شود، در غیر این صورت `False` بازمی‌گردد.
        @return: True اگر `expires_at` تعیین شده و قبل از زمان فعلی باشد، در غیر این صورت False.
        """
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class UserSession(models.Model):
    """
    مدیریت نشست‌های کاربر
    برای ردیابی و کنترل جلسات کاری کاربران
    """
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        verbose_name='شناسه نشست'
    )
    
    user = models.ForeignKey(
        UnifiedUser, 
        on_delete=models.CASCADE, 
        related_name='sessions',
        verbose_name='کاربر'
    )
    
    # اطلاعات توکن
    access_token_hash = models.CharField(
        max_length=128,
        verbose_name='هش توکن دسترسی'
    )
    refresh_token_hash = models.CharField(
        max_length=128,
        verbose_name='هش توکن تازه‌سازی'
    )
    
    token_version = models.IntegerField(
        default=1,
        verbose_name='نسخه توکن'
    )
    # اطلاعات نشست
    ip_address = models.GenericIPAddressField(
        verbose_name='آدرس IP'
    )
    
    user_agent = models.CharField(
        max_length=500,
        verbose_name='User Agent'
    )
    
    device_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name='شناسه دستگاه'
    )
    
    DEVICE_TYPE_CHOICES = [
        ('web', 'وب'),
        ('ios', 'iOS'),
        ('android', 'اندروید'),
        ('desktop', 'دسکتاپ'),
    ]
    
    device_type = models.CharField(
        max_length=50,
        choices=DEVICE_TYPE_CHOICES,
        verbose_name='نوع دستگاه'
    )
    
    # امنیت
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین فعالیت'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='زمان انقضا'
    )
    
    # متادیتا
    location = models.JSONField(
        null=True, 
        blank=True,
        verbose_name='موقعیت جغرافیایی',
        help_text='اطلاعات GeoIP'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'نشست کاربر'
        verbose_name_plural = 'نشست‌های کاربران'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['device_id', 'is_active']),
        ]
        
    def __str__(self):
        """
        نمایش متنی کوتاه از نشست کاربر شامل نام کامل کاربر و نوع دستگاه.
        
        این متد رشته قابل‌خواندی برمی‌گرداند که برای لاگ‌گذاری یا نمایش در رابط‌های مدیریت استفاده می‌شود و به صورت "نشست {نام کامل کاربر} - {نوع دستگاه}" فرمات می‌شود. مقدار نام کامل از متد get_full_name() روی شیٔ کاربر استخراج می‌شود.
        
        Returns:
            str: رشته نمایشی نشست (به فارسی).
        """
        return f"نشست {self.user.get_full_name()} - {self.device_type}"
        
    @property
    def is_expired(self) -> bool:
        """
        بررسی می‌کند آیا نشست منقضی شده است.
        
        این متد زمان کنونی (با استفاده از timezone.now()) را با فیلد `expires_at` مقایسه می‌کند و مقدار بولی بازمی‌گرداند:
        True اگر زمان کنونی بعد از `expires_at` باشد، در غیر این صورت False.
        توجه: تابع مطابق کد موجود فرض می‌کند `expires_at` مقداردهی شده است و در صورت بودن None ممکن است استثنا ایجاد شود.
        
        Returns:
            bool: True در صورت منقضی بودن نشست، False در غیر این صورت.
        """
        return timezone.now() > self.expires_at


class AuthAuditLog(models.Model):
    """
    لاگ‌های امنیتی احراز هویت
    برای ثبت و ردیابی فعالیت‌های امنیتی
    """
    
    EVENT_TYPE_CHOICES = [
        ('login_success', 'ورود موفق'),
        ('login_failed', 'ورود ناموفق'),
        ('logout', 'خروج'),
        ('register', 'ثبت‌نام'),
        ('password_change', 'تغییر رمز عبور'),
        ('role_assigned', 'اختصاص نقش'),
        ('role_removed', 'حذف نقش'),
        ('permission_denied', 'دسترسی رد شد'),
        ('session_expired', 'نشست منقضی شد'),
        ('suspicious_activity', 'فعالیت مشکوک'),
        ('otp_sent', 'ارسال OTP'),
        ('otp_verified', 'تایید OTP'),
        ('otp_failed', 'OTP نامعتبر'),
    ]
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4,
        verbose_name='شناسه لاگ'
    )
    
    user = models.ForeignKey(
        UnifiedUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auth_logs',
        verbose_name='کاربر'
    )
    
    event_type = models.CharField(
        max_length=50, 
        choices=EVENT_TYPE_CHOICES,
        verbose_name='نوع رویداد'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        verbose_name='User Agent'
    )
    
    # جزئیات رویداد
    success = models.BooleanField(
        default=True,
        verbose_name='موفقیت‌آمیز'
    )
    
    error_message = models.TextField(
        null=True, 
        blank=True,
        verbose_name='پیام خطا'
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name='اطلاعات اضافی'
    )
    
    # زمان
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان رویداد'
    )
    
    class Meta:
        db_table = 'auth_audit_logs'
        verbose_name = 'لاگ امنیتی'
        verbose_name_plural = 'لاگ‌های امنیتی'
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        """
        نمایش متنی مختصر از رکورد لاگ احراز هویت.
        
        بازمی‌گرداند یک رشته خوانا که شامل متن نمایشِ نوع رویداد (از `get_event_type_display()`)،
        نام کامل کاربر در صورت وجود یا `'ناشناس'` در غیر این صورت، و زمان ایجاد (`created_at`) است.
        """
        user_str = self.user.get_full_name() if self.user else 'ناشناس'
        return f"{self.get_event_type_display()} - {user_str} - {self.created_at}"