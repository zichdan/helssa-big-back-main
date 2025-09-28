"""
API Ingress Core برای feedback app
مدیریت ورودی و خروجی API ها
"""

import logging
from typing import Dict, Any, Tuple, Optional
from django.core.exceptions import ValidationError
from rest_framework import status

# Import core if available
try:
    from app_standards.four_cores.api_ingress import APIIngressCore
except ImportError:
    # Fallback if app_standards doesn't exist
    class APIIngressCore:
        def __init__(self):
            self.logger = logging.getLogger(__name__)


class FeedbackAPIIngressCore(APIIngressCore):
    """
    هسته API Ingress برای مدیریت ورودی و خروجی feedback
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def validate_rating_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های امتیازدهی
        
        Args:
            data: داده‌های ورودی امتیازدهی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، داده‌های پاک شده یا خطاها)
        """
        try:
            # بررسی فیلدهای اجباری
            required_fields = ['session_id', 'overall_rating']
            for field in required_fields:
                if field not in data:
                    return False, {'error': f'فیلد {field} اجباری است'}
            
            # بررسی محدوده امتیاز
            rating = data.get('overall_rating')
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                return False, {'error': 'امتیاز باید عددی بین 1 تا 5 باشد'}
            
            # بررسی امتیازات تفکیکی
            optional_ratings = ['response_quality', 'response_speed', 'helpfulness']
            for field in optional_ratings:
                if field in data:
                    value = data[field]
                    if value is not None and (not isinstance(value, int) or not (1 <= value <= 5)):
                        return False, {'error': f'{field} باید عددی بین 1 تا 5 باشد'}
            
            # تمیز کردن متن‌ها
            text_fields = ['comment', 'suggestions']
            for field in text_fields:
                if field in data and data[field]:
                    data[field] = data[field].strip()
            
            # لاگ موفقیت
            self.logger.info(f"Rating data validated successfully for session {data['session_id']}")
            
            return True, data
            
        except Exception as e:
            self.logger.error(f"Error validating rating data: {str(e)}")
            return False, {'error': 'خطا در اعتبارسنجی داده‌ها'}
    
    def validate_feedback_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های بازخورد پیام
        
        Args:
            data: داده‌های ورودی بازخورد
            
        Returns:
            Tuple[bool, dict]: (موفقیت، داده‌های پاک شده یا خطاها)
        """
        try:
            # بررسی فیلدهای اجباری
            required_fields = ['message_id', 'feedback_type']
            for field in required_fields:
                if field not in data:
                    return False, {'error': f'فیلد {field} اجباری است'}
            
            # بررسی نوع بازخورد
            valid_types = ['helpful', 'not_helpful', 'incorrect', 'incomplete', 'inappropriate', 'excellent']
            if data['feedback_type'] not in valid_types:
                return False, {'error': 'نوع بازخورد نامعتبر است'}
            
            # تمیز کردن متن‌ها
            text_fields = ['detailed_feedback', 'expected_response']
            for field in text_fields:
                if field in data and data[field]:
                    data[field] = data[field].strip()
            
            # لاگ موفقیت
            self.logger.info(f"Feedback data validated successfully for message {data['message_id']}")
            
            return True, data
            
        except Exception as e:
            self.logger.error(f"Error validating feedback data: {str(e)}")
            return False, {'error': 'خطا در اعتبارسنجی داده‌ها'}
    
    def validate_survey_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های نظرسنجی
        
        Args:
            data: داده‌های ورودی نظرسنجی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، داده‌های پاک شده یا خطاها)
        """
        try:
            # بررسی فیلدهای اجباری
            required_fields = ['title', 'questions']
            for field in required_fields:
                if field not in data:
                    return False, {'error': f'فیلد {field} اجباری است'}
            
            # بررسی سوالات
            questions = data.get('questions', [])
            if not isinstance(questions, list) or len(questions) == 0:
                return False, {'error': 'حداقل یک سوال باید وجود داشته باشد'}
            
            # اعتبارسنجی هر سوال
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    return False, {'error': f'سوال {i+1} باید یک object باشد'}
                
                if 'text' not in question:
                    return False, {'error': f'سوال {i+1} باید متن داشته باشد'}
                
                if 'type' not in question:
                    return False, {'error': f'سوال {i+1} باید نوع داشته باشد'}
            
            # بررسی نوع نظرسنجی
            valid_types = ['general', 'post_session', 'periodic', 'satisfaction', 'improvement']
            if data.get('survey_type') and data['survey_type'] not in valid_types:
                return False, {'error': 'نوع نظرسنجی نامعتبر است'}
            
            # تمیز کردن متن‌ها
            data['title'] = data['title'].strip()
            if 'description' in data:
                data['description'] = data['description'].strip()
            
            # لاگ موفقیت
            self.logger.info(f"Survey data validated successfully: {data['title']}")
            
            return True, data
            
        except Exception as e:
            self.logger.error(f"Error validating survey data: {str(e)}")
            return False, {'error': 'خطا در اعتبارسنجی داده‌ها'}
    
    def validate_survey_response_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های پاسخ نظرسنجی
        
        Args:
            data: داده‌های ورودی پاسخ نظرسنجی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، داده‌های پاک شده یا خطاها)
        """
        try:
            # بررسی فیلدهای اجباری
            required_fields = ['survey_id', 'answers']
            for field in required_fields:
                if field not in data:
                    return False, {'error': f'فیلد {field} اجباری است'}
            
            # بررسی پاسخ‌ها
            answers = data.get('answers', {})
            if not isinstance(answers, dict) or len(answers) == 0:
                return False, {'error': 'حداقل یک پاسخ باید وجود داشته باشد'}
            
            # لاگ موفقیت
            self.logger.info(f"Survey response data validated successfully for survey {data['survey_id']}")
            
            return True, data
            
        except Exception as e:
            self.logger.error(f"Error validating survey response data: {str(e)}")
            return False, {'error': 'خطا در اعتبارسنجی داده‌ها'}
    
    def format_success_response(self, data: Any, message: str = "عملیات با موفقیت انجام شد") -> Dict[str, Any]:
        """
        فرمت کردن پاسخ موفق
        
        Args:
            data: داده‌های پاسخ
            message: پیام موفقیت
            
        Returns:
            dict: پاسخ فرمت شده
        """
        return {
            'success': True,
            'message': message,
            'data': data
        }
    
    def format_error_response(self, error: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """
        فرمت کردن پاسخ خطا
        
        Args:
            error: پیام خطا
            details: جزئیات اضافی خطا
            
        Returns:
            dict: پاسخ خطا فرمت شده
        """
        response = {
            'success': False,
            'error': error
        }
        
        if details:
            response['details'] = details
            
        return response
    
    def get_http_status_for_error(self, error_type: str) -> int:
        """
        تعیین HTTP status code برای انواع خطا
        
        Args:
            error_type: نوع خطا
            
        Returns:
            int: HTTP status code
        """
        error_status_map = {
            'validation_error': status.HTTP_400_BAD_REQUEST,
            'not_found': status.HTTP_404_NOT_FOUND,
            'permission_denied': status.HTTP_403_FORBIDDEN,
            'rate_limit': status.HTTP_429_TOO_MANY_REQUESTS,
            'internal_error': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        
        return error_status_map.get(error_type, status.HTTP_400_BAD_REQUEST)