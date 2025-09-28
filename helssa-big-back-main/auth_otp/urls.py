"""
URL Configuration for OTP Authentication System
"""

from django.urls import path
from . import views
from . import views_extended

app_name = 'auth_otp'

urlpatterns = [
    # OTP endpoints
    path('otp/send/', views.send_otp, name='otp_send'),
    path('otp/verify/', views.verify_otp, name='otp_verify'),
    path('otp/resend/', views_extended.resend_otp, name='otp_resend'),
    path('otp/status/<uuid:otp_id>/', views_extended.otp_status, name='otp_status'),
    
    # Token endpoints
    path('token/refresh/', views.refresh_token, name='token_refresh'),
    
    # Auth endpoints
    path('logout/', views.logout, name='logout'),
    path('register/', views_extended.register, name='register'),
    
    # Session management
    path('sessions/', views_extended.user_sessions, name='user_sessions'),
    path('sessions/<uuid:session_id>/revoke/', views_extended.revoke_session, name='revoke_session'),
    
    # Rate limit info
    path('rate-limit/<str:phone_number>/', views_extended.rate_limit_status, name='rate_limit_status'),
]