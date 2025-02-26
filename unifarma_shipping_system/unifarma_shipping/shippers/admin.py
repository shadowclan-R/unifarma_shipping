# shippers/admin.py
from django.contrib import admin
from .models import ShippingCompany, ShippingCompanyAccount

@admin.register(ShippingCompany)
class ShippingCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ShippingCompanyAccount)
class ShippingCompanyAccountAdmin(admin.ModelAdmin):
    list_display = ('company', 'title', 'account_type', 'is_active', 'created_at')
    list_filter = ('company', 'account_type', 'is_active')
    search_fields = ('title', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('company', 'title', 'account_type', 'is_active')
        }),
        ('بيانات الاعتماد', {
            'fields': ('api_key', 'api_secret', 'passkey', 'api_base_url'),
            'classes': ('collapse',)
        }),
        ('معلومات إضافية', {
            'fields': ('customer_id', 'warehouse_id', 'specific_countries', 'additional_settings')
        }),
        ('توقيتات', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )