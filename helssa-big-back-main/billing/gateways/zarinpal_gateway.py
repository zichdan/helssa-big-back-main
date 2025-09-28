"""
درگاه پرداخت زرین‌پال
ZarinPal Payment Gateway
"""

import requests
from typing import Dict, Optional
from .base_gateway import BasePaymentGateway, PaymentGatewayError, PaymentVerificationError


class ZarinPalGateway(BasePaymentGateway):
    """درگاه پرداخت زرین‌پال"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.merchant_id = config['merchant_id']
        self.base_url = config.get('base_url', 'https://api.zarinpal.com/pg/v4')
        self.payment_url = config.get('payment_url', 'https://www.zarinpal.com/pg/StartPay')
        self.callback_url = config.get('callback_url', '')
        
    def create_payment(
        self,
        amount: int,
        order_id: str,
        callback_url: str,
        description: str = "",
        mobile: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """ایجاد پرداخت در زرین‌پال"""
        
        self.validate_amount(amount)
        
        # تبدیل ریال به تومان
        amount_toman = amount // 10
        
        # آماده‌سازی درخواست
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_toman,
            "callback_url": callback_url or self.callback_url,
            "description": description or f"پرداخت سفارش {order_id}",
            "metadata": {
                "order_id": order_id,
                "mobile": mobile,
                "email": email
            }
        }
        
        try:
            # ارسال درخواست
            response = requests.post(
                f"{self.base_url}/payment/request.json",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            self.log_request('create_payment', payload, result)
            
            # بررسی پاسخ
            if result['data']['code'] == 100:
                authority = result['data']['authority']
                return {
                    'success': True,
                    'payment_url': f"{self.payment_url}/{authority}",
                    'reference': authority,
                    'gateway': 'zarinpal'
                }
            else:
                error_message = self._get_error_message(result['data']['code'])
                raise PaymentGatewayError(f"خطا در ایجاد پرداخت: {error_message}")
                
        except requests.RequestException as e:
            self.logger.error(f"ZarinPal request error: {str(e)}")
            raise PaymentGatewayError(f"خطا در اتصال به زرین‌پال: {str(e)}")
        except Exception as e:
            self.logger.error(f"ZarinPal create payment error: {str(e)}")
            raise PaymentGatewayError(f"خطا در ایجاد پرداخت زرین‌پال: {str(e)}")
            
    def verify_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """تایید پرداخت زرین‌پال"""
        
        # آماده‌سازی درخواست
        payload = {
            "merchant_id": self.merchant_id,
            "authority": reference,
            "amount": (amount // 10) if amount else None
        }
        
        try:
            # ارسال درخواست تایید
            response = requests.post(
                f"{self.base_url}/payment/verify.json",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            self.log_request('verify_payment', payload, result)
            
            # بررسی نتیجه
            if result['data']['code'] in [100, 101]:
                return {
                    'success': True,
                    'amount': result['data']['amount'] * 10,  # تبدیل به ریال
                    'reference': reference,
                    'ref_id': result['data']['ref_id'],
                    'card_pan': result['data'].get('card_pan', 'نامشخص'),
                    'gateway': 'zarinpal'
                }
            else:
                error_message = self._get_error_message(result['data']['code'])
                raise PaymentVerificationError(error_message)
                
        except requests.RequestException as e:
            self.logger.error(f"ZarinPal verify error: {str(e)}")
            raise PaymentVerificationError(f"خطا در اتصال به زرین‌پال: {str(e)}")
        except Exception as e:
            self.logger.error(f"ZarinPal verify payment error: {str(e)}")
            raise PaymentVerificationError(f"خطا در تایید پرداخت زرین‌پال: {str(e)}")
            
    def refund_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """بازگشت وجه در زرین‌پال"""
        
        # آماده‌سازی درخواست بازگشت
        payload = {
            "merchant_id": self.merchant_id,
            "authority": reference,
            "amount": (amount // 10) if amount else None
        }
        
        try:
            # ارسال درخواست بازگشت
            response = requests.post(
                f"{self.base_url}/payment/refund.json",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            self.log_request('refund_payment', payload, result)
            
            # بررسی نتیجه
            if result['data']['code'] == 100:
                return {
                    'success': True,
                    'refund_id': result['data']['refund_id'],
                    'amount': result['data']['amount'] * 10,  # تبدیل به ریال
                    'gateway': 'zarinpal'
                }
            else:
                error_message = self._get_error_message(result['data']['code'])
                return {
                    'success': False,
                    'message': error_message,
                    'gateway': 'zarinpal'
                }
                
        except requests.RequestException as e:
            self.logger.error(f"ZarinPal refund error: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در اتصال به زرین‌پال: {str(e)}",
                'gateway': 'zarinpal'
            }
        except Exception as e:
            self.logger.error(f"ZarinPal refund payment error: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در بازگشت وجه زرین‌پال: {str(e)}",
                'gateway': 'zarinpal'
            }
    
    def _get_error_message(self, code: int) -> str:
        """دریافت پیام خطا بر اساس کد"""
        error_messages = {
            -9: 'خطای اعتبار سنجی',
            -10: 'ایستگاه پرداخت غیرفعال',
            -11: 'درخواست مورد نظر یافت نشد',
            -12: 'امکان ویرایش درخواست میسر نیست',
            -15: 'ترمینال غیرفعال',
            -16: 'سطح تایید پذیرنده پایین‌تر از سطح نقره‌ای',
            -17: 'محدودیت مبلغ ارسالی',
            -18: 'تجاوز از حد مجاز تراکنش‌های درحال انتظار',
            -33: 'مبلغ تراکنش از حد مجاز بیشتر است',
            -34: 'نشانی IP نامعتبر',
            -40: 'اجازه دسترسی به متد مربوطه وجود ندارد',
            -41: 'اطلاعات ارسال شده مربوط به AdditionalData غیرمعتبر',
            -42: 'مدت زمان معتبر طول عمر شناسه پرداخت باید بین 30 دقیقه تا 45 روز باشد',
            -50: 'مبلغ پرداخت شده با مقدار مبلغ در تایید متفاوت است',
            -51: 'پرداخت ناموفق',
            -52: 'خطای غیر منتظره',
            -53: 'اتوریتی برای این مرچنت کد نیست',
            -54: 'اتوریتی نامعتبر است',
            100: 'تراکنش با موفقیت تایید شد',
            101: 'تراکنش قبلا تایید شده است'
        }
        
        return error_messages.get(code, f'خطای ناشناخته: {code}')