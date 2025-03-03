# test_bitrix_integration.py
import os
import django
import sys
import json
from pprint import pprint

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from crm_integration.services.bitrix24_service import Bitrix24Service
from crm_integration.models import CRMDealStage

def test_get_deals():
    """اختبار جلب الصفقات من سيتريكس 24"""
    print("بدء اختبار جلب الصفقات من Bitrix24...")

    # التأكد من وجود مراحل الشحن في قاعدة البيانات
    shipping_stages = CRMDealStage.objects.filter(is_shipping_stage=True)

    if not shipping_stages.exists():
        print("لا توجد مراحل شحن محددة. سيتم إنشاء مرحلة اختبار...")
        # إنشاء مرحلة شحن اختبارية - يجب تعديل هذه بالمراحل الفعلية
        CRMDealStage.objects.create(
            stage_id="C14:PREPARATION",
            name="تم الشحن مع الشركة",
            is_shipping_stage=True
        )
        shipping_stages = CRMDealStage.objects.filter(is_shipping_stage=True)

    # جلب معرفات مراحل الشحن
    shipping_stage_ids = list(shipping_stages.values_list('stage_id', flat=True))
    print(f"مراحل الشحن المحددة: {shipping_stage_ids}")

    # إنشاء خدمة Bitrix24
    service = Bitrix24Service()

    # جلب الصفقات
    deals = service.get_shipping_stage_deals(shipping_stage_ids)

    print(f"\nتم العثور على {len(deals)} صفقة في مراحل الشحن")

    # عرض قائمة الصفقات المنسقة
    formatted_deals = []
    for deal in deals:
        formatted_deal = service.build_deal_row_data(deal)
        formatted_deals.append(formatted_deal)

        # عرض ملخص للصفقة
        print("\n" + "-" * 50)
        print(f"معرف الصفقة: {formatted_deal['id']}")
        print(f"العنوان: {formatted_deal['title']}")
        print(f"العميل: {formatted_deal['customer_name']}")
        print(f"الدولة: {formatted_deal['country_id']}")
        print(f"شركة الشحن: {formatted_deal['shipping_company_id']}")
        print(f"المنتجات: {formatted_deal['products']}")
        print(f"الكميات: {formatted_deal['quantities']}")
        print(f"السعر: {formatted_deal['price']} {formatted_deal['currency']}")

    print("\n" + "=" * 50)
    print(f"إجمالي الصفقات: {len(formatted_deals)}")

    # يمكن إضافة المزيد من الإحصائيات هنا

    return formatted_deals

if __name__ == "__main__":
    test_get_deals()