# shippers/admin.py - إضافة إجراءات مخصصة

from django.contrib import admin
from django.utils.html import format_html
from .models import ShippingCompany, ShippingCompanyAccount, ProductSKUMapping, WarehouseMapping
from orders.models import Shipment
from .adapters.smsa_adapter import SmsaAdapter

@admin.register(ShippingCompany)
class ShippingCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(ShippingCompanyAccount)
class ShippingCompanyAccountAdmin(admin.ModelAdmin):
    list_display = ('company', 'title', 'account_type', 'is_active')
    list_filter = ('company', 'account_type', 'is_active')
    search_fields = ('title', 'company__name')
    actions = ['test_smsa_connection']
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('company', 'title', 'account_type', 'is_active')
        }),
        ('بيانات الاعتماد', {
            'fields': ('api_key', 'api_secret', 'passkey', 'api_base_url', 'customer_id', 'warehouse_id')
        }),
        ('نطاق الخدمة', {
            'fields': ('specific_countries', 'additional_settings')
        }),
    )

    def test_smsa_connection(self, request, queryset):
        """اختبار الاتصال بـ SMSA API"""
        success_count = 0
        error_count = 0

        for account in queryset:
            if account.company.code == 'smsa':
                adapter = SmsaAdapter()
                # اختبار اتصال بسيط - يمكن استخدام أي endpoint متاح
                test_shipment = Shipment(
                    shipping_account=account,
                    tracking_number="TEST123"  # معرف اختبار
                )

                result = adapter.track_shipment(test_shipment)

                if result['success']:
                    success_count += 1
                    self.message_user(request, f"نجح الاتصال بحساب SMSA: {account.title}")
                else:
                    error_count += 1
                    self.message_user(request, f"فشل الاتصال بحساب SMSA: {account.title} - {result['error']}", level='ERROR')

        if not (success_count + error_count):
            self.message_user(request, "يرجى اختيار حسابات SMSA فقط للاختبار", level='WARNING')

    test_smsa_connection.short_description = "اختبار الاتصال بـ SMSA API"

@admin.register(ProductSKUMapping)
class ProductSKUMappingAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'sku_internal', 'sku_smsa_ksa', 'sku_smsa_uae', 'sku_smsa_jordan', 'sku_naqel')
    search_fields = ('product_name', 'product_id', 'sku_internal')
    list_filter = ('created_at',)
    fieldsets = (
        ('معلومات المنتج', {
            'fields': ('product_id', 'product_name', 'sku_internal')
        }),
        ('SKUs شركة SMSA', {
            'fields': ('sku_smsa_ksa', 'sku_smsa_uae', 'sku_smsa_jordan')
        }),
        ('SKUs شركات أخرى', {
            'fields': ('sku_naqel',)
        }),
        ('معلومات إضافية', {
            'fields': ('notes',)
        }),
    )
    actions = ['import_skus_from_file']

    def import_skus_from_file(self, request, queryset):
        """استيراد SKUs من ملف"""
        self.message_user(request, "وظيفة استيراد SKUs من ملف ستُنفذ لاحقًا")
    import_skus_from_file.short_description = "استيراد SKUs من ملف"

@admin.register(WarehouseMapping)
class WarehouseMappingAdmin(admin.ModelAdmin):
    list_display = ('shipping_company', 'country_name', 'warehouse_id', 'warehouse_name', 'is_domestic', 'is_cargo', 'is_active')
    list_filter = ('shipping_company', 'country_code', 'is_domestic', 'is_cargo', 'is_active')
    search_fields = ('country_name', 'warehouse_name', 'warehouse_id')
    fieldsets = (
        ('معلومات الربط', {
            'fields': ('shipping_company', 'country_code', 'country_name')
        }),
        ('معلومات المستودع', {
            'fields': ('warehouse_id', 'warehouse_name', 'is_domestic', 'is_cargo', 'is_active')
        }),
        ('معلومات إضافية', {
            'fields': ('notes',)
        }),
    )
    actions = ['import_warehouses_from_file']

    def import_warehouses_from_file(self, request, queryset):
        """استيراد معرفات المستودعات من ملف"""
        self.message_user(request, "وظيفة استيراد معرفات المستودعات من ملف ستُنفذ لاحقًا")
    import_warehouses_from_file.short_description = "استيراد معرفات المستودعات من ملف"