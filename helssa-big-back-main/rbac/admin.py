"""
پنل مدیریت Django برای مدل‌های RBAC
Django Admin Panel for RBAC Models
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from .models import (
    UnifiedUser, PatientProfile, DoctorProfile,
    Role, Permission, UserRole, UserSession, AuthAuditLog
)


@admin.register(UnifiedUser)
class UnifiedUserAdmin(BaseUserAdmin):
    """مدیریت کاربران یکپارچه"""
    
    list_display = [
        'phone_number', 'get_full_name', 'user_type', 
        'is_verified', 'is_active', 'created_at'
    ]
    
    list_filter = [
        'user_type', 'is_active', 'is_verified', 
        'is_staff', 'is_superuser', 'two_factor_enabled',
        'created_at'
    ]
    
    search_fields = [
        'phone_number', 'email', 'first_name', 
        'last_name', 'national_id'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_activity',
        'verified_at', 'last_login', 'failed_login_attempts'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'phone_number', 'email', 'national_id')
        }),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'birth_date', 'gender')
        }),
        ('نوع کاربر', {
            'fields': ('user_type',)
        }),
        ('وضعیت', {
            'fields': (
                'is_active', 'is_verified', 'verified_at',
                'is_staff', 'is_superuser'
            )
        }),
        ('امنیت', {
            'fields': (
                'password', 'two_factor_enabled', 
                'failed_login_attempts', 'last_login_ip', 
                'last_login_device'
            )
        }),
        ('زمان‌ها', {
            'fields': (
                'created_at', 'updated_at', 'last_login', 
                'last_activity'
            )
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number', 'email', 'first_name', 
                'last_name', 'user_type', 'password1', 
                'password2'
            ),
        }),
    )
    
    ordering = ['-created_at']
    
    def get_full_name(self, obj):
        """
        بازگرداندن نام کامل یک کاربر برای نمایش در پنل ادمین.
        
        پارامترها:
            obj: نمونه‌ی کاربری (یا آبجکتی که متد `get_full_name()` را پیاده‌سازی کرده است) که نام کامل آن استخراج می‌شود.
        
        بازگشت:
            str: رشته‌ی نام کامل همانند خروجی `obj.get_full_name()`؛ در صورت مقداردهی خالی یا پیاده‌سازی متفاوت متد، مقدار برگشتی مطابق با آن خواهد بود.
        """
        return obj.get_full_name()
    get_full_name.short_description = 'نام کامل'
    
    def get_queryset(self, request):
        """
        کوئری‌ست پیش‌پردازش‌شده برای جلوگیری از N+1 و بهینه‌سازی بارگذاری داده‌های مرتبط.
        
        این متد یک queryset پایه از سوپرکلاس می‌گیرد و روابط یک‌به‌یک مربوط به پروفایل‌های بیمار و پزشک را با select_related و رابطه‌های چند‌تایی نقش‌های کاربر را با prefetch_related پیش‌بارگذاری می‌کند تا هنگام دسترسی به patient_profile، doctor_profile یا user_roles__role در نمای ادمین از اجرای کوئری‌های اضافی جلوگیری شود.
        
        Returns:
            QuerySet: queryset بهینه‌شده برای استفاده در لیست ادمین.
        """
        qs = super().get_queryset(request)
        return qs.select_related(
            'patient_profile', 'doctor_profile'
        ).prefetch_related('user_roles__role')


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """مدیریت پروفایل بیماران"""
    
    list_display = [
        'get_patient_name', 'medical_record_number', 
        'blood_type', 'get_phone', 'created_at'
    ]
    
    list_filter = ['blood_type', 'created_at']
    
    search_fields = [
        'user__phone_number', 'user__first_name', 
        'user__last_name', 'medical_record_number'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'get_bmi']
    
    fieldsets = (
        ('کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات پزشکی', {
            'fields': (
                'medical_record_number', 'blood_type',
                'height', 'weight', 'get_bmi'
            )
        }),
        ('سوابق پزشکی', {
            'fields': (
                'allergies', 'chronic_conditions',
                'current_medications', 'medical_history',
                'family_medical_history'
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات تماس', {
            'fields': ('emergency_contact',)
        }),
        ('بیمه', {
            'fields': ('insurance_info',)
        }),
        ('تنظیمات', {
            'fields': (
                'preferred_language', 'notification_preferences',
                'privacy_settings'
            ),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_bmi(self, obj):
        """
        نمایش مقدار BMI به‌صورت قالب‌بندی‌شده و رنگی برای نمایش در لیست ادمین.
        
        اگر مقدار BMI موجود باشد، یک رشته HTML امن (`<span>`) بازمی‌گرداند که مقدار BMI با یک رقم اعشار و وضعیت فارسی («کم‌وزن»، «نرمال»، «اضافه وزن»، «چاق») را نمایش می‌دهد و رنگ متن بر اساس بازه BMI تعیین می‌شود (آبی، سبز، نارنجی، قرمز). در صورت نبود مقدار BMI، علامت `'-'` بازگردانده می‌شود.
        
        Returns:
            str: رشته‌ای امن برای قرارگیری در قالب ادمین (HTML) یا `'-'` اگر BMI موجود نباشد.
        """
        bmi = obj.bmi
        if bmi is not None:
            if bmi < 18.5:
                color = 'blue'
                status = 'کم‌وزن'
            elif bmi < 25:
                color = 'green'
                status = 'نرمال'
            elif bmi < 30:
                color = 'orange'
                status = 'اضافه وزن'
            else:
                color = 'red'
                status = 'چاق'
            return format_html(
                '<span style="color: {};">{:.1f} ({})</span>',
                color, bmi, status
            )
        return '-'
    get_bmi.short_description = 'BMI'

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """مدیریت پروفایل پزشکان"""
    
    list_display = [
        'get_doctor_name', 'specialty', 'medical_license_number',
        'consultation_fee', 'rating', 'is_available', 'created_at'
    ]
    
    list_filter = [
        'specialty', 'is_available', 'vacation_mode',
        'online_consultation', 'in_person_consultation',
        'accepts_insurance', 'created_at'
    ]
    
    search_fields = [
        'user__phone_number', 'user__first_name', 'user__last_name',
        'medical_license_number', 'medical_council_number',
        'specialty', 'sub_specialty'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'rating',
        'total_consultations', 'successful_consultations',
        'get_success_rate'
    ]
    
    fieldsets = (
        ('کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات حرفه‌ای', {
            'fields': (
                'medical_license_number', 'medical_council_number',
                'specialty', 'sub_specialty', 'experience_years'
            )
        }),
        ('تحصیلات و گواهینامه‌ها', {
            'fields': ('education', 'certifications'),
            'classes': ('collapse',)
        }),
        ('اطلاعات مالی', {
            'fields': ('consultation_fee', 'emergency_fee')
        }),
        ('اطلاعات تکمیلی', {
            'fields': (
                'bio', 'languages', 'services',
                'working_hours', 'consultation_duration'
            ),
            'classes': ('collapse',)
        }),
        ('تنظیمات ویزیت', {
            'fields': (
                'online_consultation', 'in_person_consultation',
                'accepts_insurance', 'accepted_insurances'
            )
        }),
        ('آمار و عملکرد', {
            'fields': (
                'rating', 'total_consultations',
                'successful_consultations', 'get_success_rate'
            )
        }),
        ('وضعیت', {
            'fields': (
                'is_available', 'vacation_mode', 'vacation_message'
            )
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_doctor_name(self, obj):
        """
        یک خطی: نام نمایش‌داده‌شدهٔ پزشک را با پیش‌وند فارسی "دکتر" بازمی‌گرداند.
        
        توضیحات:
            این متد نام کامل کاربر مرتبط با شیء پروفایل پزشک را با پیش‌وند "دکتر " قالب‌بندی می‌کند و به صورت یک رشته برمی‌گرداند.
        
        پارامترها:
            obj: نمونه‌ای از مدل DoctorProfile که انتظار می‌رود صفت `user` مرتبط و متدی به‌نام `get_full_name()` داشته باشد.
        
        بازگشت:
            str: رشته‌ای شامل پیش‌وند "دکتر " به‌همراه مقدار بازگشتی از `obj.user.get_full_name()`.
        """
        return f"دکتر {obj.user.get_full_name()}"
    get_doctor_name.short_description = 'نام پزشک'
    
    def get_success_rate(self, obj):
        """
        نمایش نرخ موفقیت پزشک به‌صورت درصد رنگ‌کدشده.
        
        پارامترها:
            obj: نمونه‌ای که دارای صفت `success_rate` (مقدار عددی بین ۰ تا ۱۰۰) است.
        
        توضیحات:
            - مقدار `success_rate` را به یک رشته درصد با یک رقم اعشار تبدیل و با تگ HTML `<span>` برمی‌گرداند.
            - بازه‌های رنگ‌بندی:
                - >= 90: سبز
                - >= 70 و < 90: نارنجی
                - < 70: قرمز
            - مقدار بازگشتی با `format_html` امن‌سازی شده و برای نمایش در لیست ادمین مناسب است.
        
        بازگشت:
            str: یک رشته HTML حاوی درصد قالب‌بندی‌شده و رنگ‌دار، مثلاً `'<span style="color: green;">92.3%</span>'`.
        """
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    get_success_rate.short_description = 'نرخ موفقیت'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """مدیریت نقش‌ها"""
    
# --- in rbac/admin.py ---

class RoleAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'name', 'priority',
        'is_system', 'is_active', 'get_permissions_count',
        'get_users_count'
    ]
    list_filter = ['is_active', 'is_system', 'created_at', 'permissions']

    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['permissions']

    def get_permissions_count(self, obj):
        """
        تعداد مجوزهای مرتبط با شیء (role) را برمی‌شمارد و برمی‌گرداند.
        
        پارامترها:
            obj: نمونهٔ مدل (معمولاً یک Role) که رابطهٔ `permissions` روی آن تعریف شده است.
        
        بازگشت:
            int: تعداد آیتم‌های مرتبط در relation `permissions`.
        """
        count = obj.permissions.count()
-        return format_html(
-            '<a href="{}?role__id={}">{}</a>',
-            reverse('admin:rbac_permission_changelist'),
-            obj.id,
-            count
        return format_html(
            '<a href="{}?roles__id__exact={}">{}</a>',
            reverse('admin:rbac_permission_changelist'),
            obj.id,
            count
        )


class PermissionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'resource', 'action',
        'is_active', 'created_at', 'get_roles_count'
    ]
    list_filter = ['resource', 'action', 'is_active', 'created_at', 'roles']

    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['roles']

    def get_roles_count(self, obj):
        count = obj.roles.count()
-        return format_html(
-            '<a href="{}?permissions__id={}">{}</a>',
-            reverse('admin:rbac_role_changelist'),
-            obj.id,
-            count
        return format_html(
            '<a href="{}?permissions__id__exact={}">{}</a>',
            reverse('admin:rbac_role_changelist'),
            obj.id,
            count
        )
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'name', 'display_name', 'description'
            )
        }),
        ('تنظیمات', {
            'fields': (
                'is_active', 'is_system', 'priority'
            )
        }),
        ('مجوزها', {
            'fields': ('permissions',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_permissions_count(self, obj):
        """تعداد مجوزها"""
        count = obj.permissions.count()
        return format_html(
            '<a href="{}?role__id={}">{}</a>',
            reverse('admin:rbac_permission_changelist'),
            obj.id,
            count
        )
    get_permissions_count.short_description = 'تعداد مجوزها'
    
    def get_users_count(self, obj):
        """تعداد کاربران"""
        count = obj.user_assignments.filter(is_active=True).count()
        return format_html(
            '<a href="{}?role__id={}">{}</a>',
            reverse('admin:rbac_userrole_changelist'),
            obj.id,
            count
        )
    get_users_count.short_description = 'تعداد کاربران'
    
    def get_queryset(self, request):
        """بهینه‌سازی کوئری"""
        qs = super().get_queryset(request)
        return qs.annotate(
            permissions_count=Count('permissions'),
            users_count=Count('user_assignments', filter=Q(user_assignments__is_active=True))
        )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """مدیریت مجوزها"""
    
    list_display = [
        'name', 'codename', 'resource', 'action',
        'is_active', 'get_roles_count'
    ]
    
    list_filter = ['resource', 'action', 'is_active', 'created_at']
    
    search_fields = ['name', 'codename', 'resource', 'description']
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'name', 'codename', 'description'
            )
        }),
        ('دسترسی', {
            'fields': ('resource', 'action')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )
    
    def get_roles_count(self, obj):
        """تعداد نقش‌ها"""
        count = obj.roles.count()
        return format_html(
            '<a href="{}?permissions__id={}">{}</a>',
            reverse('admin:rbac_role_changelist'),
            obj.id,
            count
        )
    get_roles_count.short_description = 'تعداد نقش‌ها'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """مدیریت نقش‌های کاربران"""
    
    list_display = [
        'get_user_name', 'get_role_name', 'assigned_by',
        'assigned_at', 'expires_at', 'is_active', 'is_expired'
    ]
    
    list_filter = [
        'is_active', 'role', 'assigned_at', 'expires_at'
    ]
    
    search_fields = [
        'user__phone_number', 'user__first_name',
        'user__last_name', 'role__name', 'role__display_name'
    ]
    
    readonly_fields = ['assigned_at', 'is_expired']
    
    autocomplete_fields = ['user', 'role', 'assigned_by']
    
    fieldsets = (
        ('کاربر و نقش', {
            'fields': ('user', 'role')
        }),
        ('اطلاعات اختصاص', {
            'fields': (
                'assigned_by', 'assigned_at', 'reason'
            )
        }),
        ('انقضا', {
            'fields': ('expires_at', 'is_expired')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def get_user_name(self, obj):
        """نمایش نام کاربر"""
        return obj.user.get_full_name()
    get_user_name.short_description = 'کاربر'
    
    def get_role_name(self, obj):
        """نمایش نام نقش"""
        return obj.role.display_name
    get_role_name.short_description = 'نقش'
    
    def is_expired(self, obj):
        """بررسی انقضا"""
        if obj.is_expired:
            return format_html(
                '<span style="color: red;">✗ منقضی شده</span>'
            )
        return format_html(
            '<span style="color: green;">✓ فعال</span>'
        )
    is_expired.short_description = 'وضعیت انقضا'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """مدیریت نشست‌های کاربران"""
    
    list_display = [
        'get_user_name', 'device_type', 'ip_address',
        'is_active', 'is_expired', 'last_activity', 'created_at'
    ]
    
    list_filter = [
        'device_type', 'is_active', 'created_at', 'expires_at'
    ]
    
    search_fields = [
        'user__phone_number', 'user__first_name',
        'user__last_name', 'ip_address', 'device_id'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'last_activity', 'is_expired'
    ]
    fieldsets = (
        ('کاربر', {
            'fields': ('user',)
        }),
        ('توکن‌ها', {
            'fields': ('id', 'token_version'),
            'classes': ('collapse',)
        }),
        ('اطلاعات دستگاه', {
            'fields': (
                'device_type', 'device_id', 'ip_address',
                'user_agent'
            )
        }),
        ('وضعیت', {
            'fields': (
                'is_active', 'expires_at', 'is_expired'
            )
        }),
        ('موقعیت', {
            'fields': ('location',),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'last_activity')
        }),
    )
    
    def get_user_name(self, obj):
        """نمایش نام کاربر"""
        return obj.user.get_full_name()
    get_user_name.short_description = 'کاربر'
    
    def is_expired(self, obj):
        """وضعیت نشست"""
        if (not obj.is_active) or obj.is_expired:
            return format_html('<span style="color: red;">✗ منقضی/غیرفعال</span>')
        return format_html('<span style="color: green;">✓ فعال</span>')
    is_expired.short_description = 'وضعیت'
    
    actions = ['terminate_sessions']
    
    def terminate_sessions(self, request, queryset):
        """خاتمه نشست‌های انتخاب شده"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} نشست با موفقیت خاتمه یافت.'
        )
    terminate_sessions.short_description = 'خاتمه نشست‌های انتخاب شده'


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    """مدیریت لاگ‌های امنیتی"""
    
    list_display = [
        'get_user_name', 'event_type', 'ip_address',
        'success', 'created_at'
    ]
    
    list_filter = [
        'event_type', 'success', 'created_at'
    ]
    
    search_fields = [
        'user__phone_number', 'user__first_name',
        'user__last_name', 'ip_address', 'error_message'
    ]
    
    readonly_fields = [
        'id', 'user', 'event_type', 'ip_address',
        'user_agent', 'success', 'error_message',
        'metadata', 'created_at'
    ]
    
    fieldsets = (
        ('اطلاعات رویداد', {
            'fields': (
                'id', 'event_type', 'success'
            )
        }),
        ('کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات فنی', {
            'fields': (
                'ip_address', 'user_agent'
            )
        }),
        ('جزئیات', {
            'fields': (
                'error_message', 'metadata'
            ),
            'classes': ('collapse',)
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )
    
    def get_user_name(self, obj):
        """نمایش نام کاربر"""
        if obj.user:
            return obj.user.get_full_name()
        return 'ناشناس'
    get_user_name.short_description = 'کاربر'
    
    def has_add_permission(self, request):
        """غیرفعال کردن افزودن دستی"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """غیرفعال کردن ویرایش"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """محدود کردن حذف به ادمین‌ها"""
        return request.user.is_superuser