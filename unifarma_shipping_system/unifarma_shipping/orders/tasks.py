# orders/tasks.py
import logging
from celery import shared_task
from .models import Order, Shipment
from .services import ShipmentService

logger = logging.getLogger(__name__)

@shared_task
def process_new_shipments():
    """
    مهمة لمعالجة الطلبات الجديدة وإرسالها إلى شركات الشحن
    """
    logger.info("بدء معالجة الطلبات الجديدة للشحن")

    # الحصول على الطلبات الجديدة التي لم يتم شحنها بعد
    new_orders = Order.objects.filter(status='new').select_related('shipping_company', 'shipping_account')

    processed_count = 0
    errors_count = 0

    for order in new_orders:
        try:
            logger.info(f"معالجة الطلب {order.id} ({order.reference_number})")

            # التحقق من وجود شركة شحن محددة
            if not order.shipping_company or not order.shipping_account:
                logger.error(f"الطلب {order.id} لا يحتوي على شركة شحن محددة")
                continue

            # إنشاء الشحنة وإرسالها
            service = ShipmentService()
            shipment = service.create_shipment_for_order(order)

            if shipment and shipment.status != 'error':
                processed_count += 1
                logger.info(f"تم إنشاء الشحنة بنجاح للطلب {order.id}: {shipment.tracking_number}")
            else:
                errors_count += 1
                error_msg = shipment.error_message if shipment else "خطأ غير معروف"
                logger.error(f"فشل في إنشاء الشحنة للطلب {order.id}: {error_msg}")

        except Exception as e:
            errors_count += 1
            logger.exception(f"خطأ في معالجة الطلب {order.id}: {str(e)}")

    logger.info(f"اكتملت معالجة الشحنات: {processed_count} نجحت، {errors_count} فشلت")
    return {
        "processed": processed_count,
        "errors": errors_count,
        "total": new_orders.count()
    }

@shared_task
def update_shipment_tracking():
    """
    مهمة لتحديث معلومات تتبع الشحنات
    """
    logger.info("بدء تحديث معلومات تتبع الشحنات")

    # الحصول على الشحنات المقدمة التي تحتاج إلى تحديث
    active_shipments = Shipment.objects.filter(
        status__in=['submitted', 'accepted', 'in_transit']
    ).select_related('shipping_company', 'shipping_account', 'order')

    updated_count = 0
    errors_count = 0

    for shipment in active_shipments:
        try:
            logger.info(f"تحديث معلومات تتبع الشحنة {shipment.id} ({shipment.tracking_number})")

            service = ShipmentService()
            updated = service.update_shipment_tracking(shipment)

            if updated:
                updated_count += 1
                logger.info(f"تم تحديث معلومات تتبع الشحنة {shipment.id}: {shipment.status}")
            else:
                errors_count += 1
                logger.error(f"فشل في تحديث معلومات تتبع الشحنة {shipment.id}")

        except Exception as e:
            errors_count += 1
            logger.exception(f"خطأ في تحديث معلومات تتبع الشحنة {shipment.id}: {str(e)}")

    logger.info(f"اكتمل تحديث تتبع الشحنات: {updated_count} نجحت، {errors_count} فشلت")
    return {
        "updated": updated_count,
        "errors": errors_count,
        "total": active_shipments.count()
    }