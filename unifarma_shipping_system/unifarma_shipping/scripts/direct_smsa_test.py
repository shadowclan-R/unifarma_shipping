# scripts/direct_smsa_test.py
import os
import django
import sys
import json
import requests
from datetime import datetime

# إعداد Django للوصول إلى الإعدادات
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.conf import settings

def direct_smsa_test():
    """اختبار مباشر لإرسال طلب إلى SMSA"""
    print("بدء اختبار مباشر لإرسال طلب إلى SMSA...")

    # استخدام الباس كي من الملف المرفق
    passkey = "DIQ@10077"

    # إعداد بيانات الطلب
    fulfilment_order_data = {
        "passkey": passkey,
        "CustId": "UNIFARMA",  # استخدام معرف عميل افتراضي
        "WrhId": "SMSA AE",    # استخدام مستودع الإمارات للبنان
        "Refid": "TEST-ORDER-18962",
        "codAmt": "0",  # ليس الدفع عند الاستلام
        "fforderitemCreations": [
            {
                "orderId": 0,
                "SKU": "9771210107001",  # SKU SMSA للمنتج ROMA-RX
                "quantity": 3,
                "iLotNo": "",
                "serno": "",
                "iExpDate": ""
            }
        ],
        "PONo": "18962",  # رقم الصفقة
        "Shipdt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "CancelDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S"),
        "Notes": "اختبار مباشر لـ SMSA API",
        "shipToRecipientId": "",
        "ShipAccountNo": "",
        "ShipToName": "Cesar Tarbay",
        "ShipToCompany": "",
        "ShipToAddress1": "أيطو-ساحة أيطو-تمثال العذرا",
        "ShipToAddress2": "",
        "ShipToCity": "Aitou",
        "ShipToZip": "",
        "ShipToCountry": "Lebanon",
        "ShipToMobile": "9613898696",  # إزالة رمز الدولة (+)
        "ShipToPhone": "9613898696",
        "ShipToCustomerId": ""
    }

    # طباعة بيانات الطلب
    print("\nبيانات الطلب:")
    print(json.dumps(fulfilment_order_data, indent=2, ensure_ascii=False))

    # سؤال المستخدم للمتابعة
    print("\nهل ترغب في متابعة إرسال الطلب إلى SMSA؟ (y/n)")
    choice = input()
    if choice.lower() != 'y':
        print("تم إلغاء الاختبار")
        return

    # إرسال الطلب إلى SMSA
    api_url = "https://sam.smsaexpress.com/STAXRestApi/api/FulfilmentOrder"
    print(f"\nإرسال الطلب إلى: {api_url}")

    try:
        response = requests.post(
            api_url,
            json=fulfilment_order_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nرمز الاستجابة: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"استجابة SMSA: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                first_result = response_data[0]
                if 'Orderid' in first_result:
                    tracking_number = first_result.get('Orderid')
                    print(f"تم إنشاء الشحنة بنجاح! رقم التتبع: {tracking_number}")
                else:
                    error_msg = first_result.get('Msg', 'لم يتم العثور على معرف الطلب في الاستجابة')
                    print(f"خطأ: {error_msg}")
            else:
                print("استجابة غير صالحة من SMSA API")
        else:
            print(f"خطأ في الاستجابة: {response.text}")

    except Exception as e:
        print(f"حدث خطأ: {str(e)}")

if __name__ == "__main__":
    direct_smsa_test()