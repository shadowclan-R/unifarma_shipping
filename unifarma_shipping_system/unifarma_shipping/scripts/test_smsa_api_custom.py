# scripts/test_smsa_api_custom.py
import os
import sys
import json
import requests
from datetime import datetime, timedelta

# إعداد المسار الصحيح للتطبيق
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

import django
django.setup()

def format_phone_number(phone_number, country):
    """
    تنسيق رقم الهاتف حسب الدولة

    للبحرين وقطر والكويت: إضافة 0 قبل الرقم (9 أرقام)
    لباقي الدول: الاحتفاظ بـ 8 أرقام
    """
    if not phone_number:
        return ""

    # إزالة الـ + من بداية الرقم إن وجد
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # إزالة 00 من بداية الرقم إن وجد
    if phone_number.startswith('00'):
        phone_number = phone_number[2:]

    # إزالة رمز الدولة
    if phone_number.startswith('961'):  # لبنان
        phone_number = phone_number[3:]
    elif phone_number.startswith('966'):  # السعودية
        phone_number = phone_number[3:]
    elif phone_number.startswith('971'):  # الإمارات
        phone_number = phone_number[3:]
    elif phone_number.startswith('962'):  # الأردن
        phone_number = phone_number[3:]
    elif phone_number.startswith('973'):  # البحرين
        phone_number = phone_number[3:]
    elif phone_number.startswith('974'):  # قطر
        phone_number = phone_number[3:]
    elif phone_number.startswith('965'):  # الكويت
        phone_number = phone_number[3:]

    # إضافة 0 للبحرين وقطر والكويت إذا كان طول الرقم 8 أرقام
    nine_digits_countries = ['Bahrain', 'Qatar', 'Kuwait', 'البحرين', 'قطر', 'الكويت']
    if country in nine_digits_countries and len(phone_number) == 8:
        return "0" + phone_number

    return phone_number

