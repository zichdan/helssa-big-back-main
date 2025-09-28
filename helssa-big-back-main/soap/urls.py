from django.urls import path
from .views import GenerateSOAPView, SOAPFormatsView


urlpatterns = [
    path('generate/', GenerateSOAPView.as_view(), name='soap-generate'),
    path('formats/<int:report_id>/', SOAPFormatsView.as_view(), name='soap-formats'),
]