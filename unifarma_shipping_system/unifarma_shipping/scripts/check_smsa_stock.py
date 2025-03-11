# scripts/check_smsa_stock.py
import os
import sys
import json
import requests

# Set the correct path for the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

import django
django.setup()

def check_smsa_stock():
    """Check the stock status of a specific product in SMSA"""
    print("\n=== Checking Stock Status in SMSA ===\n")

    # Enter the access key
    passkey = input("Enter the Passkey [default: DIQ@10077]: ") or "DIQ@10077"

    # Enter the customer ID
    customer_id = input("Enter the Customer ID (CustId) [default: UNIFARMA]: ") or "UNIFARMA"

    # Enter the warehouse ID
    warehouse_id = input("Enter the Warehouse ID (WrhId) [default: SMSA AE]: ") or "SMSA AE"

    # Enter the SKU (product code)
    sku = input("Enter the SKU (product code) [default: 9771210107001]: ") or "9771210107001"

    # Set up the request parameters
    stock_params = {
        'passkey': passkey,
        'CustId': customer_id,
        'WrhId': warehouse_id,
        'SKU': sku
    }

    # Send the request to the SMSA API
    api_url = "https://sam.smsaexpress.com/STAXRestApi/api/StockStatusDetail"

    print(f"\nSending stock status query to: {api_url}")
    print(f"Request parameters: {stock_params}")

    try:
        # Send the query request
        response = requests.get(api_url, params=stock_params)

        print(f"\nResponse Code: {response.status_code}")

        # Parse the response
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"\nSMSA Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                if response_data:
                    print("\n✅ Stock information retrieved successfully.")

                    # Display stock details
                    if isinstance(response_data, list):
                        for i, item in enumerate(response_data):
                            print(f"\nStock Information {i+1}:")
                            for key, value in item.items():
                                print(f"  {key}: {value}")
                    elif isinstance(response_data, dict):
                        print("\nStock Information:")
                        for key, value in response_data.items():
                            print(f"  {key}: {value}")
                else:
                    print("\n❌ No stock information found for this product.")
            except json.JSONDecodeError:
                print(f"\n❌ Invalid response (not JSON): {response.text}")
        else:
            print(f"\n❌ Error in response: {response.text}")

    except Exception as e:
        print(f"\n❌ An error occurred while connecting to the SMSA API: {str(e)}")

if __name__ == "__main__":
    check_smsa_stock()
