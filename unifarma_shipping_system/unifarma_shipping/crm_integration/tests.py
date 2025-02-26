# crm_integration/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from .models import CRMWebhookEvent
from .services import CitrixCRMService

logger = logging.getLogger(__name__)

# إضافة إلى المهام الموجودة

@shared_task
def process_webhook_event(event_id):
    """
    مهمة لمعالجة حدث Webhook من نظام Citrix
    """
    try:
        event = CRMWebhookEvent.objects.get(id=event_id)

        # تحقق من أن الحدث لم تتم معالجته بالفعل
        if event.processed:
            logger.info(f"الحدث {event.id} تمت معالجته بالفعل - تخطي")
            return

        logger.info(f"معالجة حدث Webhook {event.id} من نوع {event.event_type}")

        # معالجة الحدث حسب النوع
        if event.event_type == 'deal_update':
            # استخراج معرف الصفقة ومرحلتها من البيانات
            deal_data = event.payload.get('fields', {})
            deal_id = event.payload.get('id')
            stage_id = deal_data.get('STAGE_ID')

            if deal_id and stage_id:
                # التحقق مما إذا كانت المرحلة هي مرحلة الشحن
                from .models import CRMDealStage
                shipping_stage = CRMDealStage.objects.filter(stage_id=stage_id, is_shipping_stage=True).exists()

                if shipping_stage:
                    # جلب الصفقة كاملة من سيتريكس وإنشاء طلب
                    service = CitrixCRMService()
                    # استدعاء دالة لجلب تفاصيل الصفقة ثم معالجتها
                    # (يمكن إنشاء هذه الدالة في الخدمة)

        # تحديث حالة المعالجة
        event.processed = True
        event.processed_at = timezone.now()
        event.save()

        logger.info(f"تمت معالجة حدث Webhook {event.id} بنجاح")

    except CRMWebhookEvent.DoesNotExist:
        logger.error(f"لم يتم العثور على حدث Webhook بمعرف {event_id}")

    except Exception as e:
        logger.exception(f"خطأ في معالجة حدث Webhook {event_id}: {str(e)}")

        # تحديث حالة المعالجة مع رسالة الخطأ
        try:
            event = CRMWebhookEvent.objects.get(id=event_id)
            event.error_message = str(e)
            event.retry_count += 1
            event.save()
        except:
            pass    