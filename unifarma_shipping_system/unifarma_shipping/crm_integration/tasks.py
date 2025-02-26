# crm_integration/tasks.py
import logging
from celery import shared_task
from .services import CitrixCRMService

logger = logging.getLogger(__name__)

@shared_task
def sync_citrix_shipping_deals():
    """
    مهمة لمزامنة الصفقات من سيتريكس التي في مرحلة الشحن
    """
    logger.info("بدء مزامنة صفقات الشحن من سيتريكس")

    service = CitrixCRMService()
    result = service.process_shipping_deals()

    logger.info(f"اكتملت مزامنة صفقات الشحن: {result}")
    return result