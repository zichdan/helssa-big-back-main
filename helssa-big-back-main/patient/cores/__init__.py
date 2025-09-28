"""
هسته‌های معماری چهارگانه اپلیکیشن بیمار
Patient Application Four-Core Architecture
"""

from .api_ingress import PatientAPIIngress
from .text_processor import PatientTextProcessor
from .speech_processor import PatientSpeechProcessor
from .orchestrator import PatientOrchestrator

__all__ = [
    'PatientAPIIngress',
    'PatientTextProcessor',
    'PatientSpeechProcessor',
    'PatientOrchestrator'
]