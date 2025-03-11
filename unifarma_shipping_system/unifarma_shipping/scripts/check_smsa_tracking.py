# scripts/check_smsa_tracking.py
import os
import sys
import json
import requests

# Set the correct path for the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')

import django
django.setup()

def check_smsa_tracking():
    """Check the status of an SMSA order using a tracking number."""
    print("\n=== Checking SMSA Order Status ===\n")

    # Enter the access key
    passkey = input("Enter the Passkey [default: DIQ@10077]: ") or "DIQ@10077"

    # Enter the tracking number
    tracking_number = input("Enter the tracking number: ")
    if not tracking_number:
        print("A tracking number is required to continue.")
        return

    # Set up request parameters
    tracking_params = {
        'passkey': passkey,
        'Reference': tracking_number
    }

    # Send request to the SMSA API
    api_url = "https://sam.smsaexpress.com/STAXRestApi/api/Tracking"

    print(f"\nSending tracking request to: {api_url}")
    print(f"Request parameters: {tracking_params}")

    try:
        # Send the query request
        response = requests.get(api_url, params=tracking_params)

        print(f"\nResponse Code: {response.status_code}")

        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nSMSA Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response_data and isinstance(response_data, list):
                if len(response_data) > 0:
                    print("\n📦 Tracking Information:")
                    print("-" * 50)

                    # Display tracking info in chronological order
                    for i, event in enumerate(response_data):
                        status = event.get('Status', 'Unknown')
                        date = event.get('Date', 'Unknown')
                        location = event.get('Location', 'Unknown')
                        details = event.get('Details', 'Unknown')

                        print(f"{i+1}. Status: {status}")
                        print(f"   Date: {date}")
                        print(f"   Location: {location}")
                        print(f"   Details: {details}")
                        print("-" * 50)

                    # Display the latest status
                    latest_status = response_data[-1].get('Status', 'Unknown')
                    print(f"\n🔍 Latest Shipment Status: {latest_status}")
                else:
                    print("\n❌ No tracking information found for this number.")
            else:
                print("\n❌ Invalid response from SMSA API.")
        else:
            print(f"\n❌ Error in response: {response.text}")

    except Exception as e:
        print(f"\n❌ An error occurred while connecting to the SMSA API: {str(e)}")

if __name__ == "__main__":
    check_smsa_tracking()
