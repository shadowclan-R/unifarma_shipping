# scripts/check_smsa_confirmation.py
import os
import sys
import json
import requests

# Set the correct path for the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

import django
django.setup()

def check_smsa_confirmation():
    """Check the confirmation status of an SMSA order"""
    print("\n=== Checking SMSA Order Confirmation Status ===\n")

    # Enter the access key
    passkey = input("Enter the Passkey [default: DIQ@10077]: ") or "DIQ@10077"

    # Enter the customer ID
    customer_id = input("Enter the Customer ID (CustId) [default: UNIFARMA]: ") or "UNIFARMA"

    # Enter the warehouse ID
    warehouse_id = input("Enter the Warehouse ID (WrhId) [default: SMSA AE]: ") or "SMSA AE"

    # Enter the reference number
    reference_id = input("Enter the reference (Reference/RefId): ")
    if not reference_id:
        print("You must enter a reference number to continue.")
        return

    # Set up the request parameters
    confirmation_params = {
        'passkey': passkey,
        'CustId': customer_id,
        'WrhId': warehouse_id,
        'orderreference': reference_id
    }

    # Send request to the SMSA API
    api_url = "https://sam.smsaexpress.com/STAXRestApi/api/FulfilmentOrderConfirmation"

    print(f"\nSending confirmation request to: {api_url}")
    print(f"Request parameters: {confirmation_params}")

    try:
        # Send the query request
        response = requests.get(api_url, params=confirmation_params)

        print(f"\nResponse Code: {response.status_code}")

        # Parse the response
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"\nSMSA Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                if response_data:
                    print("\n✅ Successfully retrieved confirmation information.")

                    # Show confirmation details
                    if isinstance(response_data, list):
                        for i, item in enumerate(response_data):
                            print(f"\nConfirmation Information {i+1}:")
                            for key, value in item.items():
                                print(f"  {key}: {value}")
                    elif isinstance(response_data, dict):
                        print("\nConfirmation Information:")
                        for key, value in response_data.items():
                            print(f"  {key}: {value}")
                else:
                    print("\n❌ No confirmation information found for this reference.")
            except json.JSONDecodeError:
                print(f"\n❌ Invalid response (not JSON): {response.text}")
        else:
            print(f"\n❌ Error in response: {response.text}")

    except Exception as e:
        print(f"\n❌ An error occurred while connecting to the SMSA API: {str(e)}")

if __name__ == "__main__":
    check_smsa_confirmation()
