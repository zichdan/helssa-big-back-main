"""
URL additions for ai_guardrails
"""

from django.urls import path, include

from django.urls import path, include

# این فایل باید فقط الگوهای خودش رو اکسپورت کنه
urlpatterns = [
    path('api/ai_guardrails/', include('ai_guardrails.urls')),
]
