"""
FHIR Adapter for Helssa

این ماژول برای تبدیل داده‌های داخلی به استاندارد FHIR و بالعکس استفاده می‌شود.
"""

default_app_config = 'fhir_adapter.apps.FhirAdapterConfig'

# Version
__version__ = '1.0.0'

# Public API
__all__ = [
    'FHIRTransformer',
    'FHIRValidator',
    'FHIRCodeSystemMapper',
]

# Lazy imports
def __getattr__(name):
    if name == 'FHIRTransformer':
        from .utils import FHIRTransformer
        return FHIRTransformer
    elif name == 'FHIRValidator':
        from .utils import FHIRValidator
        return FHIRValidator
    elif name == 'FHIRCodeSystemMapper':
        from .utils import FHIRCodeSystemMapper
        return FHIRCodeSystemMapper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")