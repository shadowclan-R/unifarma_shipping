# test_smsa_integration.py
import os
import django
import sys
import json
from datetime import datetime, timedelta

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount
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

    # إنشاء طلب اختبار
    order, created = Order.objects.get_or_create(
        reference_number="TEST-ORDER-123",
        defaults={
            "citrix_deal_id": "TEST123",
            "status": "new",
            "customer_name": "عميل الاختبار",
            "customer_phone": "966501234567",
            "customer_email": "test@example.com",
            "shipping_country": "Saudi Arabia",
            "shipping_city": "Riyadh",
            "shipping_address": "شارع الملك فهد، الرياض",
            "shipping_postal_code": "12345",
            "total_amount": 500.00,
            "cod_amount": 0.00,
            "is_cod": False,
            "shipping_company": company,
            "shipping_account": account,
            "citrix_created_at": timezone.now(),
            "notes": "طلب اختبار SMSA API"
        }
    )

    # إنشاء عناصر الطلب
    if created:
        OrderItem.objects.create(
            order=order,
            product_id="PROD-001",
            product_name="منتج اختبار 1",
            sku="SKU001",
            quantity=2,
            unit_price=100.00,
            total_price=200.00
        )

        OrderItem.objects.create(
            order=order,
            product_id="PROD-002",
            product_name="منتج اختبار 2",
            sku="SKU002",
            quantity=3,
            unit_price=100.00,
            total_price=300.00
        )

    # إرجاع البيانات للاختبار
    return {
        "company": company,
        "account": account,
        "order": order
    }

def test_create_shipment():
    """اختبار إنشاء شحنة في SMSA"""
    print("بدء اختبار إنشاء شحنة SMSA...")

    # إعداد بيانات الاختبار
    test_data = setup_test_data()
    order = test_data["order"]

    # إنشاء شحنة
    shipment = Shipment.objects.create(
        order=order,
        shipping_company=test_data["company"],
        shipping_account=test_data["account"],
        status="pending"
    )

    # استخدام محول SMSA
    adapter = SmsaAdapter()
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

        # اختبار تتبع الشحنة
        print("\nاختبار تتبع الشحنة...")
        tracking_result = adapter.track_shipment(shipment)
        print(f"نجاح التتبع: {tracking_result['success']}")
        if tracking_result['success']:
            print(f"حالة الشحنة: {tracking_result['status']}")
            print(f"تفاصيل التتبع: {json.dumps(tracking_result['details'], indent=2, ensure_ascii=False)}")

        # اختبار التحقق من تأكيد الطلب
        print("\nاختبار التحقق من تأكيد الطلب...")
        confirmation_result = adapter.check_order_confirmation(shipment)
        print(f"نجاح التحقق: {confirmation_result['success']}")
        if confirmation_result['success']:
            print(f"بيانات التأكيد: {json.dumps(confirmation_result.get('confirmation_data', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"خطأ: {result['error']}")
        print(f"استجابة API: {json.dumps(result.get('response_data', {}), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_create_shipment()