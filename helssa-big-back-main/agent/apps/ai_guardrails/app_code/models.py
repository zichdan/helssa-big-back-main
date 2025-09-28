"""
مدل‌های اپلیکیشن
Application Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from app_standards.models.base_models import BaseModel
from typing import ClassVar
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class GuardrailPolicy(BaseModel):
    """
    سیاست‌های گاردریل برای اعمال محدودیت‌ها و قوانین ایمنی محتوای AI
    """

    ENFORCEMENT_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("block", "مسدودسازی"),
        ("warn", "هشدار"),
        ("log", "ثبت فقط")
    ]

    APPLY_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("input", "ورودی"),
        ("output", "خروجی"),
        ("both", "هردو")
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name="نام سیاست")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    enforcement_mode = models.CharField(
        max_length=10,
        choices=ENFORCEMENT_CHOICES,
        default="warn",
        verbose_name="حالت اعمال"
    )
    applies_to = models.CharField(
        max_length=10,
        choices=APPLY_CHOICES,
        default="both",
        verbose_name="حوزه اعمال"
    )
    priority = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0)],
        verbose_name="اولویت",
    )
    conditions = models.JSONField(default=dict, blank=True, verbose_name="شرایط")

    class Meta:
        verbose_name = "سیاست گاردریل"
        verbose_name_plural = "سیاست‌های گاردریل"
        ordering = ["priority", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "applies_to", "priority"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.enforcement_mode})"

    def clean(self):
        """
        اعتبارسنجی داده‌های conditions برای تضمین صحت ساختار
        """
        from django.core.exceptions import ValidationError
        super().clean()
        if not isinstance(self.conditions, dict):
            raise ValidationError("Conditions must be a dictionary.")

        severity_min = self.conditions.get('severity_min')
        if severity_min is not None:
            if not isinstance(severity_min, int):
                raise ValidationError({'conditions': "severity_min must be an integer."})
            if not (0 <= severity_min <= 100):
                raise ValidationError({'conditions': "severity_min must be between 0 and 100."})


class RedFlagRule(BaseModel):
    """
    قوانین رد-فلگ برای شناسایی الگوهای خطرناک (اورژانس، توصیه درمانی، PII و ...)
    """

    PATTERN_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("keyword", "کلمه کلیدی"),
        ("regex", "عبارت منظم"),
    ]

    CATEGORY_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("emergency", "اورژانسی"),
        ("medical_advice", "توصیه پزشکی"),
        ("pii", "اطلاعات شناسایی فردی"),
        ("safety", "ایمنی"),
        ("other", "سایر")
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name="نام قانون")
    pattern_type = models.CharField(max_length=10, choices=PATTERN_CHOICES, verbose_name="نوع الگو")
    pattern = models.TextField(verbose_name="الگو")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="other", verbose_name="دسته‌بندی")
    severity = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="شدت (0-100)",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")

    class Meta:
        verbose_name = "قانون رد-فلگ"
        verbose_name_plural = "قوانین رد-فلگ"
        ordering = ["-severity", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.category}]"


class PolicyViolationLog(BaseModel):
    """
    لاگ نقض سیاست‌ها هنگام ارزیابی ورودی/خروجی
    """

    ACTION_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("blocked", "مسدود شد"),
        ("warned", "هشدار داده شد"),
        ("logged", "ثبت شد"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="guardrail_violations",
                             verbose_name="کاربر")
    policy = models.ForeignKey(GuardrailPolicy, on_delete=models.SET_NULL, null=True, blank=True, related_name="violations",
                               verbose_name="سیاست")
    rule = models.ForeignKey(RedFlagRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="violations",
                             verbose_name="قانون")

    content_snapshot = models.TextField(verbose_name="نمونه محتوا")
    direction = models.CharField(max_length=10, choices=[("input", "ورودی"), ("output", "خروجی")],
                                 verbose_name="جهت")
    context = models.JSONField(default=dict, blank=True, verbose_name="زمینه")

    action_taken = models.CharField(max_length=10, choices=ACTION_CHOICES, default="logged", verbose_name="اقدام")
    risk_score = models.IntegerField(default=0, verbose_name="امتیاز ریسک")
    matched_spans = models.JSONField(default=list, blank=True, verbose_name="ناحیه‌های منطبق")

    request_path = models.CharField(max_length=255, blank=True, verbose_name="مسیر درخواست")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    class Meta:
        verbose_name = "گزارش نقض سیاست"
        verbose_name_plural = "گزارش‌های نقض سیاست"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["policy"]),
            models.Index(fields=["rule"]),
        ]

    def __str__(self) -> str:
        return f"violation:{self.id} action={self.action_taken} risk={self.risk_score}"

