from django.urls import path
from .views import (
    CertificateCreateView,
    CertificateRevokeView,
    CertificateDetailView,
    CertificateVerifyPageView,
)


app_name = 'visit_extentions'

urlpatterns = [
    path('api/v1/visit-ext/certificates/', CertificateCreateView.as_view(), name='certificate-create'),
    path('api/v1/visit-ext/certificates/<uuid:certificate_id>/', CertificateDetailView.as_view(), name='certificate-detail'),
    path('api/v1/visit-ext/certificates/<uuid:certificate_id>/revoke/', CertificateRevokeView.as_view(), name='certificate-revoke'),

    # صفحه عمومی بررسی اعتبار
    path('verify/certificate/<str:token>/', CertificateVerifyPageView.as_view(), name='certificate-verify-page'),
]

