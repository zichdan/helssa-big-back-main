"""
سرویس یکپارچه کاوه‌نگار برای ارسال پیامک
Kavenegar Service for SMS Sending
"""

from kavenegar import KavenegarAPI, APIException, HTTPException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class KavenegarService:
    """
    سرویس ارسال پیامک با کاوه‌نگار
    """
    
    def __init__(self):
        """

        مقداردهی اولیه سرویس Kavenegar: کلید API را از تنظیمات می‌خواند، کلاینت Kavenegar را مقداردهی می‌کند و مقادیر اختیاری sender و قالب OTP را تنظیم می‌نماید.
        
        اگر KAVENEGAR_API_KEY در تنظیمات یافت نشود، ValueError پرتاب می‌شود. پس از موفقیت، فیلدهای نمونه زیر مقداردهی می‌شوند:
        - self.api_key: مقدار کلید API از تنظیمات
        - self.api: نمونهٔ KavenegarAPI ساخته‌شده با کلید API
        - self.sender: مقدار اختیاری KAVENEGAR_SENDER از تنظیمات (در صورت نبود None)
        - self.otp_template: قالب OTP از KAVENEGAR_OTP_TEMPLATE یا مقدار پیش‌فرض 'verify'
       """
        self.api_key = getattr(settings, 'KAVENEGAR_API_KEY', None)
        if not self.api_key:
            raise ValueError("KAVENEGAR_API_KEY not found in settings")
        
        self.api = KavenegarAPI(self.api_key)
        self.sender = getattr(settings, 'KAVENEGAR_SENDER', None)
        self.otp_template = getattr(settings, 'KAVENEGAR_OTP_TEMPLATE', 'verify')
    
    def send_otp(self, phone_number: str, otp_code: str, template: str = None) -> dict:
        """

        ارسال یک کد یک‌بارمصرف (OTP) با استفاده از API تایید قالبیِ کاوه‌نگار.
        
        این متد یک OTP را با فراخوانی verify_lookup در Kavenegar ارسال می‌کند. اگر قالب (template) مشخص نشود، قالب پیش‌فرض سرویس استفاده می‌شود. ورودی‌ها در پارامترهای API به‌صورت receptor (شماره گیرنده)، token (کد OTP) و template ارسال می‌شوند. پاسخ موفق شامل شناسه پیام، وضعیت و متن وضعیت است. در صورت بروز خطا، خروجی یک دیکشنری با فیلدهای مربوط به خطا برمی‌گردد (بدون بالا بردن خطا).
        
        Parameters:
            phone_number (str): شماره موبایل گیرنده (قابل استفاده با فرمت محلی یا بین‌المللی؛ پیش‌نیاز فرمتر خارجی با متد format_phone_number در سطح سرویس).
            otp_code (str): کد یک‌بارمصرف که در قالب به عنوان `token` قرار می‌گیرد.
            template (str, optional): نام قالب کاوه‌نگار برای ارسال (اگر مشخص نشود از تنظیم پیش‌فرض سرویس استفاده می‌شود).
        
        Returns:
            dict: نتیجه عملیات با ساختار مشابه یکی از موارد زیر:
                - موفق: {'success': True, 'message_id': str, 'status': <int|str>, 'status_text': <str>}
                - خطا:   {'success': False, 'error': <str>, 'error_code': <int|None>?, 'error_detail': <str>}
        """
        try:
            # استفاده از template پیش‌فرض اگر مشخص نشده
            if not template:
                template = self.otp_template
            
            # ارسال با استفاده از verify API (برای OTP)
            params = {
                'receptor': phone_number,
                'token': otp_code,
                'template': template
            }
            
            # اگر token2 یا token3 نیاز است
            # params['token2'] = 'مقدار'
            # params['token3'] = 'مقدار'
            
            response = self.api.verify_lookup(params)
            
            # لاگ موفقیت
            logger.info(
                f"OTP sent successfully to {phone_number}, "
                f"message_id: {response['messageid']}"
            )
            
            return {
                'success': True,
                'message_id': str(response['messageid']),
                'status': response['status'],
                'status_text': response['statustext']
            }
            
        except APIException as e:
            # خطای API کاوه‌نگار
            logger.error(f"Kavenegar API error: {e}")
            return {
                'success': False,
                'error': 'خطا در ارسال پیامک',
                'error_code': getattr(e, 'status', None),
                'error_detail': str(e)
            }
            
        except HTTPException as e:
            # خطای HTTP
            logger.error(f"Kavenegar HTTP error: {e}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با سرور پیامک',
                'error_detail': str(e)
            }
            
        except Exception as e:
            # خطای عمومی
            logger.error(f"Unexpected error in Kavenegar service: {e}")
            return {
                'success': False,
                'error': 'خطای غیرمنتظره در ارسال پیامک',
                'error_detail': str(e)
            }
    
    def send_simple_sms(self, phone_number: str, message: str) -> dict:
        """

        ارسال یک پیامک متنی ساده (غیر OTP) به یک شماره گیرنده با استفاده از کلاینت Kavenegar.
        
        توضیحات:
            شماره ورودی باید به فرمت قابل قبول Kavenegar باشد (ترجیحاً از `KavenegarService.format_phone_number` استفاده شود).
            در صورت وجود مقدار `sender` در تنظیمات سرویس، آن مقدار به‌صورت خودکار به پارامترهای ارسال افزوده می‌شود.
        
        پارامترها:
            phone_number: شماره موبایل گیرنده (رشته) — فرمت مناسب برای Kavenegar.
            message: متن پیامک که ارسال خواهد شد.
        
        بازگشت:
            dict با ساختار زیر:
              - success (bool): وضعیت کلی عملیات؛ True در صورت موفقیت.
              - message_id (str): شناسه پیام که از Kavenegar برمی‌گردد (فقط در صورت موفقیت).
              - status: وضعیت خام برگشتی از API Kavenegar (فقط در صورت موفقیت).
              - error (str): پیام خطا به زبان فارسی (فقط در صورت شکست).
              - error_detail (str): جزئیات خطا/استثنا به صورت رشته‌ای (فقط در صورت شکست).
        
        رفتار در خطا:
            در صورت بروز استثنا، تابع استثنا را بالا نمی‌فرستد بلکه یک دیکشنری با `success: False`، `error` و `error_detail` برمی‌گرداند.
        """
        try:
            params = {
                'receptor': phone_number,
                'message': message
            }
            
            if self.sender:
                params['sender'] = self.sender
            
            response = self.api.sms_send(params)
            
            logger.info(
                f"SMS sent successfully to {phone_number}, "
                f"message_id: {response['messageid']}"
            )
            
            return {
                'success': True,
                'message_id': str(response['messageid']),
                'status': response['status']
            }
            
        except Exception as e:
            logger.error(f"Error sending simple SMS: {e}")
            return {
                'success': False,
                'error': 'خطا در ارسال پیامک',
                'error_detail': str(e)
            }
    
    def get_message_status(self, message_id: str) -> dict:
        """

        وضعیت یک پیام ارسالی از طریق Kavenegar را بازیابی می‌کند.
        
        پارامترها:
            message_id (str): شناسه پیام در سرویس Kavenegar (messageid) که برای بازیابی وضعیت لازم است.
        
        بازگشت:
            dict: نتیجه عملیات با ساختار زیر:
                - موفقیت‌آمیز:
                    {
                        'success': True,
                        'status': <کد وضعیت از API>,
                        'statustext': <متن وضعیت از API>
                    }
                - در صورت خطا:
                    {
                        'success': False,
                        'error': 'خطا در دریافت وضعیت پیام',
                        'error_detail': <جزئیات خطای قابل بررسی به صورت رشته>
                    }
        """
        try:
            response = self.api.sms_status({'messageid': message_id})
            
            return {
                'success': True,
                'status': response['status'],
                'statustext': response['statustext']
            }
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return {
                'success': False,
                'error': 'خطا در دریافت وضعیت پیام',
                'error_detail': str(e)
            }
    
    def send_voice_otp(self, phone_number: str, otp_code: str) -> dict:
        """

        ارسال کد یک‌بارمصرف از طریق تماس صوتی.
        
        تابع یک پیام صوتی تولید می‌کند که در آن ارقام OTP با فاصله از هم خوانده می‌شوند (مثلاً "1 2 3 4" برای "1234") و درخواست ایجاد تماس متنی-به-صدا (TTS) را به سرویس کاوه‌نگار ارسال می‌کند. در صورت موفقیت، شناسه پیام و وضعیت بازگشتی از API را برمی‌گرداند؛ در صورت خطا، اطلاعات خطا را در قالب دیکشنری بازمی‌گرداند.
        
        Parameters:
            phone_number (str): شماره گیرنده تماس به فرمت مورد انتظار سرویس کاوه‌نگار.
            otp_code (str): کد OTP که قرار است قرائت شود (اعداد به‌عنوان رشته).
        
        Returns:
            dict: نتیجه عملیات با یکی از ساختارهای زیر:
                - موفق:
                    {
                        'success': True,
                        'message_id': <str>,   # شناسه پیام برگشتی از API
                        'status': <any>        # وضعیت برگشتی از API
                    }
                - ناموفق:
                    {
                        'success': False,
                        'error': <str>,        # پیام خطای خلاصه (به فارسی)
                        'error_detail': <str>  # جزئیات خطا (استثنا به صورت رشته)
                    }
        """
        try:
            # تبدیل کد به متن قابل خواندن
            # مثلاً 123456 به "یک دو سه چهار پنج شش"
            spoken_code = ' '.join(otp_code)
            
            message = f"کد تأیید شما: {spoken_code}"
            
            params = {
                'receptor': phone_number,
                'message': message
            }
            
            response = self.api.call_maketts(params)
            
            logger.info(
                f"Voice OTP sent successfully to {phone_number}, "
                f"message_id: {response['messageid']}"
            )
            
            return {
                'success': True,
                'message_id': str(response['messageid']),
                'status': response['status']
            }
            
        except Exception as e:
            logger.error(f"Error sending voice OTP: {e}")
            return {
                'success': False,
                'error': 'خطا در برقراری تماس صوتی',
                'error_detail': str(e)
            }
    
    @staticmethod
    def format_phone_number(phone_number: str) -> str:
        """

        شماره تلفن را برای ارسال به کاوه‌نگار نرمال‌سازی و قالب‌بندی می‌کند.
        
        توضیحات:
        - فاصله‌ها و خط تیره‌ها را حذف می‌کند.
        - پیش‌شماره‌های بین‌المللی معمول ایران را به شکل محلی تبدیل می‌کند:
          - اگر با '+98' شروع شود، به '0' + باقی‌مانده تبدیل می‌شود.
          - اگر با '0098' شروع شود، به '0' + باقی‌مانده تبدیل می‌شود.
          - اگر با '98' شروع شود، به '0' + باقی‌مانده تبدیل می‌شود.
        - سایر رشته‌ها بدون تغییر (به جز حذف فاصله و '-') بازگردانده می‌شوند.
        
        پارامترها:
            phone_number (str): شماره ورودی (می‌تواند شامل فاصله، خط تیره یا پیش‌شماره بین‌المللی باشد).
        
        بازگشت:
            str: شماره تلفن فرمت‌شده مطابق با قالب مورد انتظار کاوه‌نگار (معمولاً با صفر اول).

        """
        # حذف فاصله‌ها و کاراکترهای اضافی
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')
        
        # حذف +98 یا 0098 از ابتدا
        if phone_number.startswith('+98'):
            phone_number = '0' + phone_number[3:]
        elif phone_number.startswith('0098'):
            phone_number = '0' + phone_number[4:]
        elif phone_number.startswith('98'):
            phone_number = '0' + phone_number[2:]
        
        return phone_number