import os
import django
import sys
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount
from orders.models import Order, OrderItem, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

def test_smsa_shipping():
    print("بدء اختبار إرسال طلب شحن إلى SMSA...")

    try:
        company = ShippingCompany.objects.get(code="smsa")
        print(f"تم العثور على شركة شحن SMSA: {company.name}")
    except ShippingCompany.DoesNotExist:
        print("لم يتم العثور على شركة شحن SMSA. سيتم إنشاؤها...")
        company = ShippingCompany.objects.create(
            name="SMSA Express",
            code="smsa",
            is_active=True
        )

    try:
        account = ShippingCompanyAccount.objects.get(company=company, title__icontains="test")
        print(f"تم العثور على حساب شحن SMSA: {account.title}")
    except ShippingCompanyAccount.DoesNotExist:
        print("لم يتم العثور على حساب شحن SMSA. سيتم إنشاؤه...")
        account = ShippingCompanyAccount.objects.create(
            company=company,
            title="SMSA Test Account",
            account_type="international",
            api_base_url="https://sam.smsaexpress.com/STAXRestApi/api",
            passkey="DIQ@10077",
            customer_id="UNIFARMA",
            warehouse_id="SMSA AE",
            is_active=True
        )

    order = Order.objects.create(
        reference_number="TEST-ORDER-18962",
        citrix_deal_id="18962",
        status="approved",
        customer_name="Cesar Tarbay",
        customer_phone="+9613898696",
        customer_email="",
        shipping_country="Lebanon",
        shipping_city="Aitou",
        shipping_address="أيطو-ساحة أيطو-تمثال العذرا",
        shipping_postal_code="",
        total_amount=140.00,
        currency="USD",
        cod_amount=0.00,
        is_cod=False,
        shipping_company=company,
        shipping_account=account,
        citrix_created_at=timezone.now(),
        notes="طلب اختبار SMSA API - Lebanon"
    )

    item = OrderItem.objects.create(
        order=order,
        product_id="ROMA-RX",
        product_name="LIFE STREAM ROMA-RX LUBRICANT GEL",
        sku="9771210107001",
        quantity=3,
        unit_price=46.67,
        total_price=140.00
    )

    shipment = Shipment.objects.create(
        order=order,
        shipping_company=company,
        shipping_account=account,
        status="pending"
    )

    adapter = SmsaAdapter()
    result = adapter.create_shipment(shipment)

    print("\nنتيجة إرسال طلب الشحن:")
    print(f"نجاح: {result.get('success', False)}")

    if result.get('success', False):
        print(f"رقم التتبع: {result.get('tracking_number', 'غير متوفر')}")
        shipment.tracking_number = result.get('tracking_number')
        shipment.status = "submitted"
        shipment.save()
        print("تم تحديث الشحنة برقم التتبع")
    else:
        print(f"خطأ: {result.get('error', 'خطأ غير معروف')}")
        print(f"تفاصيل الاستجابة: {result.get('response_data', 'لا توجد بيانات')}")

    print("\nهل ترغب في مسح بيانات الاختبار؟ (y/n)")
    choice = input()
    if choice.lower() == 'y':
        shipment.delete()
        order.delete()
        print("تم مسح بيانات الاختبار")
    else:
        print(f"تم الاحتفاظ ببيانات الاختبار. معرف الطلب: {order.id}, معرف الشحنة: {shipment.id}")

if __name__ == "__main__":
    test_smsa_shipping()