# Import تمام مدل‌ها برای دسترسی آسان‌تر
from .encounter import Encounter
from .audio_chunk import AudioChunk
from .transcript import Transcript
from .soap_report import SOAPReport
from .prescription import Prescription
from .encounter_file import EncounterFile

__all__ = [
    'Encounter',
    'AudioChunk',
    'Transcript',
    'SOAPReport',
    'Prescription',
    'EncounterFile',
]