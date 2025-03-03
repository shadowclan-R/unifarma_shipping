# scripts/test_smsa_integration.py
import os
import django
import sys
import json
from datetime import datetime, timedelta

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount, WarehouseMapping, ProductSKUMapping
from orders.models import Order, OrderItem, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

def setup_test_data():
    """إنشاء بيانات اختبار"""
    # إنشاء شركة شحن SMSA
    company, created = ShippingCompany.objects.get_or_create(
        code="smsa",
        defaults={
            "name": "SMSA Express",
            "is_active": True
        }
    )

    # إنشاء حساب SMSA
    account, created = ShippingCompanyAccount.objects.get_or_create(
        company=company,
        title="SMSA Test Account",
        defaults={
            "account_type": "international",
            "api_base_url": "https://sam.smsaexpress.com/STAXRestApi/api",
            "passkey": "DIQ@10077",  # الباس كي المؤقت للاختبار
            "customer_id": "TEST_CUSTOMER",
            "warehouse_id": "TEST_WAREHOUSE",
            "is_active": True
        }
    )

    # تحديث قيمة passkey
    if not created:
        account.passkey = "DIQ@10077"
        account.save(update_fields=['passkey'])

    # إنشاء طلبات اختبار لدول مختلفة
    test_countries = [
        {"code": "KSA", "name": "Saudi Arabia", "phone": "0501234567"},
        {"code": "UAE", "name": "United Arab Emirates", "phone": "501234567"},
        {"code": "Jordan", "name": "Jordan", "phone": "791234567"},
        {"code": "Bahrain", "name": "Bahrain", "phone": "31234567"},  # سيتم إضافة 0 قبل الرقم
        {"code": "Kuwait", "name": "Kuwait", "phone": "51234567"},    # سيتم إضافة 0 قبل الرقم
        {"code": "Qatar", "name": "Qatar", "phone": "31234567"}       # سيتم إضافة 0 قبل الرقم
    ]

    test_orders = []

    for i, country in enumerate(test_countries):
        order, created = Order.objects.get_or_create(
            reference_number=f"TEST-ORDER-{country['code']}",
            defaults={
                "citrix_deal_id": f"TEST{country['code']}",
                "status": "new",
                "customer_name": f"عميل اختبار {country['name']}",
                "customer_phone": country['phone'],
                "customer_email": f"test_{country['code'].lower()}@example.com",
                "shipping_country": country['name'],
                "shipping_city": f"العاصمة",
                "shipping_address": f"عنوان اختبار، {country['name']}",
                "shipping_postal_code": "12345",
                "total_amount": 500.00,
                "cod_amount": 0.00,
                "is_cod": False,
                "shipping_company": company,
                "shipping_account": account,
                "citrix_created_at": timezone.now(),
                "notes": f"طلب اختبار SMSA API - {country['name']}"
            }
        )

        # إنشاء عناصر الطلب
        if created:
            OrderItem.objects.create(
                order=order,
                product_id="BLNC",  # SKU داخلي للمنتج
                product_name="MOR BALANCE SOFTGEL CAPSULE GARLIC OIL",
                sku="BLNC",
                quantity=2,
                unit_price=100.00,
                total_price=200.00
            )

            OrderItem.objects.create(
                order=order,
                product_id="DOOM",  # SKU داخلي للمنتج
                product_name="DOOM FIT",
                sku="DOOM",
                quantity=3,
                unit_price=100.00,
                total_price=300.00
            )

        test_orders.append(order)

    # التأكد من وجود بيانات SKUs
    if not ProductSKUMapping.objects.exists():
        # استدعاء سكربت استيراد البيانات
        from scripts.import_smsa_data import import_skus
        import_skus()

    # التأكد من وجود بيانات المستودعات
    if not WarehouseMapping.objects.exists():
        # استدعاء سكربت استيراد البيانات
        from scripts.import_smsa_data import import_warehouses
        import_warehouses()

    return {
        "company": company,
        "account": account,
        "orders": test_orders
    }

