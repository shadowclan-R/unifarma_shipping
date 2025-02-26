# shippers/services.py
import logging
from .models import ShippingCompany, ShippingCompanyAccount
from crm_integration.models import CRMShippingMapping

logger = logging.getLogger(__name__)

class ShippingSelector:
    """خدمة لاختيار شركة الشحن المناسبة بناءً على معايير مختلفة"""

    def select_shipping_account(self, shipping_company=None, country=None, account_type=None):
        """
        اختيار حساب شركة الشحن المناسب بناءً على معايير متعددة

        المعلمات:
            shipping_company (str): قيمة حقل شركة الشحن من الصفقة
            country (str): الدولة المطلوب الشحن إليها
            account_type (str, optional): نوع الحساب المطلوب (داخلي، دولي، إلخ)

        العائد:
            ShippingCompanyAccount: حساب شركة الشحن المناسب أو None إذا لم يتم العثور
        """
        logger.info(f"البحث عن حساب شحن مناسب: company={shipping_company}, country={country}, type={account_type}")

        # 1. البحث أولاً في جدول التعيين لمعرفة ما إذا كان هناك تعيين محدد
        if shipping_company and country:
            mapping = CRMShippingMapping.objects.filter(
                crm_field='UF_CRM_SHIPPING_COMPANY',
                crm_value=shipping_company,
                is_active=True
            ).first()

            if mapping:
                logger.info(f"تم العثور على تعيين محدد: {mapping}")
                return mapping.shipping_company_account

        # 2. البحث بناءً على الدولة ونوع الحساب
        query = ShippingCompanyAccount.objects.filter(is_active=True)

        # تصفية بناءً على الشركة إذا تم تحديدها
        if shipping_company:
            query = query.filter(company__name__icontains=shipping_company)

        # تصفية بناءً على نوع الحساب
        if account_type:
            query = query.filter(account_type=account_type)

        # البحث عن حسابات تتعامل مع الدولة المحددة
        if country:
            # البحث أولاً في الحسابات المخصصة للدولة
            specific_account = query.filter(
                account_type='specific_country',
                specific_countries__contains=[country]
            ).first()

            if specific_account:
                logger.info(f"تم العثور على حساب مخصص للدولة: {specific_account}")
                return specific_account

            # ثم البحث في حسابات الشحن الداخلي (إذا كانت الدولة هي دولة الشركة) أو الدولي
            if self._is_domestic_country(country):
                domestic_account = query.filter(account_type='domestic').first()
                if domestic_account:
                    logger.info(f"تم العثور على حساب شحن داخلي: {domestic_account}")
                    return domestic_account
            else:
                international_account = query.filter(account_type='international').first()
                if international_account:
                    logger.info(f"تم العثور على حساب شحن دولي: {international_account}")
                    return international_account

        # إذا لم يتم العثور على حساب محدد، إرجاع أي حساب نشط
        default_account = query.first()
        if default_account:
            logger.info(f"تم العثور على حساب افتراضي: {default_account}")
            return default_account

        logger.warning("لم يتم العثور على حساب شحن مناسب!")
        return None

    def _is_domestic_country(self, country):
        """
        تحديد ما إذا كانت الدولة محلية (داخلية) أم لا
        يجب ضبط هذه المنطق حسب دولة الشركة
        """
        # يمكن استخدام إعدادات النظام أو قيمة ثابتة هنا
        domestic_country = "Saudi Arabia"  # أو استرجاع من الإعدادات
        return country.lower() == domestic_country.lower()