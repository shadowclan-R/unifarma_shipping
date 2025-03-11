# scripts/direct_smsa_test.py
import os
import django
import sys
import json
import requests
from datetime import datetime, timedelta

# Set up Django to access settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from django.conf import settings

def format_phone_number(phone_number):
    """
    Format the phone number by removing the country code.
    """
    if not phone_number:
        return ""

    # Remove the + if it exists at the beginning
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # Remove 00 if it exists at the beginning
    if phone_number.startswith('00'):
        phone_number = phone_number[2:]

    # Remove a specific country code (assumed 961 for Lebanon)
    if phone_number.startswith('961'):
        phone_number = phone_number[3:]

    return phone_number

def direct_smsa_test():
    """Direct test to send an order to SMSA."""
    print("Starting a direct test to send an order to SMSA...")

    # Use the passkey from the attached file
    passkey = "DIQ@10077"

    # Warehouse information
    warehouse_options = {
        "UAE": "SMSA AE",
        "KSA": "SMSA DOM KSA",
        "JORDAN": "SMSA JO"
    }

    print("\nChoose the appropriate warehouse for Lebanon:")
    for i, (country, warehouse_id) in enumerate(warehouse_options.items()):
        print(f"{i+1}. {country}: {warehouse_id}")

    choice = input("Number (default 1): ") or "1"
    warehouse_country = list(warehouse_options.keys())[int(choice) - 1]
    warehouse_id = warehouse_options[warehouse_country]

    print(f"Warehouse selected: {warehouse_id} ({warehouse_country})")

    # Customer information
    customer_id = input("\nEnter the Customer ID (default UNIFARMA): ") or "UNIFARMA"

    # Order information
    print("\nOrder Information:")
    reference_id = input("Reference number (default TEST-ORDER-18962): ") or "TEST-ORDER-18962"
    pono = input("PO number (default 18962): ") or "18962"
    sku = input("Product SKU (default 9771210107001): ") or "9771210107001"
    quantity = input("Quantity (default 3): ") or "3"

    # Recipient information
    print("\nRecipient Information:")
    customer_name = input("Customer name (default Cesar Tarbay): ") or "Cesar Tarbay"
    phone = input("Phone number (default +9613898696): ") or "+9613898696"
    formatted_phone = format_phone_number(phone)
    print(f"Phone number after formatting: {formatted_phone}")

    # Shipping information
    print("\nShipping Information:")
    country = input("Country (default Lebanon): ") or "Lebanon"
    city = input("City (default Aitou): ") or "Aitou"
    address = input("Address (default Aitou - Aitou Square - Virgin Mary Statue): ") or "Aitou - Aitou Square - Virgin Mary Statue"

    # Shipping and cancellation dates
    ship_date = datetime.now()
    cancel_date = ship_date + timedelta(days=30)

    # Prepare order data
    fulfilment_order_data = {
        "passkey": passkey,
        "CustId": customer_id,
        "WrhId": warehouse_id,
        "Refid": reference_id,
        "codAmt": "0",  # Not COD
        "fforderitemCreations": [
            {
                "orderId": 0,
                "SKU": sku,
                "quantity": int(quantity),
                "iLotNo": "",
                "serno": "",
                "iExpDate": ""
            }
        ],
        "PONo": pono,
        "Shipdt": ship_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "CancelDate": cancel_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Notes": "Direct test of SMSA API",
        "shipToRecipientId": "",
        "ShipAccountNo": "",
        "ShipToName": customer_name,
        "ShipToCompany": "",
        "ShipToAddress1": address,
        "ShipToAddress2": "",
        "ShipToCity": city,
        "ShipToZip": "",
        "ShipToCountry": country,
        "ShipToMobile": formatted_phone,
        "ShipToPhone": formatted_phone,
        "ShipToCustomerId": ""
    }

    # Print order data
    print("\nOrder Data:")
    print(json.dumps(fulfilment_order_data, indent=2, ensure_ascii=False))

    # Ask the user to continue
    print("\nDo you want to continue sending this order to SMSA? (y/n)")
    choice = input()
    if choice.lower() != 'y':
        print("Test canceled.")
        return

    # Send the request to SMSA
    api_url = "https://sam.smsaexpress.com/STAXRestApi/api/FulfilmentOrder"
    print(f"\nSending the order to: {api_url}")

    try:
        response = requests.post(
            api_url,
            json=fulfilment_order_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nResponse Code: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"SMSA Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                first_result = response_data[0]
                if 'Orderid' in first_result:
                    tracking_number = first_result.get('Orderid')
                    print("\n✅ Shipment created successfully!")
                    print(f"🔢 Tracking Number: {tracking_number}")
                else:
                    error_msg = first_result.get('Msg', 'No order ID found in the response.')
                    print(f"\n❌ Error: {error_msg}")
            else:
                print("\n❌ Invalid response from SMSA API.")
        else:
            print(f"\n❌ Error in response: {response.text}")

    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    direct_smsa_test()
