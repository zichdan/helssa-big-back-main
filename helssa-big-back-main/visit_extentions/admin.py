from __future__ import annotations

from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'visit_id', 'doctor', 'patient', 'days_off', 'is_revoked', 'created_at'
    )
    search_fields = ('id', 'visit_id', 'doctor__phone_number', 'patient__phone_number')
    list_filter = ('is_revoked', 'created_at')

