# crm_integration/models.py
from django.db import models

class CRMWebhookEvent(models.Model):
    """نموذج لتخزين الأحداث الواردة من Webhook Citrix24"""
    EVENT_TYPES = [
        ('deal_update', 'تحديث صفقة'),
        ('deal_create', 'إنشاء صفقة'),
        ('deal_delete', 'حذف صفقة'),
        ('other', 'أخرى'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, verbose_name="نوع الحدث")
    event_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="معرف الحدث")
    payload = models.JSONField(verbose_name="بيانات الحدث")
    processed = models.BooleanField(default=False, verbose_name="تمت المعالجة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    processed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ المعالجة")

    # في حالة حدوث خطأ
    error_message = models.TextField(blank=True, null=True, verbose_name="رسالة الخطأ")
    retry_count = models.PositiveIntegerField(default=0, verbose_name="عدد محاولات إعادة المعالجة")

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at}"

    class Meta:
        verbose_name = "حدث CRM Webhook"
        verbose_name_plural = "أحداث CRM Webhook"
        ordering = ['-created_at']


class CRMAPICall(models.Model):
    """نموذج لتتبع طلبات API لنظام سيتريكس"""
    CALL_TYPES = [
        ('get_deals', 'جلب الصفقات'),
        ('get_deal', 'جلب صفقة'),
        ('update_deal', 'تحديث صفقة'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('success', 'نجاح'),
        ('error', 'خطأ'),
    ]

    call_type = models.CharField(max_length=50, choices=CALL_TYPES, verbose_name="نوع الطلب")
    endpoint = models.CharField(max_length=255, verbose_name="نقطة النهاية")
    parameters = models.JSONField(blank=True, null=True, verbose_name="المعلمات")
    request_data = models.JSONField(blank=True, null=True, verbose_name="بيانات الطلب")
    response_data = models.JSONField(blank=True, null=True, verbose_name="بيانات الاستجابة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    status_code = models.IntegerField(blank=True, null=True, verbose_name="رمز الحالة HTTP")

    # توقيتات
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # في حالة حدوث خطأ
    error_message = models.TextField(blank=True, null=True, verbose_name="رسالة الخطأ")

    def __str__(self):
        return f"{self.get_call_type_display()} - {self.created_at}"

    class Meta:
        verbose_name = "طلب CRM API"
        verbose_name_plural = "طلبات CRM API"
        ordering = ['-created_at']


class CRMDealStage(models.Model):
    """نموذج لتخزين مراحل الصفقة في سيتريكس"""
    stage_id = models.CharField(max_length=50, unique=True, verbose_name="معرف المرحلة")
    name = models.CharField(max_length=100, verbose_name="اسم المرحلة")
    is_shipping_stage = models.BooleanField(default=False, verbose_name="مرحلة شحن")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مرحلة صفقة CRM"
        verbose_name_plural = "مراحل صفقات CRM"
        ordering = ['name']


class CRMShippingMapping(models.Model):
    """نموذج لتخزين قواعد التعيين بين قيم سيتريكس وشركات الشحن"""
    crm_field = models.CharField(max_length=100, verbose_name="حقل CRM")
    crm_value = models.CharField(max_length=100, verbose_name="قيمة CRM")
    shipping_company_account = models.ForeignKey('shippers.ShippingCompanyAccount', on_delete=models.CASCADE, verbose_name="حساب شركة الشحن")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    def __str__(self):
        return f"{self.crm_field}: {self.crm_value} -> {self.shipping_company_account}"

    class Meta:
        verbose_name = "تعيين شحن CRM"
        verbose_name_plural = "تعيينات شحن CRM"
        ordering = ['crm_field', 'crm_value']
        unique_together = ['crm_field', 'crm_value']