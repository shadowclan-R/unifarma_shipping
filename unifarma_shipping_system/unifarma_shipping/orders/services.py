# orders/services.py
import logging
import importlib
from django.utils import timezone
from .models import Order, Shipment

logger = logging.getLogger(__name__)

class ShipmentService:
    """خدمة لإنشاء وإدارة الشحنات مع مختلف شركات الشحن"""

    def create_shipment_for_order(self, order):
        """
        إنشاء شحنة جديدة وإرسالها إلى شركة الشحن المناسبة

        المعلمات:
            order (Order): الطلب المراد شحنه

        العائد:
            Shipment: كائن الشحنة الجديد
        """
        if not order.shipping_company or not order.shipping_account:
            logger.error(f"الطلب {order.id} ليس له شركة شحن محددة")
            return None

        # إنشاء سجل الشحنة
        shipment = Shipment.objects.create(
            order=order,
            shipping_company=order.shipping_company,
            shipping_account=order.shipping_account,
            status='pending'
        )

        try:
            # الحصول على المحول (adapter) المناسب لشركة الشحن
            adapter = self._get_shipping_adapter(order.shipping_company.code)

            if not adapter:
                raise ValueError(f"لم يتم العثور على محول لشركة الشحن: {order.shipping_company.code}")

            # تجهيز الشحنة وإرسالها
            result = adapter.create_shipment(shipment)

            # تحديث سجل الشحنة بناءً على النتيجة
            if result.get('success'):
                shipment.status = 'submitted'
                shipment.tracking_number = result.get('tracking_number')
                shipment.shipping_company_response = result.get('response_data')
                shipment.submitted_at = timezone.now()

                # تحديث حالة الطلب
                order.status = 'processing'
                order.save(update_fields=['status', 'updated_at'])

                # إضافة حدث للسجل
                events = shipment.events_log or []
                events.append({
                    'timestamp': timezone.now().isoformat(),
                    'status': 'submitted',
                    'message': f"تم إنشاء الشحنة بنجاح برقم تتبع: {result.get('tracking_number')}"
                })
                shipment.events_log = events
            else:
                shipment.status = 'error'
                shipment.error_message = result.get('error')

                # إضافة حدث للسجل
                events = shipment.events_log or []
                events.append({
                    'timestamp': timezone.now().isoformat(),
                    'status': 'error',
                    'message': f"فشل في إنشاء الشحنة: {result.get('error')}"
                })
                shipment.events_log = events

            shipment.save()
            return shipment

        except Exception as e:
            logger.exception(f"خطأ أثناء إنشاء الشحنة للطلب {order.id}: {str(e)}")

            # تحديث حالة الشحنة للإشارة إلى الخطأ
            shipment.status = 'error'
            shipment.error_message = str(e)

            # إضافة حدث للسجل
            events = shipment.events_log or []
            events.append({
                'timestamp': timezone.now().isoformat(),
                'status': 'error',
                'message': f"استثناء: {str(e)}"
            })
            shipment.events_log = events

            shipment.save()
            return shipment

    def update_shipment_tracking(self, shipment):
        """
        تحديث معلومات تتبع الشحنة

        المعلمات:
            shipment (Shipment): الشحنة المراد تحديثها

        العائد:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك
        """
        if not shipment.tracking_number:
            logger.error(f"الشحنة {shipment.id} ليس لها رقم تتبع")
            return False

        try:
            # الحصول على المحول (adapter) المناسب لشركة الشحن
            adapter = self._get_shipping_adapter(shipment.shipping_company.code)

            if not adapter:
                raise ValueError(f"لم يتم العثور على محول لشركة الشحن: {shipment.shipping_company.code}")

            # تحديث معلومات التتبع
            result = adapter.track_shipment(shipment)

            if not result.get('success'):
                logger.error(f"فشل في تحديث معلومات تتبع الشحنة {shipment.id}: {result.get('error')}")
                return False

            # تحديث حالة الشحنة
            new_status = result.get('status')
            if new_status and new_status != shipment.status:
                old_status = shipment.status
                shipment.status = new_status

                # تحديث توقيتات خاصة
                if new_status == 'delivered':
                    shipment.delivered_at = timezone.now()

                    # تحديث حالة الطلب
                    shipment.order.status = 'delivered'
                    shipment.order.save(update_fields=['status', 'updated_at'])

                # إضافة حدث للسجل
                events = shipment.events_log or []
                events.append({
                    'timestamp': timezone.now().isoformat(),
                    'status': new_status,
                    'message': f"تغير الحالة من {old_status} إلى {new_status}",
                    'details': result.get('details')
                })
                shipment.events_log = events

            shipment.save()
            return True

        except Exception as e:
            logger.exception(f"خطأ أثناء تحديث معلومات تتبع الشحنة {shipment.id}: {str(e)}")
            return False

    def _get_shipping_adapter(self, company_code):
        """
        الحصول على محول (adapter) شركة الشحن المناسب

        المعلمات:
            company_code (str): رمز شركة الشحن

        العائد:
            object: كائن المحول أو None إذا لم يتم العثور على محول مناسب
        """
        # تحويل رمز الشركة إلى اسم المحول
        adapter_name = f"{company_code.lower()}_adapter"
        module_path = f"shippers.adapters.{adapter_name}"

        try:
            # استيراد المحول ديناميكيًا
            module = importlib.import_module(module_path)
            adapter_class = getattr(module, f"{company_code.capitalize()}Adapter")
            return adapter_class()
        except (ImportError, AttributeError) as e:
            logger.error(f"فشل في استيراد محول شركة الشحن {company_code}: {str(e)}")
            return None