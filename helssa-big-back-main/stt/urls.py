"""
مسیریابی URL های اپ STT
"""
from django.urls import path
from . import views

app_name = 'stt'

urlpatterns = [
    # API های مشترک
    path('transcribe/', views.create_transcription, name='create_transcription'),
    path('task/<str:task_id>/', views.get_task_status, name='get_task_status'),
    path('task/<str:task_id>/cancel/', views.cancel_task, name='cancel_task'),
    path('tasks/', views.get_user_tasks, name='get_user_tasks'),
    path('statistics/', views.get_user_statistics, name='get_user_statistics'),
    
    # API های ویژه بیمار
    path('patient/voice-to-text/', views.patient_voice_to_text, name='patient_voice_to_text'),
    
    # API های ویژه دکتر
    path('doctor/dictation/', views.doctor_dictation, name='doctor_dictation'),
    path('doctor/patient/<int:patient_id>/voice-history/', 
         views.doctor_get_patient_voice_history, 
         name='doctor_get_patient_voice_history'),
    
    # API های ادمین
    path('admin/pending-reviews/', views.admin_get_pending_reviews, name='admin_pending_reviews'),
    path('admin/review/<str:task_id>/', views.admin_review_transcription, name='admin_review_transcription'),
]