# scripts/test_smsa_api_custom.py
import os
import sys
import json
import requests
from datetime import datetime, timedelta

# Set the correct path for the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

import django
django.setup()

def format_phone_number(phone_number, country):
    """
    Format the phone number based on the country.

    For Bahrain, Qatar, and Kuwait: add a '0' before the number (9 digits).
    For other countries: keep it as 8 digits.
    """
    if not phone_number:
        return ""

    # Remove the + if it exists at the beginning
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # Remove 00 if it exists at the beginning
    if phone_number.startswith('00'):
        phone_number = phone_number[2:]

    # Remove the country code
    if phone_number.startswith('961'):  # Lebanon
        phone_number = phone_number[3:]
    elif phone_number.startswith('966'):  # Saudi Arabia
        phone_number = phone_number[3:]
    elif phone_number.startswith('971'):  # UAE
        phone_number = phone_number[3:]
    elif phone_number.startswith('962'):  # Jordan
        phone_number = phone_number[3:]
    elif phone_number.startswith('973'):  # Bahrain
        phone_number = phone_number[3:]
    elif phone_number.startswith('974'):  # Qatar
        phone_number = phone_number[3:]
    elif phone_number.startswith('965'):  # Kuwait
        phone_number = phone_number[3:]

    # Add '0' for Bahrain, Qatar, and Kuwait if length is 8 digits
    nine_digits_countries = ['Bahrain', 'Qatar', 'Kuwait', 'البحرين', 'قطر', 'الكويت']
    if country in nine_digits_countries and len(phone_number) == 8:
        return "0" + phone_number

    return phone_number

def test_smsa_api_custom():
    """Custom test for sending an order to SMSA."""
    print("\n=== Custom Test for Sending an Order to the SMSA API ===\n")

    # Deal data from Bitrix24
    deal_data = {
        "id": "18962",
        "customer_name": "Cesar Tarbay",
        "phone": "+9613898696",
        "country": "Lebanon",
        "city": "Aitou",
        "address": "Aitou-Sahat Aitou-Virgin Mary Statue",
        "product": "ROMA-RX",
        "quantity": 3,
        "price": 140,
        "currency": "USD"
    }

    # Enter the access key
    passkey = input("\nEnter the Passkey [default: DIQ@10077]: ") or "DIQ@10077"

    # Enter the customer ID
    customer_id = input("Enter the Customer ID (CustId) [default: UNIFARMA]: ") or "UNIFARMA"

    # Show warehouse options
    print("\nAvailable Warehouses:")
    warehouses = {
        "1": {"id": "SMSA AE", "name": "SMSA UAE"},
        "2": {"id": "SMSA DOM AE CARGO", "name": "SMSA UAE - Domestic Shipment"},
        "3": {"id": "SMSA DOM KSA", "name": "SMSA Saudi Arabia - Domestic"},
        "4": {"id": "SMSA DOM KSA CARGO", "name": "SMSA Saudi Arabia - Domestic (Cargo)"},
        "5": {"id": "SMSA JO", "name": "SMSA Jordan"},
        "6": {"id": "SMSA DOM JO CARGO", "name": "SMSA Jordan - Domestic (Cargo)"}
    }

    for key, value in warehouses.items():
        print(f"{key}. {value['name']} ({value['id']})")

    warehouse_choice = input("\nChoose the warehouse number [default: 1]: ") or "1"
    warehouse_id = warehouses[warehouse_choice]["id"]
    print(f"Selected: {warehouses[warehouse_choice]['name']} ({warehouse_id})")

    # Optionally modify deal data
    print("\nCurrent deal data:")
    for key, value in deal_data.items():
        print(f"{key}: {value}")

    print("\nDo you want to modify the deal data? (y/n) ")
    if input().lower() == 'y':
        deal_data["id"] = input(f"Deal ID [default: {deal_data['id']}]: ") or deal_data["id"]
        deal_data["customer_name"] = input(f"Customer name [default: {deal_data['customer_name']}]: ") or deal_data["customer_name"]
        deal_data["phone"] = input(f"Phone number [default: {deal_data['phone']}]: ") or deal_data["phone"]
        deal_data["country"] = input(f"Country [default: {deal_data['country']}]: ") or deal_data["country"]
        deal_data["city"] = input(f"City [default: {deal_data['city']}]: ") or deal_data["city"]
        deal_data["address"] = input(f"Address [default: {deal_data['address']}]: ") or deal_data["address"]
        deal_data["product"] = input(f"Product [default: {deal_data['product']}]: ") or deal_data["product"]
        deal_data["quantity"] = int(input(f"Quantity [default: {deal_data['quantity']}]: ") or deal_data["quantity"])

    # Process phone number
    formatted_phone = format_phone_number(deal_data["phone"], deal_data["country"])
    print(f"\nOriginal phone number: {deal_data['phone']}")
    print(f"Formatted phone number: {formatted_phone}")

    # Shipping and cancellation dates
    ship_date = datetime.now()
    cancel_date = ship_date + timedelta(days=30)

    # Use the correct SKU for the product (from the attached file)
    product_sku = "9771210107001"  # SKU for ROMA-RX
    if deal_data["product"] != "ROMA-RX":
        product_sku = input(f"Enter the SKU for the product {deal_data['product']}: ")

    # Prepare the order data
    order_data = {
        "passkey": passkey,
        "CustId": customer_id,
        "WrhId": warehouse_id,
        "Refid": f"TEST-{deal_data['id']}",
        "codAmt": "0",  # Not COD
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
        "PONo": deal_data["id"],  # Use the deal ID as the order number
        "Shipdt": ship_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "CancelDate": cancel_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Notes": "Test order sent to SMSA API",
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

    # Print the order data
    print("\nOrder data being sent:")
    print(json.dumps(order_data, indent=2, ensure_ascii=False))

    # Ask the user whether to continue
    print("\nDo you want to send this order to SMSA? (y/n) ")
    choice = input()
    if choice.lower() != 'y':
        print("Operation canceled.")
        return

    # Send the request to the SMSA API
    api_url = "https://sam.smsaexpress.com/STAXRestApi/swagger/ui/index#!/FulfilmentOrder/FulfilmentOrder_FulfilmentOrderCreations"

    print(f"\nSending the order to: {api_url}")

    try:
        # Send the order
        response = requests.post(
            api_url,
            json=order_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"\nResponse Code: {response.status_code}")

        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nSMSA Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                first_result = response_data[0]
                if 'Orderid' in first_result:
                    tracking_number = first_result.get('Orderid')
                    print(f"\n✅ Shipment created successfully!")
                    print(f"🔢 Tracking Number: {tracking_number}")
                else:
                    error_msg = first_result.get('Msg', 'No order ID found in the response')
                    print(f"\n❌ Error: {error_msg}")
            else:
                print("\n❌ Invalid response from SMSA API")
        else:
            print(f"\n❌ Error in response: {response.text}")

    except Exception as e:
        print(f"\n❌ An error occurred while connecting to the SMSA API: {str(e)}")

if __name__ == "__main__":
    test_smsa_api_custom()
