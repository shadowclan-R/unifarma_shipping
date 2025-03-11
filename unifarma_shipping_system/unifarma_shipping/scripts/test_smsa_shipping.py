# scripts/test_smsa_shipping.py
import os
import django
import sys
from datetime import datetime, timedelta

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount, ProductSKUMapping, WarehouseMapping
from orders.models import Order, OrderItem, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

def setup_test_data():
    """Set up test data."""
    print("Setting up test data...")

    # Create/Get the SMSA shipping company
    company, created = ShippingCompany.objects.get_or_create(
        code="smsa",
        defaults={
            "name": "SMSA Express",
            "is_active": True
        }
    )
    print(f"Shipping Company: {company.name} {'(Created)' if created else '(Exists)'}")

    # Create/Get the SMSA account
    account, created = ShippingCompanyAccount.objects.get_or_create(
        company=company,
        title="SMSA Test Account",
        defaults={
            "account_type": "international",
            "api_base_url": "https://sam.smsaexpress.com/STAXRestApi/api",
            "passkey": "DIQ@10077",  # The provided testing passkey
            "customer_id": "UNIFARMA",  # Default value; might need changing
            "warehouse_id": "SMSA AE",  # We'll use the UAE warehouse as default for Lebanon
            "is_active": True
        }
    )
    print(f"Shipping Account: {account.title} {'(Created)' if created else '(Exists)'}")

    # Ensure the appropriate warehouse ID exists
    warehouse, created = WarehouseMapping.objects.get_or_create(
        shipping_company=company,
        country_code="LBN",
        country_name="Lebanon",
        defaults={
            "warehouse_id": "SMSA AE",  # Using UAE warehouse as default for Lebanon
            "warehouse_name": "SMSA UAE for Lebanon",
            "is_domestic": False,
            "is_cargo": False,
            "is_active": True
        }
    )
    print(f"Warehouse ID: {warehouse.warehouse_id} {'(Created)' if created else '(Exists)'}")

    # Ensure the product SKU exists
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
    print(f"Product SKU: {sku_mapping.sku_internal} {'(Created)' if created else '(Exists)'}")

    # Create a test order using the provided data
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
            "shipping_address": "Aitou-Sahat Aitou-Virgin Mary Statue",
            "shipping_postal_code": "",
            "total_amount": 140.00,
            "currency": "USD",
            "cod_amount": 0.00,
            "is_cod": False,
            "shipping_company": company,
            "shipping_account": account,
            "citrix_created_at": timezone.now(),
            "notes": "SMSA API Test Order - Lebanon"
        }
    )
    print(f"Order: {order.reference_number} {'(Created)' if created else '(Exists)'}")

    # Create an order item if it doesn't exist
    if created:
        item = OrderItem.objects.create(
            order=order,
            product_id="ROMA-RX",
            product_name="LIFE STREAM ROMA-RX LUBRICANT GEL",
            sku="9771210107001",  # From SKU-SMSA_AND_NAQEL.pdf
            quantity=3,
            unit_price=46.67,  # 140 / 3
            total_price=140.00
        )
        print(f"Created order item: {item.product_name} (Quantity: {item.quantity})")
    else:
        print("Order items already exist.")

    # Create a shipment if it doesn't exist
    shipment, created = Shipment.objects.get_or_create(
        order=order,
        defaults={
            "shipping_company": company,
            "shipping_account": account,
            "status": "pending"
        }
    )
    print(f"Shipment: {shipment.id} {'(Created)' if created else '(Exists)'}")

    return {
        "company": company,
        "account": account,
        "order": order,
        "shipment": shipment
    }

def test_smsa_shipping():
    """Test sending a shipping request to SMSA."""
    print("\nStarting SMSA shipping test...\n")

    # Set up test data
    test_data = setup_test_data()

    # Print test info
    print("\nTest Information:")
    print(f"- Order ID: {test_data['order'].id}")
    print(f"- Shipment ID: {test_data['shipment'].id}")
    print(f"- Customer Name: {test_data['order'].customer_name}")
    print(f"- Phone Number: {test_data['order'].customer_phone}")
    print(f"- Country: {test_data['order'].shipping_country}")
    print(f"- City: {test_data['order'].shipping_city}")
    print(f"- Address: {test_data['order'].shipping_address}")
    print(f"- SMSA Passkey: {test_data['account'].passkey}")
    print(f"- Customer ID: {test_data['account'].customer_id}")
    print(f"- Warehouse ID: {test_data['account'].warehouse_id}")

    # Ask the user whether to proceed
    print("\nDo you want to proceed with sending the order to SMSA? (y/n)")
    choice = input()
    if choice.lower() != 'y':
        print("Test canceled.")
        return

    # Use the SMSA adapter to send the order
    print("\nSending the order to SMSA...")
    adapter = SmsaAdapter()
    result = adapter.create_shipment(test_data['shipment'])

    # Display results
    print("\nShipping request result:")
    print(f"Success: {result.get('success', False)}")

    if result.get('success', False):
        print(f"Tracking Number: {result.get('tracking_number', 'Unavailable')}")

        # Update the shipment with the tracking number
        test_data['shipment'].tracking_number = result.get('tracking_number')
        test_data['shipment'].status = "submitted"
        test_data['shipment'].save()

        print("Shipment updated with tracking number.")
    else:
        print(f"Error: {result.get('error', 'Unknown Error')}")
        if 'response_data' in result:
            print(f"Response details: {result['response_data']}")

    # Ask the user whether to clear test data
    print("\nDo you want to clear the test data? (y/n)")
    choice = input()
    if choice.lower() == 'y':
        # Clear test data
        test_data['shipment'].delete()
        test_data['order'].delete()
        print("Test data has been cleared.")
    else:
        print("Test data has been retained.")

if __name__ == "__main__":
    test_smsa_shipping()
