"""
هماهنگ‌کننده مرکزی سیستم مالی
Financial System Central Orchestrator
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import time

from .api_ingress import BillingAPIIngressCore
from .text_processor import BillingTextProcessorCore
from .speech_processor import BillingSpeechProcessorCore

User = get_user_model()
logger = logging.getLogger(__name__)


class BillingWorkflowStatus(Enum):
    """وضعیت‌های فرآیند مالی"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_CONFIRMATION = "requires_confirmation"


@dataclass
class BillingWorkflowStep:
    """تعریف یک مرحله از فرآیند مالی"""
    name: str
    handler: Callable
    required: bool = True
    timeout: int = 30
    retry_count: int = 3
    dependencies: List[str] = None
    requires_confirmation: bool = False


@dataclass
class BillingWorkflowResult:
    """نتیجه اجرای فرآیند مالی"""
    status: BillingWorkflowStatus
    data: Dict[str, Any]
    errors: List[str]
    execution_time: float
    steps_completed: List[str]
    confirmation_required: bool = False
    confirmation_message: str = ""


class BillingOrchestrator:
    """
    هماهنگ‌کننده مرکزی فرآیندهای مالی
    مسئول مدیریت جریان کار بین هسته‌های مختلف سیستم مالی
    """
    
    def __init__(self):
        self.api_core = BillingAPIIngressCore()
        self.text_core = BillingTextProcessorCore()
        self.speech_core = BillingSpeechProcessorCore()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.workflows = self._initialize_billing_workflows()
        
    def execute_billing_workflow(
        self, 
        workflow_name: str,
        input_data: Dict[str, Any],
        user: User,
        async_mode: bool = False
    ) -> BillingWorkflowResult:
        """
        اجرای یک فرآیند مالی
        
        Args:
            workflow_name: نام فرآیند
            input_data: داده‌های ورودی
            user: کاربر درخواست‌دهنده
            async_mode: اجرای غیرهمزمان
            
        Returns:
            BillingWorkflowResult object
        """
        start_time = time.time()
        
        try:
            # بررسی وجود workflow
            if workflow_name not in self.workflows:
                raise ValueError(f"Unknown billing workflow: {workflow_name}")
            
            workflow = self.workflows[workflow_name]
            
            # ایجاد context اولیه
            context = {
                'user': user,
                'input_data': input_data,
                'workflow_name': workflow_name,
                'results': {},
                'errors': [],
                'ip_address': input_data.get('ip_address'),
                'user_agent': input_data.get('user_agent')
            }
            
            # اجرای workflow
            return self._execute_sync_billing_workflow(workflow, context, start_time)
                
        except Exception as e:
            self.logger.error(f"Billing workflow execution error: {str(e)}")
            return BillingWorkflowResult(
                status=BillingWorkflowStatus.FAILED,
                data={},
                errors=[str(e)],
                execution_time=time.time() - start_time,
                steps_completed=[]
            )
    
    def _execute_sync_billing_workflow(
        self, 
        workflow: List[BillingWorkflowStep],
        context: Dict[str, Any],
        start_time: float
    ) -> BillingWorkflowResult:
        """اجرای همزمان فرآیند مالی"""
        steps_completed = []
        confirmation_required = False
        confirmation_message = ""
        
        try:
            with transaction.atomic():
                for step in workflow:
                    # بررسی وابستگی‌ها
                    if not self._check_dependencies(step, steps_completed):
                        if step.required:
                            raise Exception(f"Dependencies not met for {step.name}")
                        continue
                    
                    # اجرای مرحله
                    try:
                        self.logger.info(f"Executing billing step: {step.name}")
                        result = self._execute_step_with_retry(step, context)
                        context['results'][step.name] = result
                        steps_completed.append(step.name)
                        
                        # بررسی نیاز به تأیید
                        if step.requires_confirmation and result.get('needs_confirmation'):
                            confirmation_required = True
                            confirmation_message = result.get('confirmation_message', '')
                            break
                        
                    except Exception as e:
                        self.logger.error(f"Billing step {step.name} failed: {str(e)}")
                        context['errors'].append(f"{step.name}: {str(e)}")
                        
                        if step.required:
                            raise
            
            # تعیین وضعیت نهایی
            if confirmation_required:
                status = BillingWorkflowStatus.REQUIRES_CONFIRMATION
            elif context['errors']:
                status = BillingWorkflowStatus.COMPLETED  # با خطاهای غیرحیاتی
            else:
                status = BillingWorkflowStatus.COMPLETED
            
            return BillingWorkflowResult(
                status=status,
                data=context['results'],
                errors=context['errors'],
                execution_time=time.time() - start_time,
                steps_completed=steps_completed,
                confirmation_required=confirmation_required,
                confirmation_message=confirmation_message
            )
            
        except Exception as e:
            return BillingWorkflowResult(
                status=BillingWorkflowStatus.FAILED,
                data=context['results'],
                errors=context['errors'] + [str(e)],
                execution_time=time.time() - start_time,
                steps_completed=steps_completed
            )
    
    def _execute_step_with_retry(
        self, 
        step: BillingWorkflowStep,
        context: Dict[str, Any]
    ) -> Any:
        """اجرای یک مرحله با قابلیت retry"""
        last_error = None
        
        for attempt in range(step.retry_count):
            try:
                # اجرا با timeout
                future = self.executor.submit(step.handler, context)
                result = future.result(timeout=step.timeout)
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Billing step {step.name} attempt {attempt + 1} failed: {str(e)}"
                )
                
                if attempt < step.retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error
    
    def _check_dependencies(
        self, 
        step: BillingWorkflowStep,
        completed_steps: List[str]
    ) -> bool:
        """بررسی وابستگی‌های یک مرحله"""
        if not step.dependencies:
            return True
        
        return all(dep in completed_steps for dep in step.dependencies)
    
    def _initialize_billing_workflows(self) -> Dict[str, List[BillingWorkflowStep]]:
        """تعریف فرآیندهای مالی"""
        workflows = {
            # فرآیند پرداخت
            'payment_process': [
                BillingWorkflowStep(
                    name='validate_payment_request',
                    handler=self._validate_payment_request
                ),
                BillingWorkflowStep(
                    name='check_rate_limits',
                    handler=self._check_payment_rate_limits
                ),
                BillingWorkflowStep(
                    name='validate_user_funds',
                    handler=self._validate_user_funds,
                    dependencies=['validate_payment_request']
                ),
                BillingWorkflowStep(
                    name='create_payment_transaction',
                    handler=self._create_payment_transaction,
                    dependencies=['validate_user_funds'],
                    requires_confirmation=True
                ),
                BillingWorkflowStep(
                    name='process_gateway_payment',
                    handler=self._process_gateway_payment,
                    dependencies=['create_payment_transaction'],
                    timeout=60
                ),
                BillingWorkflowStep(
                    name='update_user_balance',
                    handler=self._update_user_balance,
                    dependencies=['process_gateway_payment']
                ),
                BillingWorkflowStep(
                    name='send_payment_notification',
                    handler=self._send_payment_notification,
                    dependencies=['update_user_balance'],
                    required=False
                ),
            ],
            
            # فرآیند اشتراک
            'subscription_process': [
                BillingWorkflowStep(
                    name='validate_subscription_request',
                    handler=self._validate_subscription_request
                ),
                BillingWorkflowStep(
                    name='check_existing_subscription',
                    handler=self._check_existing_subscription,
                    dependencies=['validate_subscription_request']
                ),
                BillingWorkflowStep(
                    name='calculate_subscription_price',
                    handler=self._calculate_subscription_price,
                    dependencies=['check_existing_subscription']
                ),
                BillingWorkflowStep(
                    name='create_subscription',
                    handler=self._create_subscription,
                    dependencies=['calculate_subscription_price']
                ),
                BillingWorkflowStep(
                    name='process_subscription_payment',
                    handler=self._process_subscription_payment,
                    dependencies=['create_subscription']
                ),
                BillingWorkflowStep(
                    name='activate_subscription',
                    handler=self._activate_subscription,
                    dependencies=['process_subscription_payment']
                ),
            ],
            
            # فرآیند انتقال وجه
            'transfer_process': [
                BillingWorkflowStep(
                    name='validate_transfer_request',
                    handler=self._validate_transfer_request
                ),
                BillingWorkflowStep(
                    name='check_sender_balance',
                    handler=self._check_sender_balance,
                    dependencies=['validate_transfer_request']
                ),
                BillingWorkflowStep(
                    name='validate_recipient',
                    handler=self._validate_recipient,
                    dependencies=['validate_transfer_request']
                ),
                BillingWorkflowStep(
                    name='calculate_transfer_fees',
                    handler=self._calculate_transfer_fees,
                    dependencies=['check_sender_balance', 'validate_recipient']
                ),
                BillingWorkflowStep(
                    name='execute_transfer',
                    handler=self._execute_transfer,
                    dependencies=['calculate_transfer_fees'],
                    requires_confirmation=True
                ),
                BillingWorkflowStep(
                    name='notify_transfer_parties',
                    handler=self._notify_transfer_parties,
                    dependencies=['execute_transfer'],
                    required=False
                ),
            ],
            
            # فرآیند برداشت
            'withdrawal_process': [
                BillingWorkflowStep(
                    name='validate_withdrawal_request',
                    handler=self._validate_withdrawal_request
                ),
                BillingWorkflowStep(
                    name='check_withdrawal_limits',
                    handler=self._check_withdrawal_limits,
                    dependencies=['validate_withdrawal_request']
                ),
                BillingWorkflowStep(
                    name='verify_user_identity',
                    handler=self._verify_user_identity,
                    dependencies=['check_withdrawal_limits']
                ),
                BillingWorkflowStep(
                    name='process_withdrawal',
                    handler=self._process_withdrawal,
                    dependencies=['verify_user_identity'],
                    timeout=120
                ),
                BillingWorkflowStep(
                    name='update_withdrawal_limits',
                    handler=self._update_withdrawal_limits,
                    dependencies=['process_withdrawal']
                ),
            ],
            
            # فرآیند پردازش صوتی
            'voice_payment_process': [
                BillingWorkflowStep(
                    name='transcribe_voice_command',
                    handler=self._transcribe_voice_command,
                    timeout=60
                ),
                BillingWorkflowStep(
                    name='analyze_voice_command',
                    handler=self._analyze_voice_command,
                    dependencies=['transcribe_voice_command']
                ),
                BillingWorkflowStep(
                    name='validate_voice_payment',
                    handler=self._validate_voice_payment,
                    dependencies=['analyze_voice_command']
                ),
                BillingWorkflowStep(
                    name='confirm_voice_payment',
                    handler=self._confirm_voice_payment,
                    dependencies=['validate_voice_payment'],
                    requires_confirmation=True
                ),
            ],
        }
        
        return workflows
    
    # Handler methods for billing workflow steps
    
    def _validate_payment_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی درخواست پرداخت"""
        user = context['user']
        input_data = context['input_data']
        
        amount = Decimal(str(input_data.get('amount', 0)))
        
        success, result = self.api_core.validate_payment_request(
            user, amount, input_data
        )
        
        if not success:
            raise Exception(result.get('message', 'Payment validation failed'))
        
        return {'validated': True, 'amount': amount}
    
    def _check_payment_rate_limits(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی محدودیت‌های نرخ پرداخت"""
        user = context['user']
        ip_address = context.get('ip_address')
        
        allowed, result = self.api_core.check_rate_limit(
            user, 'payment', ip_address
        )
        
        if not allowed:
            raise Exception(result.get('message', 'Rate limit exceeded'))
        
        return {'rate_limit_ok': True}
    
    def _validate_user_funds(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی موجودی کاربر"""
        user = context['user']
        amount = context['results']['validate_payment_request']['amount']
        
        if hasattr(user, 'wallet') and user.wallet.has_sufficient_balance(amount):
            return {'sufficient_funds': True}
        else:
            return {
                'sufficient_funds': False,
                'needs_topup': True,
                'required_amount': amount
            }
    
    def _create_payment_transaction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد تراکنش پرداخت"""
        from ..services.transaction_service import TransactionService
        
        user = context['user']
        input_data = context['input_data']
        amount = context['results']['validate_payment_request']['amount']
        
        transaction_service = TransactionService()
        
        # بررسی نیاز به تأیید
        needs_confirmation = amount > 1000000  # بیش از 1 میلیون ریال
        
        if needs_confirmation:
            return {
                'needs_confirmation': True,
                'confirmation_message': f"آیا مایل هستید مبلغ {amount:,} ریال پرداخت شود؟",
                'transaction_prepared': True
            }
        
        # ایجاد تراکنش
        transaction = transaction_service.create_transaction(
            wallet=user.wallet,
            amount=-amount,  # منفی برای پرداخت
            type='payment',
            description=input_data.get('description', ''),
            metadata=input_data.get('metadata', {})
        )
        
        return {'transaction': transaction, 'transaction_id': str(transaction.id)}
    
    def _process_gateway_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """پردازش پرداخت از طریق درگاه"""
        # شبیه‌سازی پردازش درگاه
        return {
            'gateway_result': 'success',
            'gateway_reference': 'GW123456789',
            'processing_time': 2.5
        }
    
    def _update_user_balance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """به‌روزرسانی موجودی کاربر"""
        user = context['user']
        amount = context['results']['validate_payment_request']['amount']
        
        # به‌روزرسانی موجودی
        user.wallet.withdraw(amount, "Payment processed")
        
        return {
            'balance_updated': True,
            'new_balance': user.wallet.balance
        }
    
    def _send_payment_notification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ارسال اعلان پرداخت"""
        # شبیه‌سازی ارسال اعلان
        return {'notification_sent': True}
    
    def _validate_subscription_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی درخواست اشتراک"""
        user = context['user']
        input_data = context['input_data']
        
        plan_id = input_data.get('plan_id')
        billing_cycle = input_data.get('billing_cycle', 'monthly')
        
        success, result = self.api_core.validate_subscription_request(
            user, plan_id, billing_cycle
        )
        
        if not success:
            raise Exception(result.get('message', 'Subscription validation failed'))
        
        return {
            'validated': True,
            'plan': result['plan'],
            'billing_cycle': billing_cycle
        }
    
    def _check_existing_subscription(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی اشتراک موجود"""
        from ..models import Subscription
        
        user = context['user']
        
        active_subscription = Subscription.objects.filter(
            user=user,
            status__in=['trial', 'active']
        ).first()
        
        return {
            'has_active_subscription': bool(active_subscription),
            'current_subscription': active_subscription
        }
    
    def _calculate_subscription_price(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت اشتراک"""
        plan = context['results']['validate_subscription_request']['plan']
        billing_cycle = context['results']['validate_subscription_request']['billing_cycle']
        
        price = plan.calculate_price(billing_cycle)
        
        return {
            'price': price,
            'billing_cycle': billing_cycle,
            'plan_name': plan.name
        }
    
    def _create_subscription(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد اشتراک"""
        from ..services.subscription_service import SubscriptionService
        
        user = context['user']
        plan = context['results']['validate_subscription_request']['plan']
        billing_cycle = context['results']['validate_subscription_request']['billing_cycle']
        
        subscription_service = SubscriptionService()
        subscription = subscription_service.create_subscription(
            user_id=str(user.id),
            plan_id=str(plan.id),
            billing_cycle=billing_cycle
        )
        
        return {
            'subscription': subscription,
            'subscription_id': str(subscription.id)
        }
    
    def _process_subscription_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """پردازش پرداخت اشتراک"""
        # شبیه‌سازی پردازش پرداخت
        return {'payment_processed': True}
    
    def _activate_subscription(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """فعال‌سازی اشتراک"""
        subscription = context['results']['create_subscription']['subscription']
        
        # فعال‌سازی اشتراک
        subscription.status = 'active'
        subscription.save()
        
        return {'subscription_activated': True}
    
    # Transfer workflow handlers
    def _validate_transfer_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی درخواست انتقال"""
        input_data = context['input_data']
        
        required_fields = ['recipient', 'amount']
        for field in required_fields:
            if field not in input_data:
                raise Exception(f"Field '{field}' is required for transfer")
        
        return {'validated': True}
    
    def _check_sender_balance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی موجودی فرستنده"""
        user = context['user']
        amount = Decimal(str(context['input_data']['amount']))
        
        if user.wallet.has_sufficient_balance(amount):
            return {'sufficient_balance': True}
        else:
            raise Exception("موجودی کافی نیست")
    
    def _validate_recipient(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی گیرنده"""
        recipient_id = context['input_data']['recipient']
        
        try:
            recipient = User.objects.get(id=recipient_id)
            return {'recipient': recipient, 'recipient_valid': True}
        except User.DoesNotExist:
            raise Exception("گیرنده یافت نشد")
    
    def _calculate_transfer_fees(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه کارمزد انتقال"""
        amount = Decimal(str(context['input_data']['amount']))
        
        # کارمزد 0.5 درصد
        fee = amount * Decimal('0.005')
        total_amount = amount + fee
        
        return {
            'transfer_amount': amount,
            'fee': fee,
            'total_amount': total_amount
        }
    
    def _execute_transfer(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اجرای انتقال وجه"""
        from ..services.wallet_service import WalletService
        
        user = context['user']
        recipient = context['results']['validate_recipient']['recipient']
        total_amount = context['results']['calculate_transfer_fees']['total_amount']
        
        wallet_service = WalletService()
        
        # نیاز به تأیید برای مبالغ بالا
        if total_amount > 500000:  # بیش از 500 هزار ریال
            return {
                'needs_confirmation': True,
                'confirmation_message': f"آیا مایل هستید مبلغ {total_amount:,} ریال انتقال یابد؟"
            }
        
        # اجرای انتقال
        result = wallet_service.transfer(
            from_wallet_id=str(user.wallet.id),
            to_wallet_id=str(recipient.wallet.id),
            amount=total_amount
        )
        
        return {'transfer_executed': True, 'transactions': result}
    
    def _notify_transfer_parties(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعلان به طرفین انتقال"""
        return {'notifications_sent': True}
    
    # Withdrawal workflow handlers
    def _validate_withdrawal_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی درخواست برداشت"""
        user = context['user']
        amount = Decimal(str(context['input_data']['amount']))
        
        success, result = self.api_core.validate_wallet_operation(
            user, 'withdraw', amount
        )
        
        if not success:
            raise Exception(result.get('message', 'Withdrawal validation failed'))
        
        return {'validated': True, 'amount': amount}
    
    def _check_withdrawal_limits(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی محدودیت‌های برداشت"""
        # شبیه‌سازی بررسی محدودیت‌ها
        return {'limits_ok': True}
    
    def _verify_user_identity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تأیید هویت کاربر"""
        user = context['user']
        
        if user.is_verified:
            return {'identity_verified': True}
        else:
            raise Exception("تأیید هویت لازم است")
    
    def _process_withdrawal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """پردازش برداشت"""
        # شبیه‌سازی پردازش برداشت
        return {'withdrawal_processed': True}
    
    def _update_withdrawal_limits(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """به‌روزرسانی محدودیت‌های برداشت"""
        return {'limits_updated': True}
    
    # Voice processing workflow handlers
    def _transcribe_voice_command(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """رونویسی دستور صوتی"""
        audio_file = context['input_data'].get('audio_file')
        
        result = self.speech_core.transcribe_financial_audio(audio_file)
        
        return {
            'transcription': result['transcription'],
            'confidence': result['confidence'],
            'financial_entities': result['financial_entities']
        }
    
    def _analyze_voice_command(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تحلیل دستور صوتی"""
        transcription = context['results']['transcribe_voice_command']['transcription']
        
        analysis = self.speech_core.analyze_voice_payment_command(transcription)
        
        return {
            'command_analysis': analysis,
            'command_type': analysis.get('command_type'),
            'amount': analysis.get('amount'),
            'confidence': analysis.get('confidence')
        }
    
    def _validate_voice_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی پرداخت صوتی"""
        analysis = context['results']['analyze_voice_command']['command_analysis']
        
        if analysis.get('confidence', 0) < 0.7:
            raise Exception("اعتماد کافی برای دستور صوتی وجود ندارد")
        
        return {'voice_payment_valid': True}
    
    def _confirm_voice_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تأیید پرداخت صوتی"""
        analysis = context['results']['analyze_voice_command']['command_analysis']
        
        confirmation_text = self.speech_core.generate_voice_confirmation(analysis)
        
        return {
            'needs_confirmation': True,
            'confirmation_message': confirmation_text,
            'voice_command_ready': True
        }