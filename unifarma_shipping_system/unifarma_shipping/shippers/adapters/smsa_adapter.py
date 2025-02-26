# shippers/adapters/smsa_adapter.py
import logging
import requests
from django.utils import timezone
from .base_adapter import ShippingAdapter

logger = logging.getLogger(__name__)

class SmsaAdapter(ShippingAdapter):
    """محول للتكامل مع شركة SMSA Stax API"""

    def __init__(self):
        self.api_base_url = "https://sam.smsaexpress.com/STAXRestApi/api"

    def create_shipment(self, shipment):
        """
        إنشاء شحنة جديدة مع SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة العملية (success, tracking_number, response_data, error)
        """
        try:
            # الحصول على معلومات الاعتماد من الحساب
            passkey = shipment.shipping_account.passkey
            customer_id = shipment.shipping_account.customer_id
            warehouse_id = shipment.shipping_account.warehouse_id

            if not all([passkey, customer_id, warehouse_id]):
                return {
                    'success': False,
                    'error': "معلومات الاعتماد ناقصة (passkey, customer_id, warehouse_id)"
                }

            # الحصول على بيانات الطلب
            order = shipment.order

            # تجهيز بيانات عناصر الطلب
            order_items = []
            for item in order.items.all():
                order_item = {
                    "orderId": 0,  # سيتم ملؤه بواسطة SMSA
                    "SKU": item.sku or item.product_id,
                    "quantity": item.quantity,
                    "iLotNo": item.lot_number or "",
                    "serno": item.serial_number or "",
                    "iExpDate": item.expiry_date.isoformat() if item.expiry_date else ""
                }
                order_items.append(order_item)

            # تجهيز بيانات الطلب
            fulfilment_order_data = {
                "passkey": passkey,
                "CustId": customer_id,
                "WrhId": warehouse_id,
                "Refid": order.reference_number or f"ORD-{order.id}",
                "codAmt": str(order.cod_amount) if order.is_cod else "0",
                "fforderitemCreations": order_items,
                "PONo": order.reference_number or f"ORD-{order.id}",
                "Shipdt": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "CancelDate": (timezone.now() + timezone.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S"),
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
                "ShipToMobile": order.customer_phone or "",
                "ShipToPhone": order.customer_phone or "",
                "ShipToCustomerId": ""
            }

            # إرسال الطلب إلى SMSA
            endpoint = f"{self.api_base_url}/FulfilmentOrder"
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(endpoint, json=fulfilment_order_data, headers=headers)

            if response.status_code == 200:
                response_data = response.json()

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
            response = requests.get(endpoint, params=tracking_params)

            if response.status_code == 200:
                tracking_data = response.json()

                # تفسير بيانات التتبع (يجب تعديل هذا بناءً على هيكل استجابة SMSA الفعلي)
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

    def cancel_shipment(self, shipment):
        """
        إلغاء شحنة مع SMSA

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة الإلغاء (success, response_data, error)
        """
        # هذه الدالة ستحتاج إلى تنفيذ إذا كان SMSA يوفر واجهة لإلغاء الشحنات
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
        # هذه الدالة يجب تعديلها بناءً على هيكل استجابة SMSA الفعلي
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
        # هذه الدالة يجب ضبطها بناءً على حالات SMSA الفعلية
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