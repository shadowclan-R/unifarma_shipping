# shippers/models.py
from django.db import models

class ShippingCompany(models.Model):
    """نموذج لشركات الشحن المتعامل معها"""
    name = models.CharField(max_length=100, verbose_name="اسم الشركة")
    code = models.CharField(max_length=20, unique=True, verbose_name="رمز الشركة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    logo = models.ImageField(upload_to='shipping_companies/logos/', blank=True, null=True, verbose_name="الشعار")
    website = models.URLField(blank=True, null=True, verbose_name="الموقع الإلكتروني")
    description = models.TextField(blank=True, null=True, verbose_name="وصف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "شركة شحن"
        verbose_name_plural = "شركات الشحن"
        ordering = ['name']

class ShippingCompanyAccount(models.Model):
    """نموذج لحسابات شركات الشحن (يمكن وجود أكثر من حساب لنفس الشركة)"""
    ACCOUNT_TYPE_CHOICES = [
        ('domestic', 'شحن داخلي'),
        ('international', 'شحن دولي'),
        ('specific_country', 'دولة محددة'),
    ]

    company = models.ForeignKey(ShippingCompany, on_delete=models.CASCADE, related_name='accounts', verbose_name="شركة الشحن")
    title = models.CharField(max_length=100, verbose_name="اسم الحساب")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, verbose_name="نوع الحساب")
    api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="مفتاح API")
    api_secret = models.CharField(max_length=255, blank=True, null=True, verbose_name="سر API")
    passkey = models.CharField(max_length=255, blank=True, null=True, verbose_name="كلمة المرور")
    api_base_url = models.URLField(verbose_name="رابط API الأساسي")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # للحسابات من نوع "دولة محددة"
    specific_countries = models.JSONField(blank=True, null=True, verbose_name="الدول المحددة")

    # معلومات إضافية
    customer_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="معرف العميل")
    warehouse_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="معرف المستودع")
    additional_settings = models.JSONField(blank=True, null=True, verbose_name="إعدادات إضافية")

    def __str__(self):
        return f"{self.company.name} - {self.title}"

    class Meta:
        verbose_name = "حساب شركة شحن"
        verbose_name_plural = "حسابات شركات الشحن"
        ordering = ['company__name', 'title']

class ProductSKUMapping(models.Model):
    """نموذج لربط SKU المنتج بشركات الشحن المختلفة"""
    product_id = models.CharField(max_length=100, unique=True, verbose_name="معرف المنتج")
    product_name = models.CharField(max_length=255, verbose_name="اسم المنتج")
    sku_internal = models.CharField(max_length=100, verbose_name="SKU الداخلي")

    # SKUs لشركات الشحن المختلفة
    sku_smsa_ksa = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU SMSA السعودية")
    sku_smsa_uae = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU SMSA الإمارات")
    sku_smsa_jordan = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU SMSA الأردن")
    sku_naqel = models.CharField(max_length=100, blank=True, null=True, verbose_name="SKU ناقل")

    # بيانات إضافية
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"{self.product_name} ({self.sku_internal})"

    class Meta:
        verbose_name = "ربط SKU منتج"
        verbose_name_plural = "ربط SKUs المنتجات"
        indexes = [
            models.Index(fields=['product_id']),
            models.Index(fields=['sku_internal']),
        ]

class WarehouseMapping(models.Model):
    """نموذج لربط المستودعات بالدول وشركات الشحن"""
    shipping_company = models.ForeignKey(ShippingCompany, on_delete=models.CASCADE, related_name='warehouses', verbose_name="شركة الشحن")
    country_code = models.CharField(max_length=10, verbose_name="كود الدولة")
    country_name = models.CharField(max_length=100, verbose_name="اسم الدولة")
    warehouse_id = models.CharField(max_length=100, verbose_name="معرف المستودع")
    warehouse_name = models.CharField(max_length=255, verbose_name="اسم المستودع")
    is_domestic = models.BooleanField(default=False, verbose_name="شحن داخلي")
    is_cargo = models.BooleanField(default=False, verbose_name="شحن بضائع")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    # بيانات إضافية
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"{self.country_name} - {self.warehouse_name} ({self.warehouse_id})"

    class Meta:
        verbose_name = "ربط مستودع"
        verbose_name_plural = "ربط المستودعات"
        unique_together = ['shipping_company', 'country_code', 'warehouse_id']