"""
URL patterns برای اپلیکیشن تریاژ
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ایجاد router برای ViewSet ها
router = DefaultRouter()
router.register(r'symptom-categories', views.SymptomCategoryViewSet, basename='symptom-categories')
router.register(r'symptoms', views.SymptomViewSet, basename='symptoms')
router.register(r'diagnoses', views.DifferentialDiagnosisViewSet, basename='diagnoses')
router.register(r'sessions', views.TriageSessionViewSet, basename='triage-sessions')
router.register(r'rules', views.TriageRuleViewSet, basename='triage-rules')

app_name = 'triage'

urlpatterns = [
    # ViewSet URLs
    path('api/', include(router.urls)),
    
    # API های اضافی
    path('api/analyze-symptoms/', views.analyze_symptoms, name='analyze-symptoms'),
    path('api/search-symptoms/', views.search_symptoms, name='search-symptoms'),
    path('api/statistics/', views.get_triage_statistics, name='statistics'),
    path('api/emergency-symptoms/', views.get_emergency_symptoms, name='emergency-symptoms'),
    path('api/common-diagnoses/', views.get_common_diagnoses, name='common-diagnoses'),
]