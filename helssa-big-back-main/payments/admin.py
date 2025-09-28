"""
پنل ادمین اپلیکیشن پرداخت
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from decimal import Decimal
import jdatetime

from .models import (
    Payment, PaymentMethod, Transaction,
    Wallet, WalletTransaction, PaymentGateway
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    مدیریت پرداخت‌ها در پنل ادمین
    """
    list_display = [
        'payment_id_display', 'user_display', 'user_type',
        'payment_type', 'amount_display', 'status_badge',
        'tracking_code', 'jalali_created'
    ]
    list_filter = [
        'status', 'user_type', 'payment_type',
        'created_at', 'payment_method__method_type'
    ]
    search_fields = [
        'payment_id', 'tracking_code', 'user__username',
        'user__first_name', 'user__last_name',
        'description'
    ]
    readonly_fields = [
        'payment_id', 'tracking_code', 'created_at',
        'updated_at', 'paid_at', 'failed_at', 'refunded_at',
        'jalali_created', 'jalali_updated'
    ]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'payment_id', 'user', 'user_type',
                'payment_type', 'amount', 'status',
                'tracking_code'
            )
        }),
        ('جزئیات', {
            'fields': (
                'description', 'payment_method',
                'appointment_id', 'doctor_id'
            )
        }),
        ('اطلاعات فنی', {
            'fields': (
                'gateway_response', 'metadata'
            ),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': (
                'created_at', 'jalali_created',
                'updated_at', 'jalali_updated',
                'paid_at', 'failed_at', 'refunded_at'
            )
        })
    )
    
    def payment_id_display(self, obj):
        """نمایش شناسه پرداخت با لینک"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:payments_payment_change', args=[obj.payment_id]),
            str(obj.payment_id)[:8] + '...'
        )
    payment_id_display.short_description = 'شناسه'
    
    def user_display(self, obj):
        """نمایش نام کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            return obj.user.get_full_name() or obj.user.username
        return str(obj.user)
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'
    
    def amount_display(self, obj):
        """نمایش مبلغ با فرمت مناسب"""
        return format_html(
            '<span style="direction: ltr; display: inline-block;">{:,} ریال</span>',
            int(obj.amount)
        )
    amount_display.short_description = 'مبلغ'
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """نمایش وضعیت با رنگ مناسب"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'success': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'purple',
            'partially_refunded': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    status_badge.admin_order_field = 'status'
    
    def jalali_created(self, obj):
        """تاریخ ایجاد شمسی"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')
    jalali_created.short_description = 'تاریخ ایجاد'
    jalali_created.admin_order_field = 'created_at'
    
    def jalali_updated(self, obj):
        """تاریخ بروزرسانی شمسی"""
        jalali = jdatetime.datetime.fromgregorian(datetime=obj.updated_at)
        return jalali.strftime('%Y/%m/%d %H:%M')
    jalali_updated.short_description = 'آخرین بروزرسانی'
    
    def get_queryset(self, request):
        """بهینه‌سازی query"""
        return super().get_queryset(request).select_related(
            'user', 'payment_method'
        ).prefetch_related('transactions')
    
    class Media:
        css = {
            'all': ('admin/css/payments_admin.css',)
        }


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """
    مدیریت روش‌های پرداخت
    """
    list_display = [
        'title', 'user_display', 'method_type',
        'is_default', 'is_active', 'jalali_created'
    ]
    list_filter = ['method_type', 'is_default', 'is_active', 'created_at']
    search_fields = ['title', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def user_display(self, obj):
        """نمایش نام کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            return obj.user.get_full_name() or obj.user.username
        return str(obj.user)
    user_display.short_description = 'کاربر'
    
    def jalali_created(self, obj):
        """تاریخ ایجاد شمسی"""
        return obj.get_jalali_created().strftime('%Y/%m/%d')
    jalali_created.short_description = 'تاریخ ایجاد'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    مدیریت تراکنش‌ها
    """
    list_display = [
        'transaction_id', 'payment_link', 'transaction_type',
        'amount_display', 'status_badge', 'reference_number',
        'jalali_created'
    ]
    list_filter = ['transaction_type', 'status', 'gateway_name', 'created_at']
    search_fields = ['transaction_id', 'reference_number', 'payment__tracking_code']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    
    def payment_link(self, obj):
        """لینک به پرداخت مرتبط"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:payments_payment_change', args=[obj.payment.payment_id]),
            obj.payment.tracking_code
        )
    payment_link.short_description = 'پرداخت'
    
    def amount_display(self, obj):
        """نمایش مبلغ"""
        return format_html(
            '<span style="direction: ltr; display: inline-block;">{:,}</span>',
            int(obj.amount)
        )
    amount_display.short_description = 'مبلغ'
    
    def status_badge(self, obj):
        """نمایش وضعیت"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'reversed': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def jalali_created(self, obj):
        """تاریخ شمسی"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')
    jalali_created.short_description = 'تاریخ'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    مدیریت کیف پول‌ها
    """
    list_display = [
        'user_display', 'balance_display', 'blocked_display',
        'available_display', 'last_transaction_jalali', 'is_active'
    ]
    list_filter = ['is_active', 'last_transaction_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'balance', 'blocked_balance', 'available_balance',
        'created_at', 'updated_at', 'last_transaction_at'
    ]
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            return obj.user.get_full_name() or obj.user.username
        return str(obj.user)
    user_display.short_description = 'کاربر'
    
    def balance_display(self, obj):
        """نمایش موجودی"""
        return format_html(
            '<span style="color: green;">{:,}</span>',
            int(obj.balance)
        )
    balance_display.short_description = 'موجودی'
    
    def blocked_display(self, obj):
        """نمایش موجودی مسدود"""
        if obj.blocked_balance > 0:
            return format_html(
                '<span style="color: orange;">{:,}</span>',
                int(obj.blocked_balance)
            )
        return '0'
    blocked_display.short_description = 'مسدود شده'
    
    def available_display(self, obj):
        """نمایش موجودی قابل استفاده"""
        return format_html(
            '<span style="color: blue;">{:,}</span>',
            int(obj.available_balance)
        )
    available_display.short_description = 'قابل استفاده'
    
    def last_transaction_jalali(self, obj):
        """آخرین تراکنش"""
        if obj.last_transaction_at:
            jalali = jdatetime.datetime.fromgregorian(
                datetime=obj.last_transaction_at
            )
            return jalali.strftime('%Y/%m/%d')
        return '-'
    last_transaction_jalali.short_description = 'آخرین تراکنش'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """
    مدیریت تراکنش‌های کیف پول
    """
    list_display = [
        'id', 'wallet_user', 'transaction_type', 'amount_display',
        'balance_change', 'jalali_created'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = [
        'wallet__user__username', 'description',
        'payment__tracking_code'
    ]
    readonly_fields = [
        'wallet', 'balance_before', 'balance_after',
        'created_at', 'updated_at'
    ]
    
    def wallet_user(self, obj):
        """نمایش کاربر کیف پول"""
        return obj.wallet.user
    wallet_user.short_description = 'کاربر'
    
    def amount_display(self, obj):
        """نمایش مبلغ با رنگ"""
        if obj.transaction_type in ['deposit', 'refund']:
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = '-'
        return format_html(
            '<span style="color: {};">{}{:,}</span>',
            color, sign, int(abs(obj.amount))
        )
    amount_display.short_description = 'مبلغ'
    
    def balance_change(self, obj):
        """تغییرات موجودی"""
        return format_html(
            '{:,} ← {:,}',
            int(obj.balance_before),
            int(obj.balance_after)
        )
    balance_change.short_description = 'تغییر موجودی'
    
    def jalali_created(self, obj):
        """تاریخ شمسی"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')
    jalali_created.short_description = 'تاریخ'


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    """
    مدیریت درگاه‌های پرداخت
    """
    list_display = [
        'display_name', 'name', 'gateway_type',
        'is_active', 'priority'
    ]
    list_filter = ['gateway_type', 'is_active']
    search_fields = ['name', 'display_name']
    ordering = ['-priority', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'display_name', 'gateway_type')
        }),
        ('تنظیمات', {
            'fields': ('configuration', 'priority', 'is_active')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']