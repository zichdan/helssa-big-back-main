"""
سرویس مدیریت کمیسیون‌ها
Commission Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Tuple
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .base_service import BaseService
from ..models import Commission, CommissionType, CommissionStatus, Settlement

User = get_user_model()


class CommissionService(BaseService):
    """سرویس مدیریت کمیسیون‌ها"""
    
    def __init__(self):
        super().__init__()
        
    def calculate_commission(
        self,
        doctor_id: str,
        gross_amount: Decimal,
        commission_rate: Decimal,
        commission_type: str = CommissionType.VISIT,
        source_transaction_id: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        محاسبه کمیسیون
        
        Args:
            doctor_id: شناسه پزشک
            gross_amount: مبلغ ناخالص
            commission_rate: نرخ کمیسیون
            commission_type: نوع کمیسیون
            source_transaction_id: شناسه تراکنش مبدأ
            
        Returns:
            Tuple[bool, Dict]: نتیجه محاسبه
        """
        try:
            doctor = User.objects.get(id=doctor_id, user_type='doctor')
            
            # ایجاد کمیسیون
            commission = Commission.objects.create(
                doctor=doctor,
                type=commission_type,
                gross_amount=gross_amount,
                commission_rate=commission_rate,
                source_transaction_id=source_transaction_id
            )
            
            # محاسبه و علامت‌گذاری به عنوان محاسبه شده
            commission.mark_calculated()
            
            return self.success_response({
                'commission_id': str(commission.id),
                'gross_amount': commission.gross_amount,
                'commission_amount': commission.commission_amount,
                'net_amount': commission.net_amount,
                'final_amount': commission.final_amount
            })
            
        except User.DoesNotExist:
            return self.error_response('doctor_not_found', 'پزشک یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در محاسبه کمیسیون: {str(e)}")
            return self.error_response(
                'commission_calculation_failed',
                'خطا در محاسبه کمیسیون'
            )