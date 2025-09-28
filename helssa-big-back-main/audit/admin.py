from django.contrib import admin

from .models import AuditLog, SecurityEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'event_type', 'resource', 'action', 'result', 'ip_address')
    list_filter = ('event_type', 'result', 'resource')
    search_fields = ('user__username', 'action', 'resource', 'ip_address', 'user_agent')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'severity', 'risk_score', 'user', 'ip_address')
    list_filter = ('event_type', 'severity', 'result')
    search_fields = ('user__username', 'event_type', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