def test_smsa_api_custom():
    """اختبار مخصص لإرسال طلب إلى SMSA"""
    print("\n=== اختبار مخصص لإرسال طلب إلى SMSA API ===\n")

    # بيانات الصفقة من Bitrix24
    deal_data = {
        "id": "18962",
        "customer_name": "Cesar Tarbay",
        "phone": "+9613898696",
        "country": "Lebanon",
        "city": "Aitou",
        "address": "أيطو-ساحة أيطو-تمثال العذرا",
        "product": "ROMA-RX",
        "quantity": 3,
        "price": 140,
        "currency": "USD"
    }

    # إدخال مفتاح الوصول
    passkey = input("\nأدخل مفتاح الوصول (Passkey) [افتراضي: DIQ@10077]: ") or "DIQ@10077"

    # إدخال معرف العميل
    customer_id = input("أدخل معرف العميل (CustId) [افتراضي: UNIFARMA]: ") or "UNIFARMA"

    # عرض خيارات المستودعات
    print("\nالمستودعات المتاحة:")
    warehouses = {
        "1": {"id": "SMSA AE", "name": "SMSA الإمارات"},
        "2": {"id": "SMSA DOM AE CARGO", "name": "SMSA الإمارات - شحن داخلي"},
        "3": {"id": "SMSA DOM KSA", "name": "SMSA السعودية - داخلي"},
        "4": {"id": "SMSA DOM KSA CARGO", "name": "SMSA السعودية - داخلي (بضائع)"},
        "5": {"id": "SMSA JO", "name": "SMSA الأردن"},
        "6": {"id": "SMSA DOM JO CARGO", "name": "SMSA الأردن - داخلي (بضائع)"}
    }

    for key, value in warehouses.items():
        print(f"{key}. {value['name']} ({value['id']})")

    warehouse_choice = input("\nاختر رقم المستودع [افتراضي: 1]: ") or "1"
    warehouse_id = warehouses[warehouse_choice]["id"]
    print(f"تم اختيار: {warehouses[warehouse_choice]['name']} ({warehouse_id})")

    # تعديل بيانات الصفقة (اختياري)
    print("\nبيانات الصفقة الحالية:")
    for key, value in deal_data.items():
        print(f"{key}: {value}")

    print("\nهل ترغب في تعديل بيانات الصفقة؟ (y/n) ")
    if input().lower() == 'y':
        deal_data["id"] = input(f"معرف الصفقة [افتراضي: {deal_data['id']}]: ") or deal_data["id"]
        deal_data["customer_name"] = input(f"اسم العميل [افتراضي: {deal_data['customer_name']}]: ") or deal_data["customer_name"]
        deal_data["phone"] = input(f"رقم الهاتف [افتراضي: {deal_data['phone']}]: ") or deal_data["phone"]
        deal_data["country"] = input(f"الدولة [افتراضي: {deal_data['country']}]: ") or deal_data["country"]
        deal_data["city"] = input(f"المدينة [افتراضي: {deal_data['city']}]: ") or deal_data["city"]
        deal_data["address"] = input(f"العنوان [افتراضي: {deal_data['address']}]: ") or deal_data["address"]
        deal_data["product"] = input(f"المنتج [افتراضي: {deal_data['product']}]: ") or deal_data["product"]
        deal_data["quantity"] = int(input(f"الكمية [افتراضي: {deal_data['quantity']}]: ") or deal_data["quantity"])

    # معالجة رقم الهاتف
    formatted_phone = format_phone_number(deal_data["phone"], deal_data["country"])
    print(f"\nرقم الهاتف الأصلي: {deal_data['phone']}")
    print(f"رقم الهاتف بعد التنسيق: {formatted_phone}")

    # تاريخ الشحن والإلغاء
    ship_date = datetime.now()
    cancel_date = ship_date + timedelta(days=30)

    # استخدام SKU المناسب للمنتج (من الملف المرفق)
    product_sku = "9771210107001"  # SKU للمنتج ROMA-RX
    if deal_data["product"] != "ROMA-RX":
        product_sku = input(f"أدخل SKU للمنتج {deal_data['product']}: ")

    # إعداد بيانات الطلب
    order_data = {
        "passkey": passkey,
        "CustId": customer_id,
        "WrhId": warehouse_id,
        "Refid": f"TEST-{deal_data['id']}",
        "codAmt": "0",  # ليس الدفع عند الاستلام
        "fforderitemCreations": [
            {
                "orderId": 0,
                "SKU": product_sku,
                "quantity": deal_data["quantity"],
                "iLotNo": "",
                "serno": "",
                "iExpDate": ""
            }
        ],
        "PONo": deal_data["id"],  # استخدام معرف الصفقة كرقم الطلب
        "Shipdt": ship_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "CancelDate": cancel_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Notes": "اختبار إرسال طلب إلى SMSA API",
        "shipToRecipientId": "",
        "ShipAccountNo": "",
        "ShipToName": deal_data["customer_name"],
        "ShipToCompany": "",
        "ShipToAddress1": deal_data["address"],
        "ShipToAddress2": "",
        "ShipToCity": deal_data["city"],
        "ShipToZip": "",
        "ShipToCountry": deal_data["country"],
        "ShipToMobile": formatted_phone,
        "ShipToPhone": formatted_phone,
        "ShipToCustomerId": ""
    }

    # طباعة بيانات الطلب
    print("\nبيانات الطلب المرسلة:")
    print(json.dumps(order_data, indent=2, ensure_ascii=False))

    # سؤال المستخدم للمتابعة
    print("\nهل ترغب في إرسال الطلب إلى SMSA؟ (y/n) ")
    choice = input()
    if choice.lower() != 'y':
        print("تم إلغاء العملية")
        return

    # إرسال الطلب إلى SMSA API
    api_url = "https://sam.smsaexpress.com/STAXRestApi/swagger/ui/index#!/FulfilmentOrder/FulfilmentOrder_FulfilmentOrderCreations"

    print(f"\nإرسال الطلب إلى: {api_url}")

    try:
        # إرسال الطلب
        response = requests.post(
            api_url,
            json=order_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nرمز الاستجابة: {response.status_code}")

        # تحليل الاستجابة
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nاستجابة SMSA: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                first_result = response_data[0]
                if 'Orderid' in first_result:
                    tracking_number = first_result.get('Orderid')
                    print(f"\n✅ تم إنشاء الشحنة بنجاح!")
                    print(f"🔢 رقم التتبع: {tracking_number}")
                else:
                    error_msg = first_result.get('Msg', 'لم يتم العثور على معرف الطلب في الاستجابة')
                    print(f"\n❌ خطأ: {error_msg}")
            else:
                print("\n❌ استجابة غير صالحة من SMSA API")
        else:
            print(f"\n❌ خطأ في الاستجابة: {response.text}")

    except Exception as e:
        print(f"\n❌ حدث خطأ أثناء الاتصال بـ SMSA API: {str(e)}")

if __name__ == "__main__":
    test_smsa_api_custom()