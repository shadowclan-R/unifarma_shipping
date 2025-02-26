#unifarma_shipping/celery.py

import os
from celery import Celery

# تحديد متغير البيئة لإعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

# إنشاء تطبيق Celery
app = Celery('unifarma_shipping')

# تحميل الإعدادات من ملف إعدادات Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# اكتشاف تلقائي للمهام من التطبيقات المسجلة
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')