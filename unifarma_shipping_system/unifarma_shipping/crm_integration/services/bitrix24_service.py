# crm_integration/services/bitrix24_service.py
import logging
import requests
from django.conf import settings
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

class Bitrix24Service:
    """خدمة للتكامل مع نظام Bitrix24 CRM"""

    def __init__(self):
        # إعداد روابط API
        self.urls = {
            'deal_fields': settings.BITRIX_DEAL_FIELDS_URL,
            'deal_list': settings.BITRIX_DEAL_LIST_URL,
            'deal_get': settings.BITRIX_DEAL_GET_BASE_URL,
            'deal_product_rows': settings.BITRIX_DEAL_PRODUCT_ROWS_URL,
            'deal_contact_items': settings.BITRIX_DEAL_CONTACT_ITEMS_URL,
            'contact_get': settings.BITRIX_CONTACT_GET_URL,
            'user_get': settings.BITRIX_USER_GET_URL,
            'stage_list': settings.BITRIX_STAGE_LIST_URL,
            'deal_update': settings.BITRIX_DEAL_UPDATE_URL
        }

        # قواميس التخزين المؤقت
        self.users_cache = {}
        self.stages_cache = {}
        self.countries_cache = {}
        self.shipping_companies_cache = {}

        # تحميل بيانات القواميس
        self._load_cached_data()

    def _load_cached_data(self):
        """تحميل بيانات القواميس المستخدمة بشكل متكرر"""
        try:
            # تحميل قائمة المراحل
            stages = self.get_stages_list()
            if stages:
                self.stages_cache = stages

            # يمكن إضافة تحميل بيانات إضافية هنا
            logger.info("تم تحميل البيانات المخزنة مؤقتًا بنجاح")
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات المخزنة مؤقتًا: {str(e)}")

    def _make_api_request(self, url, params=None, method="GET"):
        """
        تنفيذ طلب API مع معالجة الأخطاء
        """
        try:
            if method == "GET":
                response = requests.get(url, params=params)
            else:  # POST
                response = requests.post(url, json=params)

            response.raise_for_status()  # رفع استثناء في حالة وجود خطأ HTTP
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في طلب Bitrix24 API: {str(e)}")
            return None

    def get_shipping_stage_deals(self, shipping_stage_ids):
        """
        جلب الصفقات التي وصلت إلى مراحل الشحن المحددة

        المعلمات:
            shipping_stage_ids: قائمة بمعرفات مراحل الشحن

        العائد:
            list: قائمة بالصفقات المُسترجعة
        """
        if not shipping_stage_ids:
            logger.warning("لم يتم تحديد مراحل شحن للبحث")
            return []

        # إعداد معلمات الطلب
        params = {
            'filter[STAGE_ID]': shipping_stage_ids,
            'select[]': [
                'ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID',
                'DATE_CREATE', 'ASSIGNED_BY_ID', 'UF_CRM_1733571566',  # شركة الشحن
                'UF_CRM_1733571177',  # الدولة
                'UF_CRM_1734298491',  # المدينة
                'UF_CRM_1733571320',  # العنوان التفصيلي
                'UF_CRM_173357126',   # رقم التتبع
                'UF_CRM_1733572765',  # PNO
                'UF_CRM_1733581129585'  # حالة الموافقة
            ]
        }

        # طلب قائمة الصفقات
        result = self._make_api_request(self.urls['deal_list'], params)

        if not result or 'result' not in result:
            logger.error("فشل في جلب الصفقات من Bitrix24 CRM")
            return []

        deals = result.get('result', [])
        logger.info(f"تم العثور على {len(deals)} صفقة في مراحل الشحن المحددة")

        # جلب تفاصيل إضافية لكل صفقة
        detailed_deals = []
        for deal in deals:
            deal_details = self.get_deal_details(deal['ID'])
            if deal_details:
                detailed_deals.append(deal_details)

        return detailed_deals

    def get_deal_details(self, deal_id):
        """
        جلب تفاصيل كاملة لصفقة محددة بما فيها المنتجات وبيانات العميل

        المعلمات:
            deal_id: معرف الصفقة

        العائد:
            dict: تفاصيل الصفقة المُكمّلة
        """
        # جلب تفاصيل الصفقة الأساسية
        params = {'id': deal_id}
        deal_result = self._make_api_request(self.urls['deal_get'], params)

        if not deal_result or 'result' not in deal_result:
            logger.error(f"فشل في جلب تفاصيل الصفقة {deal_id}")
            return None

        deal_details = deal_result['result']

        # جلب المنتجات المرتبطة بالصفقة
        products = self.get_deal_products(deal_id)
        deal_details['PRODUCTS'] = products

        # جلب بيانات العميل
        contact_data = self.get_deal_contact(deal_id)
        if contact_data:
            deal_details['CLIENT_NAME'] = contact_data.get('NAME', '') + ' ' + contact_data.get('LAST_NAME', '')
            deal_details['CLIENT_PHONE'] = contact_data.get('PHONE', '')
            deal_details['CLIENT_EMAIL'] = contact_data.get('EMAIL', '')

        return deal_details

    def get_deal_products(self, deal_id):
        """
        جلب منتجات صفقة محددة

        المعلمات:
            deal_id: معرف الصفقة

        العائد:
            list: قائمة بمنتجات الصفقة
        """
        params = {'id': deal_id}
        product_result = self._make_api_request(self.urls['deal_product_rows'], params)

        if not product_result or 'result' not in product_result:
            logger.warning(f"لم يتم العثور على منتجات للصفقة {deal_id}")
            return []

        return product_result['result']

    def get_deal_contact(self, deal_id):
        """
        جلب بيانات العميل المرتبط بالصفقة

        المعلمات:
            deal_id: معرف الصفقة

        العائد:
            dict: بيانات العميل
        """
        # أولاً جلب معرف جهة الاتصال المرتبطة بالصفقة
        params = {'id': deal_id}
        contacts_result = self._make_api_request(self.urls['deal_contact_items'], params)

        if not contacts_result or 'result' not in contacts_result or not contacts_result['result']:
            logger.warning(f"لم يتم العثور على جهات اتصال للصفقة {deal_id}")
            return {}

        # استخدام أول جهة اتصال
        contact_id = contacts_result['result'][0].get('CONTACT_ID')
        if not contact_id:
            return {}

        # جلب تفاصيل جهة الاتصال
        params = {'id': contact_id}
        contact_result = self._make_api_request(self.urls['contact_get'], params)

        if not contact_result or 'result' not in contact_result:
            logger.warning(f"لم يتم العثور على تفاصيل جهة الاتصال {contact_id}")
            return {}

        return contact_result['result']

    def get_user_name(self, user_id):
        """
        جلب اسم المستخدم بناءً على المعرف مع دعم التخزين المؤقت

        المعلمات:
            user_id: معرف المستخدم

        العائد:
            str: اسم المستخدم الكامل
        """
        if not user_id:
            return "غير متوفر"

        # التحقق من وجود المستخدم في الذاكرة المؤقتة
        if user_id in self.users_cache:
            return self.users_cache[user_id]

        params = {'ID': user_id}
        user_result = self._make_api_request(self.urls['user_get'], params)

        if not user_result or 'result' not in user_result or not user_result['result']:
            return "غير متوفر"

        user = user_result['result'][0] if isinstance(user_result['result'], list) else user_result['result']
        user_name = f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip() or "غير متوفر"

        # تخزين اسم المستخدم في الذاكرة المؤقتة
        self.users_cache[user_id] = user_name

        return user_name

    def get_stages_list(self):
        """
        جلب قائمة مراحل الصفقات المتاحة

        العائد:
            dict: قاموس يربط معرف المرحلة باسمها
        """
        result = self._make_api_request(self.urls['stage_list'])

        if not result or 'result' not in result:
            logger.error("فشل في جلب قائمة مراحل الصفقات")
            return {}

        stages = {}
        for stage in result['result']:
            stages[stage['STATUS_ID']] = stage['NAME']

        return stages

    def update_deal_status(self, deal_id, status_field, status_value):
        """تحديث حالة الصفقة في Bitrix24"""
        data = {
            'id': deal_id,
            'fields': {
                status_field: status_value
            }
        }

        result = self._make_api_request(self.urls['deal_update'], data, method="POST")

        if not result or 'result' not in result:
            logger.error(f"فشل في تحديث حالة الصفقة {deal_id}")
            return False

        return True

    def build_deal_row_data(self, deal):
        """
        بناء بيانات الصفقة في تنسيق مناسب للاستخدام

        المعلمات:
            deal: بيانات الصفقة

        العائد:
            dict: بيانات الصفقة المنسقة
        """
        if not deal:
            return {}

        # الحصول على أسماء المنتجات وكمياتها وSKUs
        product_data = [(
            product.get('PRODUCT_NAME', ''),
            str(product.get('QUANTITY', '')),
            product.get('PRODUCT_ID', '')
        ) for product in deal.get('PRODUCTS', [])]

        # تجهيز بيانات الصفقة المنسقة
        formatted_deal = {
            'id': deal.get('ID', ''),
            'title': deal.get('TITLE', ''),
            'stage_id': deal.get('STAGE_ID', ''),
            'customer_name': deal.get('CLIENT_NAME', ''),
            'customer_phone': deal.get('CLIENT_PHONE', ''),
            'customer_email': deal.get('CLIENT_EMAIL', ''),
            'tracking_number': deal.get('UF_CRM_173357126', ''),
            'shipping_company_id': deal.get('UF_CRM_1733571566', ''),
            'country_id': deal.get('UF_CRM_1733571177', ''),
            'city': deal.get('UF_CRM_1734298491', ''),
            'address': deal.get('UF_CRM_1733571320', ''),
            'product_skus': [sku for _, _, sku in product_data],
            'products': ' | '.join(name for name, _, _ in product_data),
            'quantities': ' | '.join(qty for _, qty, _ in product_data),
            'price': deal.get('OPPORTUNITY', ''),
            'currency': deal.get('CURRENCY_ID', ''),
            'created_at': deal.get('DATE_CREATE', ''),
            'pno': deal.get('UF_CRM_1733572765', '') or deal.get('ID', ''),
            'assigned_by': self.get_user_name(deal.get('ASSIGNED_BY_ID', '')),
            'approval_status': deal.get('UF_CRM_1733581129585', ''),
            'raw_data': deal
        }

        return formatted_deal