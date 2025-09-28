"""
هسته پردازش متن برای پرداخت‌ها
"""
import logging
import re
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class TextProcessorCore:
    """
    پردازش متن‌های مربوط به پرداخت
    
    این کلاس مسئول:
    - تولید توضیحات پرداخت
    - پردازش و اعتبارسنجی ورودی‌های متنی
    - تولید رسید و گزارش‌های متنی
    """
    
    def __init__(self):
        self.logger = logger
        
    def generate_payment_description(
        self, 
        payment_type: str,
        amount: Decimal,
        context: Dict[str, Any]
    ) -> str:
        """
        تولید توضیحات پرداخت
        
        Args:
            payment_type: نوع پرداخت
            amount: مبلغ پرداخت
            context: اطلاعات تکمیلی
            
        Returns:
            str: توضیحات فرمت شده
        """
        try:
            descriptions = {
                'appointment': 'پرداخت نوبت پزشکی',
                'consultation': 'پرداخت مشاوره آنلاین',
                'medication': 'پرداخت دارو',
                'test': 'پرداخت آزمایش',
                'imaging': 'پرداخت تصویربرداری',
                'procedure': 'پرداخت عملیات پزشکی'
            }
            
            base_description = descriptions.get(payment_type, 'پرداخت خدمات پزشکی')
            
            # افزودن جزئیات بیشتر
            if payment_type == 'appointment' and 'doctor_name' in context:
                base_description += f" - دکتر {context['doctor_name']}"
            
            if 'service_name' in context:
                base_description += f" - {context['service_name']}"
                
            # افزودن مبلغ
            formatted_amount = self._format_amount(amount)
            base_description += f" - مبلغ: {formatted_amount} ریال"
            
            return base_description
            
        except Exception as e:
            self.logger.error(f"Error generating payment description: {str(e)}")
            return "پرداخت خدمات پزشکی"
    
    def _format_amount(self, amount: Decimal) -> str:
        """
        فرمت‌دهی مبلغ با جداکننده هزارگان
        
        Args:
            amount: مبلغ
            
        Returns:
            str: مبلغ فرمت شده
        """
        try:
            # تبدیل به رشته و حذف اعشار اضافی
            amount_str = str(int(amount))
            
            # افزودن جداکننده هزارگان
            formatted = ""
            for i, digit in enumerate(reversed(amount_str)):
                if i > 0 and i % 3 == 0:
                    formatted = "," + formatted
                formatted = digit + formatted
                
            return formatted
        except:
            return str(amount)
    
    def validate_card_number(self, card_number: str) -> Tuple[bool, Optional[str]]:
        """
        اعتبارسنجی شماره کارت بانکی
        
        Args:
            card_number: شماره کارت
            
        Returns:
            Tuple[bool, Optional[str]]: (معتبر بودن، پیام خطا)
        """
        try:
            # حذف فاصله‌ها و خط تیره‌ها
            card_number = re.sub(r'[\s-]', '', card_number)
            
            # بررسی طول
            if len(card_number) != 16:
                return False, "شماره کارت باید 16 رقم باشد"
            
            # بررسی عددی بودن
            if not card_number.isdigit():
                return False, "شماره کارت باید فقط شامل عدد باشد"
            
            # الگوریتم Luhn برای اعتبارسنجی
            total = 0
            for i, digit in enumerate(reversed(card_number)):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
                
            if total % 10 != 0:
                return False, "شماره کارت نامعتبر است"
                
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error validating card number: {str(e)}")
            return False, "خطا در اعتبارسنجی شماره کارت"
    
    def generate_receipt_text(self, payment_data: Dict[str, Any]) -> str:
        """
        تولید متن رسید پرداخت
        
        Args:
            payment_data: اطلاعات پرداخت
            
        Returns:
            str: متن رسید
        """
        try:
            receipt_lines = [
                "=== رسید پرداخت ===",
                f"شماره پیگیری: {payment_data.get('tracking_code', 'نامشخص')}",
                f"تاریخ: {payment_data.get('date', 'نامشخص')}",
                f"ساعت: {payment_data.get('time', 'نامشخص')}",
                "",
                f"نوع خدمت: {payment_data.get('service_type', 'نامشخص')}",
                f"توضیحات: {payment_data.get('description', 'ندارد')}",
                "",
                f"مبلغ: {self._format_amount(payment_data.get('amount', 0))} ریال",
                f"وضعیت: {payment_data.get('status', 'نامشخص')}",
                "",
                "با تشکر از اعتماد شما",
                "پلتفرم پزشکی هلسا"
            ]
            
            return "\n".join(receipt_lines)
            
        except Exception as e:
            self.logger.error(f"Error generating receipt: {str(e)}")
            return "خطا در تولید رسید"
    
    def parse_amount(self, amount_text: str) -> Tuple[bool, Optional[Decimal]]:
        """
        تبدیل متن مبلغ به عدد
        
        Args:
            amount_text: متن مبلغ
            
        Returns:
            Tuple[bool, Optional[Decimal]]: (موفقیت، مبلغ)
        """
        try:
            # حذف کاراکترهای اضافی
            cleaned = re.sub(r'[^\d.]', '', amount_text)
            
            if not cleaned:
                return False, None
                
            amount = Decimal(cleaned)
            
            # بررسی مثبت بودن
            if amount <= 0:
                return False, None
                
            return True, amount
            
        except Exception as e:
            self.logger.error(f"Error parsing amount: {str(e)}")
            return False, None