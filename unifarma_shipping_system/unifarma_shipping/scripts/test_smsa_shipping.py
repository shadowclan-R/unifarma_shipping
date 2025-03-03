# scripts/test_smsa_shipping.py
import os
import django
import sys
from datetime import datetime, timedelta

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount, ProductSKUMapping, WarehouseMapping
from orders.models import Order, OrderItem, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

def setup_test_data():
    """إعداد بيانات الاختبار"""
    print("إعداد بيانات الاختبار...")

    # إنشاء/الحصول على شركة SMSA
    company, created = ShippingCompany.objects.get_or_create(
        code="smsa",
        defaults={
            "name": "SMSA Express",
            "is_active": True
        }
    )
    print(f"شركة الشحن: {company.name} {'(تم إنشاؤها)' if created else '(موجودة)'}")

    # إنشاء/الحصول على حساب SMSA
    account, created = ShippingCompanyAccount.objects.get_or_create(
        company=company,
        title="SMSA Test Account",
        defaults={
            "account_type": "international",
            "api_base_url": "https://sam.smsaexpress.com/STAXRestApi/api",
            "passkey": "DIQ@10077",  # الباس كي التجريبي المرفق
            "customer_id": "UNIFARMA",  # هذا افتراضي، قد تحتاج إلى تغييره
            "warehouse_id": "SMSA AE",  # نستخدم مستودع الإمارات كافتراضي للبنان
            "is_active": True
        }
    )
    print(f"حساب الشحن: {account.title} {'(تم إنشاؤه)' if created else '(موجود)'}")

    # التأكد من وجود معرف المستودع المناسب
    warehouse, created = WarehouseMapping.objects.get_or_create(
        shipping_company=company,
        country_code="LBN",
        country_name="Lebanon",
        defaults={
            "warehouse_id": "SMSA AE",  # نستخدم مستودع الإمارات كافتراضي للبنان
            "warehouse_name": "SMSA UAE for Lebanon",
            "is_domestic": False,
            "is_cargo": False,
            "is_active": True
        }
    )
    print(f"معرف المستودع: {warehouse.warehouse_id} {'(تم إنشاؤه)' if created else '(موجود)'}")

    # التأكد من وجود SKU للمنتج
    sku_mapping, created = ProductSKUMapping.objects.get_or_create(
        product_id="ROMA-RX",
        defaults={
            "product_name": "LIFE STREAM ROMA-RX LUBRICANT GEL",
            "sku_internal": "ROMA-RX",
            "sku_smsa_ksa": "9771210107001",
            "sku_smsa_uae": "9771210107001",
            "sku_smsa_jordan": None,
            "sku_naqel": "ROMA-RX"
        }
    )
    print(f"SKU المنتج: {sku_mapping.sku_internal} {'(تم إنشاؤه)' if created else '(موجود)'}")

    # إنشاء طلب اختبار باستخدام البيانات المقدمة
    order, created = Order.objects.get_or_create(
        reference_number="TEST-ORDER-18962",
        defaults={
            "citrix_deal_id": "18962",
            "status": "approved",
            "customer_name": "Cesar Tarbay",
            "customer_phone": "+9613898696",
            "customer_email": "",
            "shipping_country": "Lebanon",
            "shipping_city": "Aitou",
            "shipping_address": "أيطو-ساحة أيطو-تمثال العذرا",
            "shipping_postal_code": "",
            "total_amount": 140.00,
            "currency": "USD",
            "cod_amount": 0.00,
            "is_cod": False,
            "shipping_company": company,
            "shipping_account": account,
            "citrix_created_at": timezone.now(),
            "notes": "طلب اختبار SMSA API - Lebanon"
        }
    )
    print(f"الطلب: {order.reference_number} {'(تم إنشاؤه)' if created else '(موجود)'}")

    # إنشاء عنصر الطلب إذا لم يكن موجودًا
    if created:
        item = OrderItem.objects.create(
            order=order,
            product_id="ROMA-RX",
            product_name="LIFE STREAM ROMA-RX LUBRICANT GEL",
            sku="9771210107001",  # من ملف SKU-SMSA_AND_NAQEL.pdf
            quantity=3,
            unit_price=46.67,  # 140 / 3
            total_price=140.00
        )
        print(f"تم إنشاء عنصر الطلب: {item.product_name} (الكمية: {item.quantity})")
    else:
        print("عناصر الطلب موجودة بالفعل")

    # إنشاء شحنة إذا لم تكن موجودة
    shipment, created = Shipment.objects.get_or_create(
        order=order,
        defaults={
            "shipping_company": company,
            "shipping_account": account,
            "status": "pending"
        }
    )
    print(f"الشحنة: {shipment.id} {'(تم إنشاؤها)' if created else '(موجودة)'}")

    return {
        "company": company,
        "account": account,
        "order": order,
        "shipment": shipment
    }

def test_smsa_shipping():
    """اختبار إرسال طلب شحن إلى SMSA"""
    print("\nبدء اختبار إرسال طلب شحن إلى SMSA...\n")

    # إعداد بيانات الاختبار
    test_data = setup_test_data()

    # طباعة معلومات الاختبار
    print("\nمعلومات الاختبار:")
    print(f"- معرف الطلب: {test_data['order'].id}")
    print(f"- معرف الشحنة: {test_data['shipment'].id}")
    print(f"- اسم العميل: {test_data['order'].customer_name}")
    print(f"- رقم الهاتف: {test_data['order'].customer_phone}")
    print(f"- الدولة: {test_data['order'].shipping_country}")
    print(f"- المدينة: {test_data['order'].shipping_city}")
    print(f"- العنوان: {test_data['order'].shipping_address}")
    print(f"- باس كي SMSA: {test_data['account'].passkey}")
    print(f"- معرف العميل: {test_data['account'].customer_id}")
    print(f"- معرف المستودع: {test_data['account'].warehouse_id}")

    # سؤال المستخدم للمتابعة
    print("\nهل ترغب في متابعة إرسال الطلب إلى SMSA؟ (y/n)")
    choice = input()
    if choice.lower() != 'y':
        print("تم إلغاء الاختبار")
        return

    # استخدام محول SMSA لإرسال الطلب
    print("\nإرسال الطلب إلى SMSA...")
    adapter = SmsaAdapter()
    result = adapter.create_shipment(test_data['shipment'])

    # عرض النتائج
    print("\nنتيجة إرسال طلب الشحن:")
    print(f"نجاح: {result.get('success', False)}")

    if result.get('success', False):
        print(f"رقم التتبع: {result.get('tracking_number', 'غير متوفر')}")

        # تحديث الشحنة برقم التتبع
        test_data['shipment'].tracking_number = result.get('tracking_number')
        test_data['shipment'].status = "submitted"
        test_data['shipment'].save()

        print("تم تحديث الشحنة برقم التتبع")
    else:
        print(f"خطأ: {result.get('error', 'خطأ غير معروف')}")
        if 'response_data' in result:
            print(f"تفاصيل الاستجابة: {result['response_data']}")

    # سؤال المستخدم لمسح بيانات الاختبار
    print("\nهل ترغب في مسح بيانات الاختبار؟ (y/n)")
    choice = input()
    if choice.lower() == 'y':
        # مسح بيانات الاختبار
        test_data['shipment'].delete()
        test_data['order'].delete()
        print("تم مسح بيانات الاختبار")
    else:
        print(f"تم الاحتفاظ ببيانات الاختبار.")

if __name__ == "__main__":
    test_smsa_shipping()