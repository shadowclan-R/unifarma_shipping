# crm_integration/services.py
import json
import logging
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import CRMAPICall, CRMDealStage, CRMShippingMapping
from orders.models import Order, OrderItem

logger = logging.getLogger(__name__)

class CitrixCRMService:
    """خدمة للتكامل مع نظام Citrix24 CRM"""

    def __init__(self):
        self.base_url = settings.CITRIX_API_BASE_URL
        self.api_key = settings.CITRIX_API_KEY
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def _make_api_request(self, endpoint, method="GET", params=None, data=None):
        """
        إجراء طلب API مع تسجيل التفاصيل
        """
        url = f"{self.base_url}/{endpoint}"

        # إنشاء سجل طلب API
        api_call = CRMAPICall.objects.create(
            call_type='get_deals' if 'deals' in endpoint and method == 'GET' else 'other',
            endpoint=endpoint,
            parameters=params,
            request_data=data
        )

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"طريقة غير مدعومة: {method}")

            # تحديث سجل طلب API بالاستجابة
            api_call.status_code = response.status_code
            api_call.response_data = response.json() if response.content else None

            if response.ok:
                api_call.status = 'success'
            else:
                api_call.status = 'error'
                api_call.error_message = f"HTTP Error: {response.status_code} - {response.text}"

            api_call.save()

            if not response.ok:
                logger.error(f"خطأ في طلب Citrix API: {response.status_code} - {response.text}")
                return None

            return response.json() if response.content else None

        except Exception as e:
            logger.exception(f"استثناء في طلب Citrix API: {str(e)}")
            api_call.status = 'error'
            api_call.error_message = str(e)
            api_call.save()
            return None

    def get_deals_with_shipping_stage(self):
        """
        جلب الصفقات التي وصلت إلى مرحلة 'تم الشحن مع الشركة'
        """
        # الحصول على معرفات مراحل الشحن المخزنة في قاعدة البيانات
        shipping_stages = CRMDealStage.objects.filter(is_shipping_stage=True).values_list('stage_id', flat=True)

        if not shipping_stages:
            logger.warning("لا توجد مراحل شحن محددة في قاعدة البيانات!")
            return []

        # تحضير معلمات الطلب للحصول على الصفقات في مرحلة الشحن
        params = {
            'filter[STAGE_ID]': shipping_stages,
            'filter[IS_PROCESSED]': 'N',  # صفقات غير معالجة (قد يختلف اسم الحقل حسب إعداد سيتريكس)
            'select[]': ['ID', 'TITLE', 'STAGE_ID', 'COMPANY_ID', 'CONTACT_ID',
                        'UF_CRM_SHIPPING_COMPANY', 'UF_CRM_SHIPPING_COUNTRY',
                        'UF_CRM_SHIPPING_ADDRESS', 'UF_CRM_COD_AMOUNT',
                        'OPPORTUNITY', 'CURRENCY_ID', 'UF_CRM_CUSTOMER_PHONE',
                        'UF_CRM_CUSTOMER_EMAIL', 'DATE_CREATE', 'PRODUCTS']
        }

        # استدعاء API للحصول على الصفقات
        result = self._make_api_request("crm.deal.list", method="GET", params=params)

        if not result or 'result' not in result:
            logger.error("فشل في جلب الصفقات من Citrix CRM")
            return []

        return result.get('result', [])

    def process_shipping_deals(self):
        """
        معالجة الصفقات الجديدة التي في مرحلة الشحن وإنشاء طلبات في النظام
        """
        deals = self.get_deals_with_shipping_stage()
        logger.info(f"تم العثور على {len(deals)} صفقة في مرحلة الشحن")

        processed_count = 0
        errors_count = 0

        for deal in deals:
            try:
                # التحقق من وجود الطلب مسبقًا
                deal_id = deal.get('ID')
                if Order.objects.filter(citrix_deal_id=deal_id).exists():
                    logger.info(f"الصفقة {deal_id} موجودة بالفعل في النظام - تخطي")
                    continue

                # إنشاء طلب جديد
                order = self._create_order_from_deal(deal)
                if order:
                    processed_count += 1

                    # تحديث حالة الصفقة في سيتريكس (وضع علامة كمعالجة)
                    self._update_deal_as_processed(deal_id)

                    logger.info(f"تم إنشاء طلب بنجاح من الصفقة {deal_id}")
                else:
                    errors_count += 1
                    logger.error(f"فشل في إنشاء طلب من الصفقة {deal_id}")

            except Exception as e:
                errors_count += 1
                logger.exception(f"خطأ في معالجة الصفقة: {str(e)}")

        return {
            "processed": processed_count,
            "errors": errors_count,
            "total": len(deals)
        }

    def _create_order_from_deal(self, deal):
        """
        إنشاء طلب جديد من بيانات الصفقة
        """
        from shippers.services import ShippingSelector

        # استخراج البيانات الرئيسية من الصفقة
        deal_id = deal.get('ID')
        shipping_company_field_value = deal.get('UF_CRM_SHIPPING_COMPANY')
        shipping_country = deal.get('UF_CRM_SHIPPING_COUNTRY')

        # استخدام خدمة اختيار شركة الشحن المناسبة
        shipping_selector = ShippingSelector()
        shipping_account = shipping_selector.select_shipping_account(
            shipping_company=shipping_company_field_value,
            country=shipping_country
        )

        if not shipping_account:
            logger.error(f"لم يتم العثور على حساب شحن مناسب للصفقة {deal_id}")
            return None

        # إنشاء الطلب
        try:
            # تحويل تاريخ الإنشاء من سيتريكس
            citrix_created_at = datetime.fromisoformat(deal.get('DATE_CREATE').replace('T', ' ').split('+')[0]) if deal.get('DATE_CREATE') else timezone.now()

            # المبالغ
            total_amount = float(deal.get('OPPORTUNITY', 0))
            cod_amount = float(deal.get('UF_CRM_COD_AMOUNT', 0))

            # إنشاء الطلب
            order = Order.objects.create(
                citrix_deal_id=deal_id,
                reference_number=f"CRM-{deal_id}",
                status='new',
                customer_name=deal.get('TITLE', ''),
                customer_phone=deal.get('UF_CRM_CUSTOMER_PHONE', ''),
                customer_email=deal.get('UF_CRM_CUSTOMER_EMAIL', ''),
                shipping_country=shipping_country,
                shipping_city=deal.get('UF_CRM_SHIPPING_CITY', ''),
                shipping_address=deal.get('UF_CRM_SHIPPING_ADDRESS', ''),
                shipping_postal_code=deal.get('UF_CRM_SHIPPING_POSTAL_CODE', ''),
                total_amount=total_amount,
                cod_amount=cod_amount,
                is_cod=cod_amount > 0,
                shipping_company=shipping_account.company,
                shipping_account=shipping_account,
                citrix_created_at=citrix_created_at,
                citrix_data=deal
            )

            # إضافة منتجات الطلب
            self._add_products_to_order(order, deal.get('PRODUCTS', []))

            return order

        except Exception as e:
            logger.exception(f"خطأ أثناء إنشاء الطلب من الصفقة {deal_id}: {str(e)}")
            return None

    def _add_products_to_order(self, order, products):
        """
        إضافة المنتجات إلى الطلب
        """
        if not products:
            return

        for product in products:
            try:
                # بيانات المنتج
                product_id = product.get('PRODUCT_ID')
                product_name = product.get('PRODUCT_NAME', '')
                sku = product.get('SKU', '')
                quantity = int(product.get('QUANTITY', 1))
                price = float(product.get('PRICE', 0))
                total = float(product.get('PRICE_EXCLUSIVE', 0))

                # إنشاء عنصر الطلب
                OrderItem.objects.create(
                    order=order,
                    product_id=product_id,
                    product_name=product_name,
                    sku=sku,
                    quantity=quantity,
                    unit_price=price,
                    total_price=total,
                    citrix_item_data=product
                )
            except Exception as e:
                logger.exception(f"خطأ أثناء إضافة المنتج إلى الطلب: {str(e)}")

    def _update_deal_as_processed(self, deal_id):
        """
        تحديث حالة الصفقة في سيتريكس كمعالجة
        """
        data = {
            'id': deal_id,
            'fields': {
                'IS_PROCESSED': 'Y'  # قد يختلف اسم الحقل حسب إعداد سيتريكس
            }
        }

        return self._make_api_request("crm.deal.update", method="POST", data=data)