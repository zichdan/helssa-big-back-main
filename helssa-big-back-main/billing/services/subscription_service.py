"""
سرویس مدیریت اشتراک‌ها
Subscription Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import timedelta
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from celery import shared_task

from .base_service import BaseService
from ..models import (
    Subscription, SubscriptionPlan, SubscriptionStatus,
    BillingCycle, PaymentMethod
)

User = get_user_model()


class SubscriptionService(BaseService):
    """سرویس مدیریت اشتراک‌ها"""
    
    def __init__(self):
        super().__init__()
        
    def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: str = 'monthly',
        payment_method: str = 'wallet',
        start_trial: bool = True,
        coupon_code: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد اشتراک جدید
        
        Args:
            user_id: شناسه کاربر
            plan_id: شناسه پلن
            billing_cycle: دوره صورت‌حساب
            payment_method: روش پرداخت
            start_trial: شروع دوره آزمایشی
            coupon_code: کد تخفیف
            
        Returns:
            Tuple[bool, Dict]: نتیجه ایجاد اشتراک
        """
        try:
            with db_transaction.atomic():
                # دریافت کاربر و پلن
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
                
                # اعتبارسنجی کاربر
                success, result = self.validate_user(user)
                if not success:
                    return success, result
                
                # بررسی اشتراک فعال
                active_subscription = self._get_active_subscription(user)
                if active_subscription:
                    return self.error_response(
                        'active_subscription_exists',
                        'شما در حال حاضر اشتراک فعال دارید'
                    )
                
                # بررسی مناسب بودن پلن
                if not plan.is_suitable_for_user(user.user_type):
                    return self.error_response(
                        'plan_not_suitable',
                        'این پلن برای نوع کاربری شما مناسب نیست'
                    )
                
                # محاسبه تاریخ‌ها
                now = timezone.now()
                trial_days = plan.trial_days if start_trial and plan.trial_days > 0 else 0
                
                if trial_days > 0:
                    start_date = now
                    trial_end_date = now + timedelta(days=trial_days)
                    end_date = trial_end_date
                    next_billing_date = trial_end_date
                    status = SubscriptionStatus.TRIAL
                else:
                    start_date = now
                    trial_end_date = None
                    
                    if billing_cycle == BillingCycle.MONTHLY:
                        end_date = now + timedelta(days=30)
                    else:  # yearly
                        end_date = now + timedelta(days=365)
                    
                    next_billing_date = end_date
                    status = SubscriptionStatus.ACTIVE
                
                # محاسبه قیمت و تخفیف
                price_info = self._calculate_subscription_price(
                    plan, billing_cycle, coupon_code
                )
                
                # پرداخت اولیه (در صورت عدم وجود trial)
                if status == SubscriptionStatus.ACTIVE:
                    payment_success = self._process_initial_payment(
                        user, price_info['final_price'], payment_method
                    )
                    if not payment_success[0]:
                        return payment_success
                
                # ایجاد اشتراک
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    status=status,
                    billing_cycle=billing_cycle,
                    trial_end_date=trial_end_date,
                    start_date=start_date,
                    end_date=end_date,
                    next_billing_date=next_billing_date,
                    payment_method=payment_method,
                    discount_percent=price_info.get('discount_percent', 0),
                    discount_amount=price_info.get('discount_amount', 0),
                    coupon_code=coupon_code
                )
                
                self.log_operation('create_subscription', user, {
                    'subscription_id': str(subscription.id),
                    'plan_id': str(plan.id),
                    'billing_cycle': billing_cycle,
                    'status': status,
                    'trial_days': trial_days
                })
                
                # ارسال ایمیل خوش‌آمد
                self._send_welcome_notification(user, plan, subscription)
                
                return self.success_response({
                    'subscription_id': str(subscription.id),
                    'plan_name': plan.name,
                    'status': status,
                    'trial_end_date': trial_end_date,
                    'next_billing_date': next_billing_date,
                    'price': price_info['final_price'],
                    'trial_days': trial_days
                }, 'اشتراک با موفقیت ایجاد شد')
                
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except SubscriptionPlan.DoesNotExist:
            return self.error_response('plan_not_found', 'پلن یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در ایجاد اشتراک: {str(e)}")
            return self.error_response(
                'subscription_creation_failed',
                'خطا در ایجاد اشتراک'
            )
    
    def upgrade_subscription(
        self,
        subscription_id: str,
        new_plan_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ارتقاء اشتراک
        
        Args:
            subscription_id: شناسه اشتراک
            new_plan_id: شناسه پلن جدید
            
        Returns:
            Tuple[bool, Dict]: نتیجه ارتقاء
        """
        try:
            with db_transaction.atomic():
                subscription = Subscription.objects.select_for_update().get(
                    id=subscription_id,
                    status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
                )
                
                new_plan = SubscriptionPlan.objects.get(
                    id=new_plan_id, 
                    is_active=True
                )
                old_plan = subscription.plan
                
                # بررسی ارتقاء
                if subscription.billing_cycle == BillingCycle.MONTHLY:
                    old_price = old_plan.monthly_price
                    new_price = new_plan.monthly_price
                else:
                    old_price = old_plan.yearly_price
                    new_price = new_plan.yearly_price
                
                if new_price <= old_price:
                    return self.error_response(
                        'invalid_upgrade',
                        'پلن انتخابی باید از پلن فعلی بالاتر باشد'
                    )
                
                # محاسبه مابه‌التفاوت
                proration_result = subscription.calculate_proration(new_plan)
                
                if proration_result > 0:
                    # پرداخت مابه‌التفاوت
                    payment_success = self._process_payment(
                        subscription.user,
                        proration_result,
                        f"ارتقاء اشتراک از {old_plan.name} به {new_plan.name}"
                    )
                    if not payment_success[0]:
                        return payment_success
                
                # به‌روزرسانی اشتراک
                subscription.plan = new_plan
                subscription.save()
                
                # ریست محدودیت‌های استفاده
                subscription.reset_usage()
                
                self.log_operation('upgrade_subscription', subscription.user, {
                    'subscription_id': str(subscription.id),
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'proration_amount': proration_result
                })
                
                return self.success_response({
                    'subscription_id': str(subscription.id),
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'proration_amount': proration_result
                }, f'اشتراک به {new_plan.name} ارتقاء یافت')
                
        except Subscription.DoesNotExist:
            return self.error_response('subscription_not_found', 'اشتراک یافت نشد')
        except SubscriptionPlan.DoesNotExist:
            return self.error_response('plan_not_found', 'پلن جدید یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در ارتقاء اشتراک: {str(e)}")
            return self.error_response(
                'upgrade_failed',
                'خطا در ارتقاء اشتراک'
            )
    
    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = None,
        immediate: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        لغو اشتراک
        
        Args:
            subscription_id: شناسه اشتراک
            reason: دلیل لغو
            immediate: لغو فوری
            
        Returns:
            Tuple[bool, Dict]: نتیجه لغو
        """
        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            )
            
            # لغو اشتراک
            subscription.cancel(reason, immediate)
            
            self.log_operation('cancel_subscription', subscription.user, {
                'subscription_id': str(subscription.id),
                'reason': reason,
                'immediate': immediate
            })
            
            # ارسال ایمیل تایید لغو
            self._send_cancellation_notification(subscription, immediate)
            
            message = 'اشتراک فوراً لغو شد' if immediate else 'اشتراک در پایان دوره لغو خواهد شد'
            
            return self.success_response({
                'subscription_id': str(subscription.id),
                'status': subscription.status,
                'cancelled_at': subscription.cancelled_at,
                'end_date': subscription.end_date
            }, message)
            
        except Subscription.DoesNotExist:
            return self.error_response('subscription_not_found', 'اشتراک یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در لغو اشتراک: {str(e)}")
            return self.error_response(
                'cancellation_failed',
                'خطا در لغو اشتراک'
            )
    
    def check_usage_limit(
        self,
        user_id: str,
        resource: str,
        amount: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بررسی محدودیت استفاده
        
        Args:
            user_id: شناسه کاربر
            resource: نام منبع
            amount: مقدار استفاده
            
        Returns:
            Tuple[bool, Dict]: نتیجه بررسی
        """
        try:
            user = User.objects.get(id=user_id)
            subscription = self._get_active_subscription(user)
            
            if not subscription:
                return self.error_response(
                    'no_active_subscription',
                    'اشتراک فعالی یافت نشد'
                )
            
            # بررسی محدودیت
            can_use = subscription.can_use_feature(resource, amount)
            
            if can_use:
                # استفاده از منبع
                subscription.use_feature(resource, amount)
                
                return self.success_response({
                    'allowed': True,
                    'current_usage': subscription.get_usage(resource),
                    'limit': subscription.get_limit(resource),
                    'remaining': subscription.get_limit(resource) - subscription.get_usage(resource)
                }, 'استفاده مجاز است')
            else:
                limit = subscription.get_limit(resource)
                current_usage = subscription.get_usage(resource)
                
                return self.error_response(
                    'usage_limit_exceeded',
                    f'از محدودیت {resource} تجاوز کرده‌اید. محدودیت: {limit}, استفاده فعلی: {current_usage}',
                    {
                        'resource': resource,
                        'limit': limit,
                        'current_usage': current_usage,
                        'requested_amount': amount
                    }
                )
                
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در بررسی محدودیت: {str(e)}")
            return self.error_response(
                'usage_check_failed',
                'خطا در بررسی محدودیت استفاده'
            )
    
    def get_subscription_info(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت اطلاعات اشتراک کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            Tuple[bool, Dict]: اطلاعات اشتراک
        """
        try:
            user = User.objects.get(id=user_id)
            subscription = self._get_active_subscription(user)
            
            if not subscription:
                return self.error_response(
                    'no_active_subscription',
                    'اشتراک فعالی یافت نشد'
                )
            
            # اطلاعات اشتراک
            subscription_info = {
                'subscription_id': str(subscription.id),
                'plan': {
                    'id': str(subscription.plan.id),
                    'name': subscription.plan.name,
                    'type': subscription.plan.type,
                    'features': subscription.plan.features,
                    'limits': subscription.plan.limits
                },
                'status': subscription.status,
                'status_display': subscription.get_status_display(),
                'billing_cycle': subscription.billing_cycle,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'next_billing_date': subscription.next_billing_date,
                'auto_renew': subscription.auto_renew,
                'days_remaining': subscription.days_remaining,
                'is_in_trial': subscription.is_in_trial,
                'trial_end_date': subscription.trial_end_date,
                'usage_data': subscription.usage_data,
                'effective_price': subscription.effective_price,
                'discount_percent': subscription.discount_percent,
                'discount_amount': subscription.discount_amount,
                'coupon_code': subscription.coupon_code
            }
            
            # محاسبه آمار استفاده
            usage_stats = {}
            for feature, limit in subscription.plan.limits.items():
                current_usage = subscription.get_usage(feature)
                usage_stats[feature] = {
                    'current': current_usage,
                    'limit': limit,
                    'remaining': limit - current_usage if limit != -1 else -1,
                    'percentage': (current_usage / limit * 100) if limit > 0 else 0
                }
            
            subscription_info['usage_stats'] = usage_stats
            
            return self.success_response(subscription_info)
            
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در دریافت اطلاعات اشتراک: {str(e)}")
            return self.error_response(
                'subscription_info_failed',
                'خطا در دریافت اطلاعات اشتراک'
            )
    
    def renew_subscription(self, subscription_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        تمدید اشتراک
        
        Args:
            subscription_id: شناسه اشتراک
            
        Returns:
            Tuple[bool, Dict]: نتیجه تمدید
        """
        try:
            with db_transaction.atomic():
                subscription = Subscription.objects.select_for_update().get(
                    id=subscription_id
                )
                
                # بررسی قابلیت تمدید
                if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]:
                    return self.error_response(
                        'renewal_not_allowed',
                        'این اشتراک قابل تمدید نیست'
                    )
                
                # محاسبه قیمت تمدید
                renewal_price = subscription.effective_price
                
                # پردازش پرداخت
                payment_success = self._process_payment(
                    subscription.user,
                    renewal_price,
                    f"تمدید اشتراک {subscription.plan.name}"
                )
                
                if not payment_success[0]:
                    return payment_success
                
                # تمدید اشتراک
                if subscription.billing_cycle == BillingCycle.MONTHLY:
                    subscription.extend_subscription(30)
                else:
                    subscription.extend_subscription(365)
                
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.reset_usage()  # ریست آمار استفاده
                subscription.save()
                
                self.log_operation('renew_subscription', subscription.user, {
                    'subscription_id': str(subscription.id),
                    'renewal_price': renewal_price,
                    'new_end_date': subscription.end_date
                })
                
                return self.success_response({
                    'subscription_id': str(subscription.id),
                    'new_end_date': subscription.end_date,
                    'next_billing_date': subscription.next_billing_date,
                    'renewal_price': renewal_price
                }, 'اشتراک با موفقیت تمدید شد')
                
        except Subscription.DoesNotExist:
            return self.error_response('subscription_not_found', 'اشتراک یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در تمدید اشتراک: {str(e)}")
            return self.error_response(
                'renewal_failed',
                'خطا در تمدید اشتراک'
            )
    
    def _get_active_subscription(self, user: User) -> Optional[Subscription]:
        """دریافت اشتراک فعال کاربر"""
        return Subscription.objects.filter(
            user=user,
            status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]
        ).first()
    
    def _calculate_subscription_price(
        self,
        plan: SubscriptionPlan,
        billing_cycle: str,
        coupon_code: str = None
    ) -> Dict[str, Any]:
        """محاسبه قیمت اشتراک با تخفیف"""
        
        base_price = plan.calculate_price(billing_cycle)
        discount_percent = Decimal('0')
        discount_amount = Decimal('0')
        
        # اعمال کد تخفیف (در صورت وجود)
        if coupon_code:
            # TODO: پیاده‌سازی سیستم کد تخفیف
            pass
        
        final_price = base_price - discount_amount
        
        return {
            'base_price': base_price,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'final_price': final_price
        }
    
    def _process_initial_payment(
        self,
        user: User,
        amount: Decimal,
        payment_method: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """پردازش پرداخت اولیه"""
        
        if payment_method == PaymentMethod.WALLET:
            # پرداخت از کیف پول
            from .wallet_service import WalletService
            wallet_service = WalletService()
            
            return wallet_service.withdraw(
                user=user,
                amount=amount,
                description="پرداخت اشتراک",
                metadata={'payment_type': 'subscription_initial'}
            )
        else:
            # سایر روش‌های پرداخت
            # TODO: پیاده‌سازی درگاه‌های پرداخت
            return self.success_response({'payment_processed': True})
    
    def _process_payment(
        self,
        user: User,
        amount: Decimal,
        description: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """پردازش پرداخت عمومی"""
        
        from .wallet_service import WalletService
        wallet_service = WalletService()
        
        return wallet_service.withdraw(
            user=user,
            amount=amount,
            description=description,
            metadata={'payment_type': 'subscription'}
        )
    
    def _send_welcome_notification(
        self,
        user: User,
        plan: SubscriptionPlan,
        subscription: Subscription
    ):
        """ارسال پیام خوش‌آمد"""
        try:
            from .notification_service import NotificationService
            notification_service = NotificationService()
            
            notification_service.send_subscription_welcome(
                user, plan, subscription
            )
        except Exception as e:
            self.logger.warning(f"خطا در ارسال پیام خوش‌آمد: {str(e)}")
    
    def _send_cancellation_notification(
        self,
        subscription: Subscription,
        immediate: bool
    ):
        """ارسال پیام لغو اشتراک"""
        try:
            from .notification_service import NotificationService
            notification_service = NotificationService()
            
            notification_service.send_subscription_cancellation(
                subscription, immediate
            )
        except Exception as e:
            self.logger.warning(f"خطا در ارسال پیام لغو: {str(e)}")
    
    @shared_task
    def process_recurring_payments(self):
        """پردازش پرداخت‌های دوره‌ای"""
        
        try:
            # اشتراک‌هایی که باید تمدید شوند
            due_subscriptions = Subscription.objects.filter(
                status=SubscriptionStatus.ACTIVE,
                auto_renew=True,
                next_billing_date__lte=timezone.now()
            ).select_related('user', 'plan')
            
            renewed_count = 0
            failed_count = 0
            
            for subscription in due_subscriptions:
                try:
                    service = SubscriptionService()
                    success, result = service.renew_subscription(str(subscription.id))
                    
                    if success:
                        renewed_count += 1
                    else:
                        failed_count += 1
                        self._handle_payment_failure(subscription, result.get('message', ''))
                        
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"خطا در تمدید اشتراک {subscription.id}: {str(e)}")
                    self._handle_payment_failure(subscription, str(e))
            
            self.logger.info(f"Recurring payments processed: {renewed_count} renewed, {failed_count} failed")
            
            return {
                'processed': len(due_subscriptions),
                'renewed': renewed_count,
                'failed': failed_count
            }
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش پرداخت‌های دوره‌ای: {str(e)}")
            return {'error': str(e)}
    
    def _handle_payment_failure(self, subscription: Subscription, error_message: str):
        """مدیریت شکست پرداخت"""
        try:
            # تغییر وضعیت به معوق
            subscription.mark_past_due()
            
            # ارسال اعلان
            from .notification_service import NotificationService
            notification_service = NotificationService()
            
            notification_service.send_payment_failure_notification(
                subscription, error_message
            )
            
            self.log_operation('payment_failure', subscription.user, {
                'subscription_id': str(subscription.id),
                'error': error_message
            })
            
        except Exception as e:
            self.logger.error(f"خطا در مدیریت شکست پرداخت: {str(e)}")