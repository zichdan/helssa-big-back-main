"""
URL configuration for helssa project.
"""
from django.contrib import admin
from django.urls import path, include




from django.http import JsonResponse

def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Welcome to Helssa API',
        'version': '1.0.0',
        'available_services': {
            'auth_otp': '/api/auth/'
            'adminportal': '/adminportal/',
            'admin_panel': '/admin/'
        },
        'documentation': {
            'adminportal': '/adminportal/docs/',
        }
    })




urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),    
    path('api/v1/', include('api_gateway.urls')),
    path('api/', include('api_gateway.urls')),  # مسیر کوتاه
    # App URLs
    path('api/feedback/', include('feedback.urls')),
    path('chatbot/', include('chatbot.urls')),
    # API Root (for browsable API)
    path('api/', include('rest_framework.urls')),
    path('api/fhir/', include('fhir_adapter.urls')),

  

    
    # API Root
    path('api/', api_root, name='api_root'),
    
    # App URLs
    path('api/auth/', include('auth_otp.urls')),
    path('adminportal/', include('adminportal.urls')),
    path('api/analytics/', include('analytics.urls')),

    path('devops/', include('devops.urls')),
    path('api/doctor/', include('doctor.urls')),
    path('api/auth/', include('auth_otp.urls')),
    path('api/triage/', include('triage.urls')),
    path('api/privacy/', include('privacy.urls')),
    path('api/patient/', include('patient.urls')),

]

# در حالت development فایل‌های media و static را سرو کن
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
