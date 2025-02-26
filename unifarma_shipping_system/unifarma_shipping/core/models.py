# core/models.py
from django.db import models

class SystemSetting(models.Model):
    """نموذج لإعدادات النظام العامة"""
    key = models.CharField(max_length=100, unique=True, verbose_name="المفتاح")
    value = models.JSONField(blank=True, null=True, verbose_name="القيمة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    is_sensitive = models.BooleanField(default=False, verbose_name="بيانات حساسة")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "إعداد النظام"
        verbose_name_plural = "إعدادات النظام"
        ordering = ['key']


class Notification(models.Model):
    """نموذج للإشعارات في النظام"""
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'معلومات'),
        ('success', 'نجاح'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
    ]

    NOTIFICATION_LEVEL_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    ]

    title = models.CharField(max_length=255, verbose_name="العنوان")
    message = models.TextField(verbose_name="الرسالة")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='info', verbose_name="نوع الإشعار")
    level = models.CharField(max_length=20, choices=NOTIFICATION_LEVEL_CHOICES, default='medium', verbose_name="مستوى الأهمية")

    # ربط بالمستخدم إذا كان متاحًا
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, blank=True, null=True, related_name='notifications', verbose_name="المستخدم")

    # حالة الإشعار
    is_read = models.BooleanField(default=False, verbose_name="تمت القراءة")
    read_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ القراءة")

    # مرجع (إذا كان الإشعار مرتبطًا بكيان معين)
    reference_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="نموذج المرجع")
    reference_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="معرف المرجع")

    # توقيتات
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "إشعار"
        verbose_name_plural = "إشعارات"
        ordering = ['-created_at']


class ActivityLog(models.Model):
    """نموذج لتسجيل نشاطات النظام"""
    ACTION_CHOICES = [
        ('create', 'إنشاء'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
        ('view', 'عرض'),
        ('export', 'تصدير'),
        ('import', 'استيراد'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('api_call', 'استدعاء API'),
        ('webhook', 'Webhook'),
        ('other', 'أخرى'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='activity_logs', verbose_name="المستخدم")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="الإجراء")

    # المصدر
    entity_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="نوع الكيان")
    entity_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="معرف الكيان")
    entity_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="اسم الكيان")

    # معلومات إضافية
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="وكيل المستخدم")

    # بيانات إضافية
    extra_data = models.JSONField(blank=True, null=True, verbose_name="بيانات إضافية")

    # توقيتات
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    def __str__(self):
        return f"{self.get_action_display()} - {self.entity_type or ''} - {self.created_at}"

    class Meta:
        verbose_name = "سجل النشاط"
        verbose_name_plural = "سجلات النشاط"
        ordering = ['-created_at']