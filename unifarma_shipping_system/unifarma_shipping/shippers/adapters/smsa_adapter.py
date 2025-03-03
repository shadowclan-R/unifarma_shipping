# shippers/adapters/smsa_adapter.py
import logging
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .base_adapter import ShippingAdapter
from ..models import WarehouseMapping, ProductSKUMapping

logger = logging.getLogger(__name__)

class SmsaAdapter(ShippingAdapter):
    """محول للتكامل مع شركة SMSA باستخدام STAX API"""

    def __init__(self):
        self.api_base_url = "https://sam.smsaexpress.com/STAXRestApi/api"
        # قائمة الدول التي تحتاج إلى إضافة 0 قبل رقم الهاتف (9 أرقام)
        self.nine_digits_countries = ['Bahrain', 'Qatar', 'Kuwait', 'البحرين', 'قطر', 'الكويت']

    def create_shipment(self, shipment):
        """
        إنشاء شحنة جديدة في نظام SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة من نظامنا

        العائد:
            dict: نتيجة العملية (success, tracking_number, response_data, error)
        """
        try:
            # الحصول على بيانات الاعتماد من حساب الشحن
            passkey = shipment.shipping_account.passkey
            customer_id = shipment.shipping_account.customer_id
            
            # الحصول على معرف المستودع المناسب للدولة
            warehouse_id = self._get_warehouse_id(
                shipment.shipping_company.id, 
                shipment.order.shipping_country, 
                shipment.shipping_account.is_domestic
            ) or shipment.shipping_account.warehouse_id

            if not all([passkey, customer_id, warehouse_id]):
                return {
                    'success': False,
                    'error': "معلومات الاعتماد ناقصة (passkey, customer_id, warehouse_id)"
                }

            # الحصول على بيانات الطلب
            order = shipment.order

            # معالجة رقم العميل حسب الدولة
            customer_phone = self._format_phone_number(
                shipment.order.customer_phone, 
                shipment.order.shipping_country
            )

            # تجهيز عناصر الطلب مع SKUs المناسبة
            order_items = []
            for item in order.items.all():
                sku = self._get_product_sku(
                    item.product_id, 
                    shipment.order.shipping_country
                ) or item.sku or item.product_id

                order_item = {
                    "orderId": 0,  # سيتم ملؤه بواسطة SMSA
                    "SKU": sku,
                    "quantity": item.quantity,
                    "iLotNo": item.lot_number or "",
                    "serno": item.serial_number or "",
                    "iExpDate": item.expiry_date.isoformat() if item.expiry_date else ""
                }
                order_items.append(order_item)

            # تاريخ الشحن والإلغاء
            ship_date = timezone.now()
            cancel_date = ship_date + timedelta(days=30)

            # تجهيز بيانات الطلب
            fulfilment_order_data = {
                "passkey": passkey,
                "CustId": customer_id,
                "WrhId": warehouse_id,
                "Refid": order.reference_number or f"ORD-{order.id}",
                "codAmt": str(order.cod_amount) if order.is_cod else "0",
                "fforderitemCreations": order_items,
                "PONo": order.reference_number or f"ORD-{order.id}",
                "Shipdt": ship_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "CancelDate": cancel_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "Notes": order.notes or "",
                "shipToRecipientId": "",
                "ShipAccountNo": "",
                "ShipToName": order.customer_name,
                "ShipToCompany": "",
                "ShipToAddress1": order.shipping_address,
                "ShipToAddress2": "",
                "ShipToCity": order.shipping_city,
                "ShipToZip": order.shipping_postal_code or "",
                "ShipToCountry": order.shipping_country,
                "ShipToMobile": customer_phone,
                "ShipToPhone": customer_phone,
                "ShipToCustomerId": ""
            }

            # إرسال الطلب إلى SMSA
            endpoint = f"{self.api_base_url}/FulfilmentOrder"
            headers = {'Content-Type': 'application/json'}

            logger.info(f"إرسال طلب إنشاء شحنة إلى SMSA: {fulfilment_order_data}")
            response = requests.post(endpoint, json=fulfilment_order_data, headers=headers)

            # معالجة الاستجابة
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"استجابة SMSA: {response_data}")

                # التحقق من الاستجابة
                if response_data and isinstance(response_data, list) and len(response_data) > 0:
                    first_result = response_data[0]
                    if 'Orderid' in first_result:
                        tracking_number = first_result.get('Orderid')
                        return {
                            'success': True,
                            'tracking_number': tracking_number,
                            'response_data': response_data
                        }
                    else:
                        error_msg = first_result.get('Msg', 'لم يتم العثور على معرف الطلب في الاستجابة')
                        return {
                            'success': False,
                            'error': error_msg,
                            'response_data': response_data
                        }
                else:
                    return {
                        'success': False,
                        'error': "استجابة غير صالحة من SMSA API",
                        'response_data': response_data
                    }
            else:
                return {
                    'success': False,
                    'error': f"خطأ HTTP: {response.status_code} - {response.text}",
                    'response_data': response.text
                }

        except Exception as e:
            logger.exception(f"خطأ أثناء إنشاء شحنة SMSA: {str(e)}")
            return {
                'success': False,
                'error': f"استثناء: {str(e)}"
            }

    def track_shipment(self, shipment):
        """
        تتبع حالة الشحنة مع SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة التتبع (success, status, details, error)
        """
        try:
            # الحصول على معلومات الاعتماد من الحساب
            passkey = shipment.shipping_account.passkey

            if not passkey:
                return {
                    'success': False,
                    'error': "معلومات الاعتماد ناقصة (passkey)"
                }

            # تجهيز معلمات التتبع
            tracking_params = {
                'passkey': passkey,
                'Reference': shipment.tracking_number
            }

            # استدعاء API التتبع
            endpoint = f"{self.api_base_url}/Tracking"

            logger.info(f"طلب تتبع شحنة SMSA: {tracking_params}")
            response = requests.get(endpoint, params=tracking_params)

            if response.status_code == 200:
                tracking_data = response.json()
                logger.info(f"استجابة تتبع SMSA: {tracking_data}")

                # تفسير بيانات التتبع
                if tracking_data:
                    # استخراج آخر حالة
                    latest_status = self._extract_latest_status(tracking_data)

                    # تحويل حالة SMSA إلى حالة النظام
                    shipment_status = self._map_smsa_status_to_system(latest_status.get('status', ''))

                    return {
                        'success': True,
                        'status': shipment_status,
                        'details': tracking_data
                    }
                else:
                    return {
                        'success': True,
                        'status': shipment.status,  # الإبقاء على الحالة الحالية
                        'details': None,
                        'error': "لا توجد بيانات تتبع متاحة"
                    }
            else:
                return {
                    'success': False,
                    'error': f"خطأ HTTP: {response.status_code} - {response.text}"
                }

        except Exception as e:
            logger.exception(f"خطأ أثناء تتبع شحنة SMSA: {str(e)}")
            return {
                'success': False,
                'error': f"استثناء: {str(e)}"
            }

    def check_order_confirmation(self, shipment):
        """
        التحقق من حالة تأكيد الطلب في SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة التحقق
        """
        try:
            # الحصول على معلومات الاعتماد من الحساب
            passkey = shipment.shipping_account.passkey
            customer_id = shipment.shipping_account.customer_id
            warehouse_id = shipment.shipping_account.warehouse_id

            if not all([passkey, customer_id, warehouse_id]):
                return {
                    'success': False,
                    'error': "معلومات الاعتماد ناقصة"
                }

            # تجهيز معلمات الطلب
            params = {
                'passkey': passkey,
                'CustId': customer_id,
                'WrhId': warehouse_id,
                'orderreference': shipment.order.reference_number or f"ORD-{shipment.order.id}"
            }

            # استدعاء API التأكيد
            endpoint = f"{self.api_base_url}/FulfilmentOrderConfirmation"

            logger.info(f"طلب تأكيد طلب SMSA: {params}")
            response = requests.get(endpoint, params=params)

            if response.status_code == 200:
                confirmation_data = response.json()
                logger.info(f"استجابة تأكيد SMSA: {confirmation_data}")

                return {
                    'success': True,
                    'confirmation_data': confirmation_data
                }
            else:
                return {
                    'success': False,
                    'error': f"خطأ HTTP: {response.status_code} - {response.text}"
                }

        except Exception as e:
            logger.exception(f"خطأ أثناء التحقق من تأكيد طلب SMSA: {str(e)}")
            return {
                'success': False,
                'error': f"استثناء: {str(e)}"
            }

    def cancel_shipment(self, shipment):
        """
        إلغاء شحنة مع SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة الإلغاء (success, response_data, error)
        """
        # SMSA API لا يوفر واجهة مباشرة لإلغاء الشحنات حسب التوثيق المُقدم
        return {
            'success': False,
            'error': "وظيفة إلغاء الشحنة غير مدعومة حاليًا لـ SMSA"
        }

    def _extract_latest_status(self, tracking_data):
        """
        استخراج آخر حالة من بيانات التتبع

        المعلمات:
            tracking_data: بيانات التتبع من SMSA

        العائد:
            dict: آخر حالة (status, date, location, details)
        """
        if not tracking_data or not isinstance(tracking_data, list):
            return {'status': '', 'date': '', 'location': '', 'details': ''}

        # افتراض أن آخر عنصر في القائمة هو أحدث حالة
        latest = tracking_data[-1] if tracking_data else {}

        return {
            'status': latest.get('Status', ''),
            'date': latest.get('Date', ''),
            'location': latest.get('Location', ''),
            'details': latest.get('Details', '')
        }

    def _map_smsa_status_to_system(self, smsa_status):
        """
        تحويل حالة SMSA إلى حالة النظام

        المعلمات:
            smsa_status (str): حالة SMSA

        العائد:
            str: حالة النظام المقابلة
        """
        status_mapping = {
            'Shipment Created': 'submitted',
            'Picked Up': 'accepted',
            'In Transit': 'in_transit',
            'Out For Delivery': 'in_transit',
            'Delivered': 'delivered',
            'Returned': 'returned',
            'Cancelled': 'cancelled',
            'Exception': 'error'
        }

        return status_mapping.get(smsa_status, 'in_transit')

    def _format_phone_number(self, phone_number, country):
        """تنسيق رقم الهاتف حسب الدولة"""
        if country in self.nine_digits_countries and len(phone_number) == 9:
            return '0' + phone_number
        return phone_number

    def _get_warehouse_id(self, shipping_company_id, country, is_domestic=False):
        """الحصول على معرف المستودع المناسب للدولة"""
        try:
            mapping = WarehouseMapping.objects.get(
                shipping_company_id=shipping_company_id,
                country=country,
                is_domestic=is_domestic
            )
            return mapping.warehouse_id
        except WarehouseMapping.DoesNotExist:
            return None

    def _get_product_sku(self, product_id, country):
        """الحصول على SKU المناسب للمنتج والدولة"""
        try:
            mapping = ProductSKUMapping.objects.get(
                product_id=product_id,
                country=country
            )
            return mapping.sku
        except ProductSKUMapping.DoesNotExist:
            return None