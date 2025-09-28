"""
سرویس مدیریت فاکتورها
Invoice Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Tuple, List
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .base_service import BaseService
from ..models import Invoice, InvoiceItem, InvoiceType, InvoiceStatus

User = get_user_model()


class InvoiceService(BaseService):
    """سرویس مدیریت فاکتورها"""
    
    def __init__(self):
        super().__init__()
        
    def create_invoice(
        self,
        user_id: str,
        invoice_type: str,
        items: List[Dict[str, Any]],
        due_date: timezone.datetime = None,
        description: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد فاکتور
        
        Args:
            user_id: شناسه کاربر
            invoice_type: نوع فاکتور
            items: آیتم‌های فاکتور
            due_date: تاریخ سررسید
            description: توضیحات
            
        Returns:
            Tuple[bool, Dict]: نتیجه ایجاد فاکتور
        """
        try:
            with db_transaction.atomic():
                user = User.objects.get(id=user_id)
                
                if not due_date:
                    due_date = timezone.now() + timezone.timedelta(days=7)
                
                # محاسبه مبلغ کل
                subtotal = sum(
                    Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
                    for item in items
                )
                
                # ایجاد فاکتور
                invoice = Invoice.objects.create(
                    user=user,
                    type=invoice_type,
                    subtotal=subtotal,
                    issue_date=timezone.now(),
                    due_date=due_date,
                    description=description
                )
                
                # ایجاد آیتم‌ها
                for item_data in items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=item_data['description'],
                        quantity=Decimal(str(item_data['quantity'])),
                        unit_price=Decimal(str(item_data['unit_price'])),
                        discount_percent=Decimal(str(item_data.get('discount_percent', 0)))
                    )
                
                # محاسبه مجدد مبلغ نهایی
                invoice.calculate_total()
                invoice.save()
                
                return self.success_response({
                    'invoice_id': str(invoice.id),
                    'invoice_number': invoice.invoice_number,
                    'total_amount': invoice.total_amount,
                    'due_date': invoice.due_date
                })
                
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در ایجاد فاکتور: {str(e)}")
            return self.error_response(
                'invoice_creation_failed',
                'خطا در ایجاد فاکتور'
            )