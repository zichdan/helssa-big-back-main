"""
مدل پلن‌های اشتراک
Subscription Plans Model
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .base import BaseModel


class PlanType(models.TextChoices):
    """انواع پلن"""
    PATIENT_FREE = 'patient_free', 'بیمار - رایگان'
    PATIENT_BASIC = 'patient_basic', 'بیمار - پایه'
    PATIENT_PREMIUM = 'patient_premium', 'بیمار - طلایی'
    DOCTOR_BASIC = 'doctor_basic', 'پزشک - پایه'
    DOCTOR_PROFESSIONAL = 'doctor_professional', 'پزشک - حرفه‌ای'
    DOCTOR_ENTERPRISE = 'doctor_enterprise', 'پزشک - سازمانی'


class FeatureType(models.TextChoices):
    """انواع ویژگی"""
    CHAT_WITH_AI = 'chat_with_ai', 'چت با هوش مصنوعی'
    VOICE_TO_TEXT = 'voice_to_text', 'تبدیل صوت به متن'
    IMAGE_ANALYSIS = 'image_analysis', 'تحلیل تصاویر پزشکی'
    VIDEO_VISIT = 'video_visit', 'ویزیت ویدیویی'
    SOAP_GENERATION = 'soap_generation', 'تولید گزارش SOAP'
    PATIENT_MANAGEMENT = 'patient_management', 'مدیریت بیماران'
    APPOINTMENT_SCHEDULING = 'appointment_scheduling', 'زمان‌بندی قرار ملاقات'
    SMS_REMINDERS = 'sms_reminders', 'یادآوری پیامکی'
    PRIORITY_SUPPORT = 'priority_support', 'پشتیبانی اولویت‌دار'
    ADVANCED_ANALYTICS = 'advanced_analytics', 'تحلیل‌های پیشرفته'
    API_ACCESS = 'api_access', 'دسترسی API'
    CUSTOM_BRANDING = 'custom_branding', 'برندسازی شخصی'


class SubscriptionPlan(BaseModel):
    """مدل پلن‌های اشتراک"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='نام پلن'
    )
    
    type = models.CharField(
        max_length=30,
        choices=PlanType.choices,
        unique=True,
        verbose_name='نوع پلن'
    )
    
    # قیمت‌گذاری
    monthly_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت ماهانه',
        help_text='قیمت ماهانه به ریال'
    )
    
    yearly_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت سالانه',
        help_text='قیمت سالانه به ریال'
    )
    
    # تخفیف
    yearly_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='درصد تخفیف سالانه'
    )
    
    # محدودیت‌ها
    limits = models.JSONField(
        default=dict,
        verbose_name='محدودیت‌ها',
        help_text='محدودیت‌های استفاده به فرمت JSON'
    )
    
    # ویژگی‌ها
    features = models.JSONField(
        default=list,
        verbose_name='ویژگی‌ها',
        help_text='فهرست ویژگی‌های پلن'
    )
    
    # کمیسیون (برای پزشکان)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='نرخ کمیسیون',
        help_text='درصد کمیسیون پلتفرم'
    )
    
    # وضعیت و نمایش
    is_recommended = models.BooleanField(
        default=False,
        verbose_name='پیشنهادی'
    )
    
    is_public = models.BooleanField(
        default=True,
        verbose_name='عمومی',
        help_text='آیا این پلن برای همه قابل مشاهده است؟'
    )
    
    display_order = models.IntegerField(
        default=0,
        verbose_name='ترتیب نمایش'
    )
    
    # رنگ و آیکون
    color_code = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        verbose_name='کد رنگ',
        help_text='کد رنگ هگز (مثال: #FF5722)'
    )
    
    icon = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='آیکون'
    )
    
    # توضیحات
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات'
    )
    
    features_description = models.JSONField(
        default=dict,
        verbose_name='توضیح ویژگی‌ها',
        help_text='توضیح تفصیلی هر ویژگی'
    )
    
    # دوره آزمایشی
    trial_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='روزهای آزمایشی'
    )
    
    class Meta:
        db_table = 'billing_subscription_plans'
        verbose_name = 'پلن اشتراک'
        verbose_name_plural = 'پلن‌های اشتراک'
        ordering = ['display_order', 'monthly_price']
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['is_public', 'is_active']),
            models.Index(fields=['display_order']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
        
    @property
    def target_user_type(self) -> str:
        """نوع کاربر هدف"""
        if self.type.startswith('patient_'):
            return 'patient'
        elif self.type.startswith('doctor_'):
            return 'doctor'
        return 'unknown'
        
    @property
    def effective_yearly_price(self) -> Decimal:
        """قیمت سالانه مؤثر با احتساب تخفیف"""
        if self.yearly_discount_percent > 0:
            discount_amount = (self.monthly_price * 12) * (self.yearly_discount_percent / 100)
            return (self.monthly_price * 12) - discount_amount
        return self.yearly_price
        
    @property
    def monthly_savings(self) -> Decimal:
        """صرفه‌جویی ماهانه در صورت انتخاب پلن سالانه"""
        annual_monthly_price = self.effective_yearly_price / 12
        return self.monthly_price - annual_monthly_price
        
    def get_limit(self, feature: str, default=None):
        """دریافت محدودیت یک ویژگی"""
        return self.limits.get(feature, default)
        
    def has_feature(self, feature: str) -> bool:
        """بررسی وجود ویژگی در پلن"""
        return feature in self.features
        
    def get_feature_description(self, feature: str) -> str:
        """دریافت توضیح یک ویژگی"""
        return self.features_description.get(feature, '')
        
    def is_suitable_for_user(self, user_type: str) -> bool:
        """بررسی مناسب بودن پلن برای نوع کاربر"""
        return self.target_user_type == user_type or self.target_user_type == 'unknown'
        
    def calculate_price(self, billing_cycle: str) -> Decimal:
        """محاسبه قیمت بر اساس دوره صورت‌حساب"""
        if billing_cycle == 'yearly':
            return self.effective_yearly_price
        return self.monthly_price
        
    def get_popular_features(self, limit: int = 5) -> list:
        """دریافت ویژگی‌های محبوب پلن"""
        popular_features = [
            'chat_with_ai',
            'voice_to_text',
            'image_analysis',
            'video_visit',
            'soap_generation'
        ]
        
        return [f for f in popular_features if f in self.features][:limit]