def test_phone_formatting():
    """اختبار تنسيق أرقام الهاتف"""
    adapter = SmsaAdapter()

    test_cases = [
        # [الرقم الأصلي, الدولة, النتيجة المتوقعة]
        ["+966501234567", "Saudi Arabia", "501234567"],
        ["+97150123456", "United Arab Emirates", "50123456"],
        ["+96279123456", "Jordan", "79123456"],
        ["+97312345678", "Bahrain", "012345678"],  # إضافة 0 لتصبح 9 أرقام
        ["+96551234567", "Kuwait", "051234567"],   # إضافة 0 لتصبح 9 أرقام
        ["+97431234567", "Qatar", "031234567"],    # إضافة 0 لتصبح 9 أرقام
        ["00966501234567", "Saudi Arabia", "501234567"],
        ["0501234567", "Saudi Arabia", "501234567"],
        ["501234567", "Saudi Arabia", "501234567"],
        ["501234567", "Bahrain", "0501234567"],    # إضافة 0 للبحرين
    ]

    print("اختبار تنسيق أرقام الهاتف...")

    for i, test_case in enumerate(test_cases):
        original = test_case[0]
        country = test_case[1]
        expected = test_case[2]

        result = adapter._format_phone_number(original, country)
        success = result == expected

        status = "✓" if success else "✗"
        print(f"{i+1}. {status} | الأصلي: {original} | الدولة: {country} | النتيجة: {result} | المتوقع: {expected}")

        if not success:
            print(f"   خطأ في تنسيق رقم الهاتف! المتوقع: {expected}, الفعلي: {result}")

def test_create_shipment():
    """اختبار إنشاء شحنة في SMSA"""
    print("\nبدء اختبار إنشاء شحنة SMSA...")

    # إعداد بيانات الاختبار
    test_data = setup_test_data()

    # اختبار تنسيق أرقام الهاتف
    test_phone_formatting()

    # اختبار كل طلب في دول مختلفة
    for order in test_data["orders"]:
        print(f"\nاختبار إنشاء شحنة للدولة: {order.shipping_country}")
        print(f"رقم الهاتف الأصلي: {order.customer_phone}")

        # إنشاء شحنة
        shipment = Shipment.objects.create(
            order=order,
            shipping_company=test_data["company"],
            shipping_account=test_data["account"],
            status="pending"
        )

        # استخدام محول SMSA
        adapter = SmsaAdapter()

        # اختبار تنسيق رقم الهاتف
        formatted_phone = adapter._format_phone_number(order.customer_phone, order.shipping_country)
        print(f"رقم الهاتف بعد التنسيق: {formatted_phone}")

        # اختبار الحصول على معرف المستودع
        warehouse_id = adapter._get_warehouse_id(test_data["company"].id, order.shipping_country)
        print(f"معرف المستودع المناسب: {warehouse_id}")

        # اختبار الحصول على SKU المنتج
        for item in order.items.all():
            product_sku = adapter._get_product_sku(item.product_id, order.shipping_country)
            print(f"المنتج: {item.product_name}, SKU الداخلي: {item.product_id}, SKU SMSA: {product_sku}")

        # إنشاء الشحنة (تعليق هذا الجزء حتى لا يتم إرسال طلبات فعلية لـ SMSA)
        if False:  # تغيير إلى True لاختبار إرسال طلب فعلي
            result = adapter.create_shipment(shipment)

            # عرض النتائج
            print("\nنتيجة إنشاء الشحنة:")
            print(f"نجاح: {result['success']}")

            if result['success']:
                print(f"رقم التتبع: {result['tracking_number']}")

                # تحديث الشحنة برقم التتبع
                shipment.tracking_number = result['tracking_number']
                shipment.status = "submitted"
                shipment.save()
            else:
                print(f"خطأ: {result['error']}")

if __name__ == "__main__":
    test_create_shipment()