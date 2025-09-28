"""
URLهای اپلیکیشن بیمار
Patient Application URLs
"""

from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    # Patient Profile URLs
    path('profile/create/', views.create_patient_profile, name='create_patient_profile'),
    path('profile/<str:patient_id>/', views.get_patient_profile, name='get_patient_profile'),
    path('profile/<str:patient_id>/update/', views.update_patient_profile, name='update_patient_profile'),
    path('profile/<str:patient_id>/statistics/', views.get_patient_statistics, name='get_patient_statistics'),
    
    # Patient Search
    path('search/', views.search_patients, name='search_patients'),
    
    # Medical Records URLs
    path('medical-records/', views.create_medical_record, name='create_medical_record'),
    path('<str:patient_id>/medical-records/', views.get_patient_medical_records, name='get_patient_medical_records'),
    
    # Prescriptions URLs
    path('prescriptions/', views.create_prescription, name='create_prescription'),
    path('<str:patient_id>/prescriptions/', views.get_patient_prescriptions, name='get_patient_prescriptions'),
    path('prescriptions/<str:prescription_id>/repeat/', views.repeat_prescription, name='repeat_prescription'),
    
    # Consent Management URLs
    path('consents/', views.create_consent, name='create_consent'),
    path('consents/<str:consent_id>/grant/', views.grant_consent, name='grant_consent'),
    
    # Audio Transcription
    path('transcribe/', views.transcribe_audio, name='transcribe_audio'),
    
    # Analytics
    path('analyze/', views.analyze_data, name='analyze_data'),
]