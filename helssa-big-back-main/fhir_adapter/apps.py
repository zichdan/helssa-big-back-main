from django.apps import AppConfig


class FhirAdapterConfig(AppConfig):
    """
    پیکربندی اپلیکیشن FHIR Adapter
    
    این اپلیکیشن مسئول تبدیل داده‌های داخلی به استاندارد FHIR و بالعکس است
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fhir_adapter'
    verbose_name = 'FHIR Adapter'