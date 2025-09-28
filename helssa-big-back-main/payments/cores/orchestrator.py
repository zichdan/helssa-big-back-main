"""
هسته هماهنگ‌کننده مرکزی برای پرداخت‌ها
"""
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from .api_ingress import APIIngressCore
from .text_processor import TextProcessorCore
from .speech_processor import SpeechProcessorCore

logger = logging.getLogger(__name__)


class CentralOrchestrator:
    """
    هماهنگ‌کننده مرکزی بین هسته‌های مختلف پرداخت
    
    این کلاس مسئول:
    - هماهنگی بین هسته‌های مختلف
    - مدیریت فرآیند پرداخت
    - تصمیم‌گیری بر اساس نوع کاربر و درخواست
    """
    
    def __init__(self):
        self.logger = logger
        self.api_core = APIIngressCore()
        self.text_core = TextProcessorCore()
        self.speech_core = SpeechProcessorCore()
        
    def process_payment_request(
        self,
        user_type: str,
        payment_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش درخواست پرداخت بر اساس نوع کاربر
        
        Args:
            user_type: نوع کاربر (doctor/patient)
            payment_data: اطلاعات پرداخت
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            self.logger.info(
                f"Processing payment request",
                extra={
                    'user_type': user_type,
                    'payment_type': payment_data.get('type')
                }
            )
            
            # اعتبارسنجی نوع کاربر
            if user_type not in ['doctor', 'patient']:
                return False, {
                    'error': 'invalid_user_type',
                    'message': 'نوع کاربر نامعتبر است'
                }
            
            # پردازش بر اساس نوع کاربر
            if user_type == 'patient':
                return self._process_patient_payment(payment_data)
            else:
                return self._process_doctor_payment(payment_data)
                
        except Exception as e:
            self.logger.error(f"Error in payment orchestration: {str(e)}")
            return False, {
                'error': 'orchestration_failed',
                'message': 'خطا در پردازش پرداخت'
            }
    
    def _process_patient_payment(
        self, 
        payment_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش پرداخت برای بیمار
        
        Args:
            payment_data: اطلاعات پرداخت
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            payment_type = payment_data.get('type')
            
            # اعتبارسنجی نوع پرداخت برای بیمار
            valid_types = [
                'appointment', 'consultation', 'medication',
                'test', 'imaging', 'procedure'
            ]
            
            if payment_type not in valid_types:
                return False, {
                    'error': 'invalid_payment_type',
                    'message': 'نوع پرداخت برای بیمار نامعتبر است'
                }
            
            # اعتبارسنجی مبلغ
            amount_valid, amount = self.text_core.parse_amount(
                str(payment_data.get('amount', 0))
            )
            
            if not amount_valid or amount <= 0:
                return False, {
                    'error': 'invalid_amount',
                    'message': 'مبلغ پرداخت نامعتبر است'
                }
            
            # تولید توضیحات پرداخت
            description = self.text_core.generate_payment_description(
                payment_type=payment_type,
                amount=amount,
                context=payment_data.get('context', {})
            )
            
            # آماده‌سازی داده‌های پرداخت
            processed_data = {
                'type': payment_type,
                'amount': float(amount),
                'description': description,
                'user_type': 'patient',
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # افزودن اطلاعات اضافی در صورت وجود
            if 'appointment_id' in payment_data:
                processed_data['appointment_id'] = payment_data['appointment_id']
            
            if 'doctor_id' in payment_data:
                processed_data['doctor_id'] = payment_data['doctor_id']
                
            return True, processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing patient payment: {str(e)}")
            return False, {
                'error': 'patient_payment_failed',
                'message': 'خطا در پردازش پرداخت بیمار'
            }
    
    def _process_doctor_payment(
        self,
        payment_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش پرداخت برای دکتر
        
        Args:
            payment_data: اطلاعات پرداخت
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            payment_type = payment_data.get('type')
            
            # اعتبارسنجی نوع پرداخت برای دکتر
            valid_types = [
                'withdrawal', 'subscription', 'commission',
                'refund', 'adjustment'
            ]
            
            if payment_type not in valid_types:
                return False, {
                    'error': 'invalid_payment_type',
                    'message': 'نوع پرداخت برای پزشک نامعتبر است'
                }
            
            # اعتبارسنجی مبلغ
            amount_valid, amount = self.text_core.parse_amount(
                str(payment_data.get('amount', 0))
            )
            
            if not amount_valid:
                return False, {
                    'error': 'invalid_amount',
                    'message': 'مبلغ نامعتبر است'
                }
            
            # برای برداشت، بررسی موجودی
            if payment_type == 'withdrawal':
                # این بخش باید با بررسی موجودی دکتر تکمیل شود
                pass
            
            # آماده‌سازی داده‌های پرداخت
            processed_data = {
                'type': payment_type,
                'amount': float(amount),
                'user_type': 'doctor',
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # اطلاعات خاص دکتر
            if payment_type == 'withdrawal':
                if 'bank_account' not in payment_data:
                    return False, {
                        'error': 'missing_bank_account',
                        'message': 'اطلاعات حساب بانکی الزامی است'
                    }
                processed_data['bank_account'] = payment_data['bank_account']
                
            return True, processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing doctor payment: {str(e)}")
            return False, {
                'error': 'doctor_payment_failed',
                'message': 'خطا در پردازش پرداخت پزشک'
            }
    
    def generate_payment_response(
        self,
        payment_result: Dict[str, Any],
        include_audio: bool = False
    ) -> Dict[str, Any]:
        """
        تولید پاسخ کامل برای پرداخت
        
        Args:
            payment_result: نتیجه پرداخت
            include_audio: آیا اعلان صوتی هم تولید شود
            
        Returns:
            Dict: پاسخ کامل
        """
        try:
            response = {
                'status': payment_result.get('status', 'unknown'),
                'tracking_code': payment_result.get('tracking_code'),
                'amount': payment_result.get('amount'),
                'timestamp': payment_result.get('timestamp'),
                'description': payment_result.get('description')
            }
            
            # تولید رسید متنی
            if payment_result.get('status') == 'success':
                receipt_text = self.text_core.generate_receipt_text(payment_result)
                response['receipt'] = receipt_text
            
            # تولید اعلان صوتی در صورت درخواست
            if include_audio:
                audio_data = self.speech_core.generate_payment_announcement(
                    payment_status=payment_result.get('status'),
                    amount=str(payment_result.get('amount', 0))
                )
                response['audio_announcement'] = audio_data
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating payment response: {str(e)}")
            return {
                'status': 'error',
                'message': 'خطا در تولید پاسخ پرداخت'
            }
    
    def validate_payment_method(
        self,
        method: str,
        method_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        اعتبارسنجی روش پرداخت
        
        Args:
            method: روش پرداخت
            method_data: اطلاعات روش پرداخت
            
        Returns:
            Tuple[bool, Optional[str]]: (معتبر بودن، پیام خطا)
        """
        try:
            if method == 'card':
                card_number = method_data.get('card_number', '')
                return self.text_core.validate_card_number(card_number)
                
            elif method == 'wallet':
                # اعتبارسنجی کیف پول
                if 'wallet_id' not in method_data:
                    return False, "شناسه کیف پول الزامی است"
                return True, None
                
            elif method == 'online':
                # پرداخت آنلاین - نیاز به gateway
                return True, None
                
            else:
                return False, "روش پرداخت نامعتبر است"
                
        except Exception as e:
            self.logger.error(f"Error validating payment method: {str(e)}")
            return False, "خطا در اعتبارسنجی روش پرداخت"