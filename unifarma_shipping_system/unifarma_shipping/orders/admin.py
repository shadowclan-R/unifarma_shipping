# orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Shipment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_id', 'product_name', 'quantity', 'unit_price', 'total_price')

class ShipmentInline(admin.StackedInline):
    model = Shipment
    extra = 0
    readonly_fields = ('tracking_number', 'status', 'created_at', 'updated_at', 'submitted_at', 'delivered_at')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'customer_name', 'shipping_country', 'status', 'shipping_company', 'created_at')
    list_filter = ('status', 'shipping_country', 'shipping_company')
    search_fields = ('reference_number', 'citrix_deal_id', 'customer_name', 'customer_phone')
    readonly_fields = ('citrix_deal_id', 'citrix_created_at', 'created_at', 'updated_at')
    inlines = [OrderItemInline, ShipmentInline]
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('reference_number', 'status', 'citrix_deal_id')
        }),
        ('معلومات العميل', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('معلومات الشحن', {
            'fields': ('shipping_country', 'shipping_city', 'shipping_address', 'shipping_postal_code')
        }),
        ('معلومات مالية', {
            'fields': ('total_amount', 'cod_amount', 'is_cod')
        }),
        ('شركة الشحن', {
            'fields': ('shipping_company', 'shipping_account')
        }),
        ('ملاحظات', {
            'fields': ('notes',)
        }),
        ('توقيتات', {
            'fields': ('citrix_created_at', 'created_at', 'updated_at', 'shipped_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shipping_company', 'shipping_account')

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('get_reference', 'tracking_number', 'status', 'shipping_company', 'created_at')
    list_filter = ('status', 'shipping_company')
    search_fields = ('tracking_number', 'order__reference_number')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'delivered_at', 'events_log_formatted')

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('order', 'status', 'tracking_number')
        }),
        ('شركة الشحن', {
            'fields': ('shipping_company', 'shipping_account')
        }),
        ('سجل الأحداث', {
            'fields': ('events_log_formatted',)
        }),
        ('ملاحظات', {
            'fields': ('error_message', 'notes')
        }),
        ('توقيتات', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    def get_reference(self, obj):
        return obj.order.reference_number
    get_reference.short_description = 'رقم الطلب'

    def events_log_formatted(self, obj):
        if not obj.events_log:
            return "لا توجد أحداث مسجلة"

        html = '<table width="100%">'
        html += '<tr><th>التاريخ</th><th>الحالة</th><th>الرسالة</th></tr>'

        for event in obj.events_log:
            timestamp = event.get('timestamp', '')
            status = event.get('status', '')
            message = event.get('message', '')

            html += f'<tr><td>{timestamp}</td><td>{status}</td><td>{message}</td></tr>'

        html += '</table>'
        return format_html(html)
    events_log_formatted.short_description = 'سجل الأحداث'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'shipping_company', 'shipping_account')