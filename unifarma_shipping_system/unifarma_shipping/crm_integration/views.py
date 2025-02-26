# crm_integration/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import CRMWebhookEvent
from .services import CitrixCRMService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def citrix_webhook(request):
    """
    Webhook لاستقبال أحداث من نظام Citrix24 CRM
    """
    try:
        # استخراج البيانات من الطلب
        payload = json.loads(request.body)

        # تحديد نوع الحدث
        event_type = 'other'
        if 'event' in payload:
            if payload['event'] == 'ONCRMDEALADD':
                event_type = 'deal_create'
            elif payload['event'] == 'ONCRMDEALUPDATE':
                event_type = 'deal_update'
            elif payload['event'] == 'ONCRMDEALDELETE':
                event_type = 'deal_delete'

        # تخزين الحدث في قاعدة البيانات
        event = CRMWebhookEvent.objects.create(
            event_type=event_type,
            event_id=payload.get('id'),
            payload=payload
        )

        # إذا كان تحديث لصفقة وتغيرت المرحلة إلى مرحلة الشحن، معالجتها فورًا
        if event_type == 'deal_update' and 'STAGE_ID' in payload.get('fields', {}):
            from crm_integration.tasks import process_webhook_event
            process_webhook_event.delay(event.id)

        return JsonResponse({
            'success': True,
            'message': 'تم استلام الحدث بنجاح',
            'event_id': event.id
        })

    except json.JSONDecodeError:
        logger.error("خطأ في تحليل البيانات الواردة من Webhook")
        return JsonResponse({
            'success': False,
            'error': 'خطأ في تحليل البيانات JSON'
        }, status=400)

    except Exception as e:
        logger.exception(f"خطأ في معالجة Webhook من Citrix: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'خطأ داخلي في الخادم'
        }, status=500)