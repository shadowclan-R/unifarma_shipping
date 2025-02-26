# core/admin.py
from django.contrib import admin
from .models import SystemSetting, Notification, ActivityLog

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'is_sensitive', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'level', 'is_read', 'created_at')
    list_filter = ('notification_type', 'level', 'is_read')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'read_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_name', 'user', 'created_at')
    list_filter = ('action',)
    search_fields = ('entity_name', 'user__username', 'description')
    readonly_fields = ('action', 'entity_type', 'entity_id', 'entity_name', 'user', 'description', 'ip_address', 'user_agent', 'extra_data', 'created_at')