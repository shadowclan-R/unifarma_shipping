# orders/models.py
from django.db import models
from shippers.models import ShippingCompany, ShippingCompanyAccount

class Order(models.Model):
    """نموذج للطلبات المستلمة من نظام سيتريكس"""
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('processing', 'قيد المعالجة'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
        ('returned', 'مرتجع'),
        ('error', 'خطأ'),
    ]

    # معلومات أساسية
    citrix_deal_id = models.CharField(max_length=100, unique=True, verbose_name="معرف الصفقة في سيتريكس")
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="الرقم المرجعي")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="الحالة")

    # معلومات العميل
    customer_name = models.CharField(max_length=255, verbose_name="اسم العميل")
    customer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="هاتف العميل")
    customer_email = models.EmailField(blank=True, null=True, verbose_name="بريد العميل الإلكتروني")

    # معلومات الشحن
    shipping_country = models.CharField(max_length=100, verbose_name="دولة الشحن")
    shipping_city = models.CharField(max_length=100, verbose_name="مدينة الشحن")
    shipping_address = models.TextField(verbose_name="عنوان الشحن")
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="الرمز البريدي")

    # معلومات مالية
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ الإجمالي")
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="مبلغ الدفع عند الاستلام")
    is_cod = models.BooleanField(default=False, verbose_name="دفع عند الاستلام")

    # شركة الشحن
    shipping_company = models.ForeignKey(ShippingCompany, on_delete=models.PROTECT, blank=True, null=True, related_name='orders', verbose_name="شركة الشحن")
    shipping_account = models.ForeignKey(ShippingCompanyAccount, on_delete=models.PROTECT, blank=True, null=True, related_name='orders', verbose_name="حساب الشحن")

    # معلومات توقيت
    citrix_created_at = models.DateTimeField(verbose_name="تاريخ الإنشاء في سيتريكس")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء في النظام")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    shipped_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الشحن")

    # بيانات إضافية من سيتريكس
    citrix_data = models.JSONField(blank=True, null=True, verbose_name="بيانات سيتريكس الأصلية")

    # ملاحظات
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"طلب {self.reference_number or self.citrix_deal_id}"

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at']


class OrderItem(models.Model):
    """نموذج لعناصر الطلب"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="الطلب")
    product_id = models.CharField(max_length=100, verbose_name="معرف المنتج")
    product_name = models.CharField(max_length=255, verbose_name="اسم المنتج")
    sku = models.CharField(max_length=100, blank=True, null=True, verbose_name="رمز المنتج")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")

    # بيانات إضافية
    weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="الوزن (كجم)")
    lot_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الدفعة")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="الرقم التسلسلي")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الانتهاء")

    # بيانات أخرى
    citrix_item_data = models.JSONField(blank=True, null=True, verbose_name="بيانات عنصر سيتريكس الأصلية")

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"

    class Meta:
        verbose_name = "عنصر طلب"
        verbose_name_plural = "عناصر الطلبات"
        ordering = ['order', 'id']


class Shipment(models.Model):
    """نموذج الشحنات المرسلة لشركات الشحن"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('submitted', 'تم الإرسال'),
        ('accepted', 'تم القبول'),
        ('in_transit', 'في الطريق'),
        ('delivered', 'تم التسليم'),
        ('returned', 'مرتجع'),
        ('cancelled', 'ملغي'),
        ('error', 'خطأ'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments', verbose_name="الطلب")
    shipping_company = models.ForeignKey(ShippingCompany, on_delete=models.PROTECT, related_name='shipments', verbose_name="شركة الشحن")
    shipping_account = models.ForeignKey(ShippingCompanyAccount, on_delete=models.PROTECT, related_name='shipments', verbose_name="حساب الشحن")

    # معلومات الشحنة
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم التتبع")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")

    # توقيتات
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الإرسال")
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ التسليم")

    # بيانات الاستجابة من شركة الشحن
    shipping_company_response = models.JSONField(blank=True, null=True, verbose_name="استجابة شركة الشحن")

    # سجل الأحداث
    events_log = models.JSONField(blank=True, null=True, verbose_name="سجل الأحداث")

    # ملاحظات
    error_message = models.TextField(blank=True, null=True, verbose_name="رسالة الخطأ")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"شحنة {self.tracking_number or self.id} للطلب {self.order.reference_number}"

    class Meta:
        verbose_name = "شحنة"
        verbose_name_plural = "الشحنات"
        ordering = ['-created_at']