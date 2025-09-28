"""
URLهای اپلیکیشن Doctor
Doctor Application URLs
"""

from django.urls import path
from . import views

app_name = 'doctor'

urlpatterns = [
    # مدیریت پروفایل پزشک
    path('profile/create/', views.create_doctor_profile, name='create_profile'),
    path('profile/', views.get_doctor_profile, name='get_profile'),
    path('profile/update/', views.update_doctor_profile, name='update_profile'),
    
    # مدیریت برنامه کاری
    path('schedule/create/', views.create_doctor_schedule, name='create_schedule'),
    path('schedule/', views.get_doctor_schedule, name='get_schedule'),
    
    # جستجوی پزشکان (عمومی)
    path('search/', views.search_doctors, name='search_doctors'),
    
    # مدیریت مدارک - اگر views اضافی داشته باشیم
    # path('certificates/', views.get_doctor_certificates, name='get_certificates'),
    # path('certificates/add/', views.add_doctor_certificate, name='add_certificate'),
    
    # امتیازدهی - اگر views اضافی داشته باشیم
    # path('<uuid:doctor_id>/rate/', views.rate_doctor, name='rate_doctor'),
    # path('<uuid:doctor_id>/ratings/', views.get_doctor_ratings, name='get_ratings'),
    
    # داشبورد - اگر view اضافی داشته باشیم
    # path('dashboard/', views.get_doctor_dashboard, name='dashboard'),
]