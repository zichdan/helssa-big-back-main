"""
تنظیمات اپ API Gateway
"""
from django.apps import AppConfig


class ApiGatewayConfig(AppConfig):
    """
    کلاس تنظیمات اپ API Gateway
    
    این کلاس تنظیمات اصلی اپ API Gateway را مدیریت می‌کند
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_gateway'
    verbose_name = 'دروازه API'
    
    def ready(self):
        """
        اجرای کدهای اولیه پس از آماده شدن اپ
        """
        # Import کردن signal handlers در اینجا
        pass