# Import views for easy access
from .encounter_views import (
    EncounterViewSet,
    EncounterScheduleView,
    EncounterStatusView,
    VisitStartView,
    VisitEndView
)
from .audio_views import (
    AudioChunkViewSet,
    AudioUploadView,
    TranscriptViewSet
)
from .report_views import (
    SOAPReportViewSet,
    PrescriptionViewSet,
    GenerateSOAPView,
    ShareReportView
)

__all__ = [
    'EncounterViewSet',
    'EncounterScheduleView',
    'EncounterStatusView',
    'VisitStartView',
    'VisitEndView',
    'AudioChunkViewSet',
    'AudioUploadView',
    'TranscriptViewSet',
    'SOAPReportViewSet',
    'PrescriptionViewSet',
    'GenerateSOAPView',
    'ShareReportView',
]