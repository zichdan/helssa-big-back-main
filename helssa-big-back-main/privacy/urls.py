"""
URL Configuration برای ماژول Privacy
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_extended

# Router برای ViewSets
router = DefaultRouter()
router.register(r'classifications', views.DataClassificationViewSet)
router.register(r'fields', views.DataFieldViewSet)
router.register(r'access-logs', views_extended.DataAccessLogViewSet)
router.register(r'consents', views_extended.ConsentRecordViewSet)

app_name = 'privacy'

urlpatterns = [
    # ViewSets از طریق router
    path('', include(router.urls)),
    
    # API های خاص برای پنهان‌سازی و تحلیل
    path('redact-text/', views_extended.redact_text, name='redact-text'),
    path('analyze-risks/', views_extended.analyze_privacy_risks, name='analyze-risks'),
    
    # API های مدیریت رضایت
    path('my-consents/', views_extended.get_user_consents, name='my-consents'),
    
    # API های آمار (فقط برای ادمین)
    path('statistics/', views_extended.get_privacy_statistics, name='statistics'),
]