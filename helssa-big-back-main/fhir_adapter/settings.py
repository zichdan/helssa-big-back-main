"""
تنظیمات اپلیکیشن FHIR Adapter
"""

from django.conf import settings

# تنظیمات پایه FHIR
FHIR_BASE_URL = getattr(settings, 'FHIR_BASE_URL', 'http://localhost:8000/fhir/')
FHIR_VERSION = getattr(settings, 'FHIR_VERSION', 'R4')

# تنظیمات اعتبارسنجی
FHIR_VALIDATION_ENABLED = getattr(settings, 'FHIR_VALIDATION_ENABLED', True)
FHIR_STRICT_VALIDATION = getattr(settings, 'FHIR_STRICT_VALIDATION', False)

# تنظیمات Bundle
FHIR_BUNDLE_MAX_SIZE = getattr(settings, 'FHIR_BUNDLE_MAX_SIZE', 100)
FHIR_BUNDLE_DEFAULT_TYPE = getattr(settings, 'FHIR_BUNDLE_DEFAULT_TYPE', 'collection')

# تنظیمات صفحه‌بندی
FHIR_DEFAULT_PAGE_SIZE = getattr(settings, 'FHIR_DEFAULT_PAGE_SIZE', 20)
FHIR_MAX_PAGE_SIZE = getattr(settings, 'FHIR_MAX_PAGE_SIZE', 100)

# تنظیمات لاگ
FHIR_LOG_RETENTION_DAYS = getattr(settings, 'FHIR_LOG_RETENTION_DAYS', 30)
FHIR_LOG_LEVEL = getattr(settings, 'FHIR_LOG_LEVEL', 'INFO')

# سیستم‌های کدگذاری
FHIR_CODE_SYSTEMS = getattr(settings, 'FHIR_CODE_SYSTEMS', {
    'condition': 'http://snomed.info/sct',
    'medication': 'http://www.nlm.nih.gov/research/umls/rxnorm',
    'procedure': 'http://www.ama-assn.org/go/cpt',
    'observation': 'http://loinc.org',
    'encounter_type': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
    'identifier_type': 'http://terminology.hl7.org/CodeSystem/v2-0203'
})

# تنظیمات امنیتی
FHIR_REQUIRE_AUTHENTICATION = getattr(settings, 'FHIR_REQUIRE_AUTHENTICATION', True)
FHIR_ALLOWED_RESOURCE_TYPES = getattr(settings, 'FHIR_ALLOWED_RESOURCE_TYPES', [
    'Patient', 'Practitioner', 'Encounter', 'Condition',
    'Observation', 'Procedure', 'MedicationRequest',
    'DiagnosticReport', 'CarePlan', 'ImagingStudy'
])

# تنظیمات عملکرد
FHIR_CACHE_ENABLED = getattr(settings, 'FHIR_CACHE_ENABLED', True)
FHIR_CACHE_TIMEOUT = getattr(settings, 'FHIR_CACHE_TIMEOUT', 300)  # 5 دقیقه
FHIR_BATCH_SIZE = getattr(settings, 'FHIR_BATCH_SIZE', 50)

# تنظیمات تبدیل
FHIR_AUTO_GENERATE_ID = getattr(settings, 'FHIR_AUTO_GENERATE_ID', True)
FHIR_PRESERVE_INTERNAL_IDS = getattr(settings, 'FHIR_PRESERVE_INTERNAL_IDS', True)
FHIR_INCLUDE_METADATA = getattr(settings, 'FHIR_INCLUDE_METADATA', True)

# نقشه‌برداری مدل‌های پیش‌فرض
FHIR_DEFAULT_MAPPINGS = getattr(settings, 'FHIR_DEFAULT_MAPPINGS', {
    'auth_otp.UnifiedUser': 'Patient',
    'patient.PatientProfile': 'Patient',
    'doctor.DoctorProfile': 'Practitioner',
    'encounters.Visit': 'Encounter',
    'soap.SOAPNote': 'Observation'
})

# تنظیمات مربوط به identifier ها
FHIR_IDENTIFIER_SYSTEMS = getattr(settings, 'FHIR_IDENTIFIER_SYSTEMS', {
    'national_id': 'http://example.ir/nationalid',
    'medical_id': 'http://example.ir/medicalid',
    'phone': 'http://example.ir/phone',
    'email': 'http://example.ir/email'
})

# تنظیمات خروجی
FHIR_PRETTY_PRINT = getattr(settings, 'FHIR_PRETTY_PRINT', True)
FHIR_INCLUDE_NARRATIVE = getattr(settings, 'FHIR_INCLUDE_NARRATIVE', False)

# Rate limiting
FHIR_RATE_LIMIT_ENABLED = getattr(settings, 'FHIR_RATE_LIMIT_ENABLED', True)
FHIR_RATE_LIMIT_REQUESTS = getattr(settings, 'FHIR_RATE_LIMIT_REQUESTS', 100)
FHIR_RATE_LIMIT_PERIOD = getattr(settings, 'FHIR_RATE_LIMIT_PERIOD', 3600)  # 1 ساعت