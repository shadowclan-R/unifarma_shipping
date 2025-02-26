# shippers/tests/test_smsa_adapter.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
from shippers.models import ShippingCompany, ShippingCompanyAccount
from orders.models import Order, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

class SmsaAdapterTest(TestCase):
    def setUp(self):
        # إنشاء شركة شحن وحساب للاختبار
        self.company = ShippingCompany.objects.create(
            name="SMSA Express",
            code="smsa",
            is_active=True
        )

        self.account = ShippingCompanyAccount.objects.create(
            company=self.company,
            title="SMSA Test Account",
            account_type="international",
            api_base_url="https://sam.smsaexpress.com/STAXRestApi/api",
            passkey="DIQ@10077",
            customer_id="TEST_CUST",
            warehouse_id="TEST_WRH",
            is_active=True
        )

        # إنشاء طلب للاختبار
        self.order = Order.objects.create(
            citrix_deal_id="TEST123",
            reference_number="TEST-123",
            status="new",
            customer_name="Test Customer",
            customer_phone="123456789",
            shipping_country="Saudi Arabia",
            shipping_city="Riyadh",
            shipping_address="Test Address",
            total_amount=100.00,
            shipping_company=self.company,
            shipping_account=self.account
        )

        # إنشاء شحنة للاختبار
        self.shipment = Shipment.objects.create(
            order=self.order,
            shipping_company=self.company,
            shipping_account=self.account,
            status="pending"
        )

        # إنشاء كائن المحول
        self.adapter = SmsaAdapter()

    @patch('requests.post')
    def test_create_shipment_success(self, mock_post):
        # تجهيز Mock للاستجابة الناجحة
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"Msg": "Success", "Orderid": "123456789"}]
        mock_post.return_value = mock_response

        # اختبار إنشاء الشحنة
        result = self.adapter.create_shipment(self.shipment)

        # التحقق من النتائج
        self.assertTrue(result['success'])
        self.assertEqual(result['tracking_number'], "123456789")

        # التحقق من استدعاء API بشكل صحيح
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_create_shipment_error(self, mock_post):
        # تجهيز Mock للاستجابة الفاشلة
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # اختبار إنشاء الشحنة
        result = self.adapter.create_shipment(self.shipment)

        # التحقق من النتائج
        self.assertFalse(result['success'])
        self.assertIn("خطأ HTTP: 400", result['error'])

    @patch('requests.get')
    def test_track_shipment_success(self, mock_get):
        # تحديث الشحنة برقم تتبع
        self.shipment.tracking_number = "123456789"
        self.shipment.save()

        # تجهيز Mock للاستجابة الناجحة
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"Status": "Delivered", "Date": "2025-02-26", "Location": "Riyadh"}]
        mock_get.return_value = mock_response

        # اختبار تتبع الشحنة
        result = self.adapter.track_shipment(self.shipment)

        # التحقق من النتائج
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], "delivered")