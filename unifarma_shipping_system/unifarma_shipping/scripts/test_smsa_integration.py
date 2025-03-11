# scripts/test_smsa_integration.py
import os
import django
import sys
import json
from datetime import datetime, timedelta

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.utils import timezone
from shippers.models import ShippingCompany, ShippingCompanyAccount, WarehouseMapping, ProductSKUMapping
from orders.models import Order, OrderItem, Shipment
from shippers.adapters.smsa_adapter import SmsaAdapter

def setup_test_data():
    """Create test data."""
    # Create the SMSA shipping company
    company, created = ShippingCompany.objects.get_or_create(
        code="smsa",
        defaults={
            "name": "SMSA Express",
            "is_active": True
        }
    )

    # Create an SMSA account
    account, created = ShippingCompanyAccount.objects.get_or_create(
        company=company,
        title="SMSA Test Account",
        defaults={
            "account_type": "international",
            "api_base_url": "https://sam.smsaexpress.com/STAXRestApi/api/FulfilmentOrder",
            "passkey": "DIQ@10077",  # Temporary passkey for testing
            "customer_id": "10077",
            "warehouse_id": "1062",
            "is_active": True
        }
    )

    # Update the passkey if the account already existed
    if not created:
        account.passkey = "DIQ@10077"
        account.save(update_fields=['passkey'])

    # Create test orders for different countries
    test_countries = [
        {"code": "KSA", "name": "Saudi Arabia", "phone": "0501234567"},
        {"code": "UAE", "name": "United Arab Emirates", "phone": "501234567"},
        {"code": "Jordan", "name": "Jordan", "phone": "791234567"},
        {"code": "Bahrain", "name": "Bahrain", "phone": "31234567"},  # '0' will be added
        {"code": "Kuwait", "name": "Kuwait", "phone": "51234567"},    # '0' will be added
        {"code": "Qatar", "name": "Qatar", "phone": "31234567"}       # '0' will be added
    ]

    test_orders = []

    for i, country in enumerate(test_countries):
        order, created = Order.objects.get_or_create(
            reference_number=f"TEST-ORDER-{country['code']}",
            defaults={
                "citrix_deal_id": f"TEST{country['code']}",
                "status": "new",
                "customer_name": f"Test Customer {country['name']}",
                "customer_phone": country['phone'],
                "customer_email": f"test_{country['code'].lower()}@example.com",
                "shipping_country": country['name'],
                "shipping_city": "Capital",
                "shipping_address": f"Test Address, {country['name']}",
                "shipping_postal_code": "12345",
                "total_amount": 500.00,
                "cod_amount": 0.00,
                "is_cod": False,
                "shipping_company": company,
                "shipping_account": account,
                "citrix_created_at": timezone.now(),
                "notes": f"SMSA API Test Order - {country['name']}"
            }
        )

        # Create order items
        if created:
            OrderItem.objects.create(
                order=order,
                product_id="BLNC",  # Internal SKU for the product
                product_name="MOR BALANCE SOFTGEL CAPSULE GARLIC OIL",
                sku="BLNC",
                quantity=2,
                unit_price=100.00,
                total_price=200.00
            )

            OrderItem.objects.create(
                order=order,
                product_id="DOOM",  # Internal SKU for the product
                product_name="DOOM FIT",
                sku="DOOM",
                quantity=3,
                unit_price=100.00,
                total_price=300.00
            )

        test_orders.append(order)

    # Ensure SKU data exists
    if not ProductSKUMapping.objects.exists():
        # Call the data import script
        from scripts.import_smsa_data import import_skus
        import_skus()

    # Ensure warehouse data exists
    if not WarehouseMapping.objects.exists():
        # Call the data import script
        from scripts.import_smsa_data import import_warehouses
        import_warehouses()

    return {
        "company": company,
        "account": account,
        "orders": test_orders
    }

def test_phone_formatting():
    """Test phone number formatting."""
    adapter = SmsaAdapter()

    test_cases = [
        # [Original number, Country, Expected result]
        ["+966501234567", "Saudi Arabia", "501234567"],
        ["+97150123456", "United Arab Emirates", "50123456"],
        ["+96279123456", "Jordan", "79123456"],
        ["+97312345678", "Bahrain", "012345678"],   # Add '0' to make 9 digits
        ["+96551234567", "Kuwait", "051234567"],    # Add '0' to make 9 digits
        ["+97431234567", "Qatar", "031234567"],     # Add '0' to make 9 digits
        ["00966501234567", "Saudi Arabia", "501234567"],
        ["0501234567", "Saudi Arabia", "501234567"],
        ["501234567", "Saudi Arabia", "501234567"],
        ["501234567", "Bahrain", "0501234567"],     # Add '0' for Bahrain
    ]

    print("Testing phone number formatting...")

    for i, test_case in enumerate(test_cases):
        original = test_case[0]
        country = test_case[1]
        expected = test_case[2]

        result = adapter._format_phone_number(original, country)
        success = (result == expected)

        status = "✓" if success else "✗"
        print(f"{i+1}. {status} | Original: {original} | Country: {country} | Result: {result} | Expected: {expected}")

        if not success:
            print(f"   Phone number formatting error! Expected: {expected}, Got: {result}")

def test_create_shipment():
    """Test creating a shipment in SMSA."""
    print("\nStarting SMSA shipment creation test...")

    # Set up test data
    test_data = setup_test_data()

    # Test phone number formatting
    test_phone_formatting()

    # Test each order in different countries
    for order in test_data["orders"]:
        print(f"\nCreating a shipment test for country: {order.shipping_country}")
        print(f"Original phone number: {order.customer_phone}")

        # Create a shipment
        shipment = Shipment.objects.create(
            order=order,
            shipping_company=test_data["company"],
            shipping_account=test_data["account"],
            status="pending"
        )

        # Use the SMSA adapter
        adapter = SmsaAdapter()

        # Test phone number formatting
        formatted_phone = adapter._format_phone_number(order.customer_phone, order.shipping_country)
        print(f"Formatted phone number: {formatted_phone}")

        # Test getting the warehouse ID
        warehouse_id = adapter._get_warehouse_id(test_data["company"].id, order.shipping_country)
        print(f"Appropriate Warehouse ID: {warehouse_id}")

        # Test retrieving the product SKU
        for item in order.items.all():
            product_sku = adapter._get_product_sku(item.product_id, order.shipping_country)
            print(f"Product: {item.product_name}, Internal SKU: {item.product_id}, SMSA SKU: {product_sku}")

        # Create the shipment (comment this out so as not to send actual requests to SMSA)
        if False:  # Change to True to test sending an actual request
            result = adapter.create_shipment(shipment)

            # Display results
            print("\nShipment Creation Result:")
            print(f"Success: {result['success']}")

            if result['success']:
                print(f"Tracking Number: {result['tracking_number']}")

                # Update the shipment with the tracking number
                shipment.tracking_number = result['tracking_number']
                shipment.status = "submitted"
                shipment.save()
            else:
                print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_create_shipment()
