# crm_integration/admin.py
from django.contrib import admin
from .models import CRMWebhookEvent, CRMAPICall, CRMDealStage, CRMShippingMapping

@admin.register(CRMWebhookEvent)
class CRMWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'event_id', 'processed', 'created_at')
    list_filter = ('event_type', 'processed')
    search_fields = ('event_id',)
    readonly_fields = ('event_type', 'event_id', 'payload', 'created_at', 'processed_at')

@admin.register(CRMAPICall)
class CRMAPICallAdmin(admin.ModelAdmin):
    list_display = ('call_type', 'endpoint', 'status', 'status_code', 'created_at')
    list_filter = ('call_type', 'status')
    search_fields = ('endpoint',)
    readonly_fields = ('call_type', 'endpoint', 'parameters', 'request_data', 'response_data', 'status', 'status_code', 'created_at', 'updated_at')

@admin.register(CRMDealStage)
class CRMDealStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage_id', 'is_shipping_stage')
    list_filter = ('is_shipping_stage',)
    search_fields = ('name', 'stage_id')

@admin.register(CRMShippingMapping)
class CRMShippingMappingAdmin(admin.ModelAdmin):
    list_display = ('crm_field', 'crm_value', 'shipping_company_account', 'is_active')
    list_filter = ('crm_field', 'is_active')
    search_fields = ('crm_field', 'crm_value')