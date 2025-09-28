from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.views import (
    EncounterViewSet,
    EncounterScheduleView,
    EncounterStatusView,
    VisitStartView,
    VisitEndView,
    AudioChunkViewSet,
    AudioUploadView,
    TranscriptViewSet,
    SOAPReportViewSet,
    PrescriptionViewSet,
    GenerateSOAPView,
    ShareReportView
)

# ایجاد router
router = DefaultRouter()
router.register(r'encounters', EncounterViewSet, basename='encounter')
router.register(r'audio-chunks', AudioChunkViewSet, basename='audiochunk')
router.register(r'transcripts', TranscriptViewSet, basename='transcript')
router.register(r'soap-reports', SOAPReportViewSet, basename='soapreport')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

app_name = 'encounters'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Encounter management URLs
    path('encounters/schedule/', EncounterScheduleView.as_view(), name='encounter-schedule'),
    path('encounters/<uuid:encounter_id>/status/', EncounterStatusView.as_view(), name='encounter-status'),
    path('encounters/<uuid:encounter_id>/start/', VisitStartView.as_view(), name='visit-start'),
    path('encounters/<uuid:encounter_id>/end/', VisitEndView.as_view(), name='visit-end'),
    
    # Audio management URLs
    path('encounters/<uuid:encounter_id>/upload-audio/', AudioUploadView.as_view(), name='audio-upload'),
    
    # Report generation URLs
    path('encounters/<uuid:encounter_id>/generate-soap/', GenerateSOAPView.as_view(), name='generate-soap'),
    path('soap-reports/<uuid:report_id>/share/', ShareReportView.as_view(), name='share-report'),
]

# URL patterns برای استفاده در urls اصلی پروژه:
# path('api/v1/encounters/', include('encounters.urls', namespace='encounters')),