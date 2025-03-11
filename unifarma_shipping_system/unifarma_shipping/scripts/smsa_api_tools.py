# smsa_api_production.py

import os
import json
import requests
from datetime import datetime, timedelta

# SMSA API Production Configuration
SMSA_API_BASE_URL = "https://sam.smsaexpress.com/STAXRestApiPrd/api"

# Credentials for different countries
SMSA_CREDENTIALS = {
    "KSA": {
        "passkey": "AC@10229",
        "cust_id": "10229",
        "wrh_id": "1062",
        "name": "GOLDEN ADVANCED COMPANY FZCO (KSA FULFILMENT)"
    },
    "UAE": {
        "passkey": "GA@10228",
        "cust_id": "10228",
        "wrh_id": "1071",
        "name": "GOLDEN ADVANCED COMPANY FZCO (DOM FULFILMENT)"
    },
    "JORDAN": {
        "passkey": "GC@10235",
        "cust_id": "10235",
        "wrh_id": "1076",
        "name": "GOLDEN ADVANCED COMPANY FZCO (JORDAN FULFILMENT)"
    }
}

# SKU Mapping for Products
SKU_MAPPING = {
    "KSA": {
        "ROMA-RX": "9771210107001",
        "BLNC": "8682655606701",
        "MOR": "8684215140243",
        "MOR GINSENG CAPSULE": "8684215140243",
        "PROSTA": "8684215140861",
        "VITTA": "8684215140878"
    },
    "UAE": {
        "ROMA-RX": "9771210107001",
        "BLNC": "8682655606701",
        "MOR": "8684215140243",
        "MOR GINSENG CAPSULE": "8684215140243",
        "PROSTA": "8684215140861",
        "VITTA": "8684215140878",
        "DOOM": "DOOM"
    },
    "JORDAN": {
        "ROMA-RX": "9771210107001",
        "BLNC": "8682655606701",
        "MOR": "8684215140243",
        "MOR GINSENG CAPSULE": "8684215140243",
        "PROSTA": "8684215140861",
        "VITTA": "8684215140878",
        "DOOM": "20957"
    }
}

# API Endpoints
ENDPOINTS = {
    "create_shipment": "/FulfilmentOrder",
    "check_confirmation": "/FulfilmentOrderConfirmation",
    "tracking": "/Tracking",
    "stock_status": "/StockStatusDetail"
}

# Mapping for special phone number handling
NINE_DIGITS_COUNTRIES = ["Bahrain", "Qatar", "Kuwait", "البحرين", "قطر", "الكويت"]

def format_phone_number(phone_number, country):
    """
    Format phone number based on country requirements.

    For Bahrain, Qatar, and Kuwait: add 0 before 8-digit numbers.
    """
    if not phone_number:
        return ""

    # Remove the + if it exists at the beginning
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # Remove 00 if it exists at the beginning
    if phone_number.startswith('00'):
        phone_number = phone_number[2:]

    # Remove country code
    country_codes = {
        '961': ['Lebanon', 'لبنان'],
        '966': ['Saudi Arabia', 'KSA', 'السعودية'],
        '971': ['UAE', 'United Arab Emirates', 'الإمارات'],
        '962': ['Jordan', 'الأردن'],
        '973': ['Bahrain', 'البحرين'],
        '974': ['Qatar', 'قطر'],
        '965': ['Kuwait', 'الكويت']
    }

    for code, countries in country_codes.items():
        if phone_number.startswith(code):
            phone_number = phone_number[len(code):]
            break

    # Add a 0 for Bahrain, Qatar, and Kuwait if the length is 8 digits
    if any(c in country for c in NINE_DIGITS_COUNTRIES) and len(phone_number) == 8:
        return "0" + phone_number

    return phone_number

def get_sku_for_product(product_name, country_code):
    """
    Get the correct SKU for a product based on the country.
    """
    if not country_code or not product_name:
        return ""

    # Standardize country code and product name
    country_code = country_code.upper()
    product_name = product_name.upper()

    # Get country-specific SKU mapping
    country_skus = SKU_MAPPING.get(country_code, {})

    # Try to find the SKU for the product
    sku = country_skus.get(product_name, "")

    return sku

def log_api_request(endpoint, params, response, success=True):
    """
    Log API request details for debugging and monitoring.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "endpoint": endpoint,
        "params": params,
        "status_code": response.status_code if hasattr(response, 'status_code') else None,
        "success": success,
        "response": response.text if hasattr(response, 'text') else str(response)
    }

    # In a production environment, you might want to log to a file or database
    # For now, we'll print to console
    print(f"[SMSA API LOG] {timestamp} | {endpoint} | Status: {'Success' if success else 'Failure'}")

    return log_entry

class SMSAApiClient:
    """
    Client for interacting with SMSA API in production environment.
    """

    def __init__(self, country_code="KSA"):
        """
        Initialize the SMSA API client.

        Args:
            country_code (str): Country code (KSA, UAE, JORDAN)
        """
        self.base_url = SMSA_API_BASE_URL
        self.country_code = country_code.upper()

        # Get credentials for the selected country
        if self.country_code not in SMSA_CREDENTIALS:
            raise ValueError(f"Unsupported country code: {country_code}. Supported countries: {', '.join(SMSA_CREDENTIALS.keys())}")

        self.credentials = SMSA_CREDENTIALS[self.country_code]
        self.passkey = self.credentials["passkey"]
        self.customer_id = self.credentials["cust_id"]
        self.warehouse_id = self.credentials["wrh_id"]

        # Request headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _build_url(self, endpoint):
        """
        Build the full URL for an API endpoint.
        """
        return f"{self.base_url}{endpoint}"

    def _send_request(self, method, endpoint, params=None, json_data=None):
        """
        Send a request to the SMSA API.

        Args:
            method (str): HTTP method (GET, POST)
            endpoint (str): API endpoint
            params (dict): Query parameters
            json_data (dict): JSON body for POST requests

        Returns:
            dict: Parsed response or error details
        """
        url = self._build_url(endpoint)

        # Add passkey to params if not already included
        if params is None:
            params = {}

        if "passkey" not in params:
            params["passkey"] = self.passkey

        # Add customer ID and warehouse ID if not already included
        if "CustId" not in params:
            params["CustId"] = self.customer_id

        if "WrhId" not in params:
            params["WrhId"] = self.warehouse_id

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, json=json_data, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log the request
            log_entry = log_api_request(endpoint, params, response, success=response.status_code < 400)

            # Parse response
            if response.status_code < 400:
                try:
                    return {"success": True, "data": response.json(), "status_code": response.status_code}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Invalid JSON in response", "response_text": response.text, "status_code": response.status_code}
            else:
                return {"success": False, "error": f"API Error: {response.status_code}", "response_text": response.text, "status_code": response.status_code}

        except requests.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            print(f"[SMSA API ERROR] {error_message}")
            return {"success": False, "error": error_message}

def create_shipment(self, shipment_data):
    """
    Create a new shipment in SMSA.

    Args:
        shipment_data (dict): Shipment details containing:
            - reference_id (str): Unique reference ID for the shipment
            - po_number (str): Purchase order number
            - recipient_name (str): Name of the recipient
            - recipient_phone (str): Phone number of the recipient
            - recipient_address (str): Address of the recipient
            - recipient_city (str): City of the recipient
            - recipient_country (str): Country of the recipient
            - product (str): Product name or SKU
            - quantity (int): Quantity of the product
            - cod_amount (str, optional): Cash on delivery amount
            - notes (str, optional): Additional notes

    Returns:
        dict: Response from SMSA API with tracking number or error details
    """
    # Validate required fields
    required_fields = [
        "reference_id", "recipient_name", "recipient_phone",
        "recipient_address", "recipient_city", "recipient_country",
        "product", "quantity"
    ]

    for field in required_fields:
        if field not in shipment_data or not shipment_data[field]:
            return {
                "success": False,
                "error": f"Missing required field: {field}"
            }

    # Format phone number based on country
    formatted_phone = format_phone_number(
        shipment_data["recipient_phone"],
        shipment_data["recipient_country"]
    )

    # Get SKU for the product
    product_name = shipment_data["product"]
    sku = shipment_data.get("sku")

    if not sku:
        sku = get_sku_for_product(product_name, self.country_code)

        if not sku:
            return {
                "success": False,
                "error": f"Unknown product '{product_name}' for country {self.country_code}"
            }

    # Set shipping and cancellation dates
    ship_date = datetime.now()
    cancel_date = ship_date + timedelta(days=30)

    # Prepare order items
    order_items = [{
        "orderId": 0,
        "SKU": sku,
        "quantity": int(shipment_data["quantity"]),
        "iLotNo": "",
        "serno": "",
        "iExpDate": ""
    }]

    # Prepare API parameters
    params = {
        "passkey": self.passkey,
        "CustId": self.customer_id,
        "WrhId": self.warehouse_id,
        "Refid": shipment_data["reference_id"],
        "codAmt": shipment_data.get("cod_amount", "0"),
        "PONo": shipment_data.get("po_number", shipment_data["reference_id"]),
        "Shipdt": ship_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "CancelDate": cancel_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "Notes": shipment_data.get("notes", ""),
        "ShipToName": shipment_data["recipient_name"],
        "ShipToAddress1": shipment_data["recipient_address"],
        "ShipToAddress2": shipment_data.get("recipient_address2", ""),
        "ShipToCity": shipment_data["recipient_city"],
        "ShipToZip": shipment_data.get("recipient_zip", ""),
        "ShipToCountry": shipment_data["recipient_country"],
        "ShipToMobile": formatted_phone,
        "ShipToPhone": formatted_phone,
        "ShipToCompany": shipment_data.get("recipient_company", ""),
        "shipToRecipientId": "",
        "ShipAccountNo": "",
        "ShipToCustomerId": ""
    }

    # Send the API request
    response = self._send_request(
        method="POST",
        endpoint=ENDPOINTS["create_shipment"],
        params=params,
        json_data=order_items
    )

    # Process response
    if response["success"] and "data" in response:
        data = response["data"]
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            if "Orderid" in first_result:
                tracking_number = first_result.get("Orderid")
                return {
                    "success": True,
                    "tracking_number": tracking_number,
                    "reference_id": shipment_data["reference_id"],
                    "raw_response": data
                }

        # If we can't extract tracking number from the response
        return {
            "success": False,
            "error": "Could not extract tracking number from response",
            "raw_response": data
        }

    return response

def track_shipment(self, tracking_number, date_range=None):
    """
    Track a shipment using its tracking number.

    Args:
        tracking_number (str): Tracking number or reference ID
        date_range (tuple, optional): Optional tuple of (from_date, to_date) in "YYYY-MM-DD" format

    Returns:
        dict: Tracking information or error details
    """
    if not tracking_number:
        return {
            "success": False,
            "error": "Tracking number is required"
        }

    # Prepare parameters
    params = {
        "passkey": self.passkey,
        "Reference": tracking_number
    }

    # Add date range if provided
    if date_range and len(date_range) == 2:
        from_date, to_date = date_range
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date

    # Send the API request
    response = self._send_request(
        method="GET",
        endpoint=ENDPOINTS["tracking"],
        params=params
    )

    # Process response
    if response["success"] and "data" in response:
        data = response["data"]

        # Handle different response formats
        if isinstance(data, list):
            if len(data) > 0:
                return {
                    "success": True,
                    "tracking_events": data,
                    "latest_status": data[-1].get("Status", "Unknown") if data else "No tracking information available"
                }
            else:
                return {
                    "success": False,
                    "error": "No tracking information found",
                    "tracking_events": []
                }
        elif isinstance(data, dict):
            # Check if there's an error message in the response
            for key in data:
                if "Failed" in key or "Error" in key:
                    return {
                        "success": False,
                        "error": key,
                        "raw_response": data
                    }

            # Otherwise, return the dictionary data
            return {
                "success": True,
                "tracking_data": data
            }
        else:
            return {
                "success": False,
                "error": "Unexpected response format",
                "raw_response": data
            }

    return response


def check_order_confirmation(self, reference_id):
    """
    Check the confirmation status of an order.

    Args:
        reference_id (str): Reference ID of the order

    Returns:
        dict: Confirmation status or error details
    """
    if not reference_id:
        return {
            "success": False,
            "error": "Reference ID is required"
        }

    # Prepare parameters
    params = {
        "passkey": self.passkey,
        "CustId": self.customer_id,
        "WrhId": self.warehouse_id,
        "orderreference": reference_id
    }

    # Send the API request
    response = self._send_request(
        method="GET",
        endpoint=ENDPOINTS["check_confirmation"],
        params=params
    )

    # Process response
    if response["success"] and "data" in response:
        data = response["data"]

        # Handle different response formats
        if isinstance(data, list):
            if len(data) > 0:
                return {
                    "success": True,
                    "confirmation_details": data
                }
            else:
                return {
                    "success": False,
                    "error": "No confirmation information found",
                    "confirmation_details": []
                }
        elif isinstance(data, dict):
            # Check if there's an error message in the response
            for key in data:
                if "Failed" in key or "Error" in key:
                    return {
                        "success": False,
                        "error": key,
                        "raw_response": data
                    }

            # Otherwise, return the dictionary data
            return {
                "success": True,
                "confirmation_data": data
            }
        else:
            return {
                "success": False,
                "error": "Unexpected response format",
                "raw_response": data
            }

    return response

def check_stock_status(self, sku):
    """
    Check the stock status of a product by SKU.

    Args:
        sku (str): Stock Keeping Unit (SKU) of the product

    Returns:
        dict: Stock status information or error details
    """
    if not sku:
        return {
            "success": False,
            "error": "SKU is required"
        }

    # Prepare parameters
    params = {
        "passkey": self.passkey,
        "CustId": self.customer_id,
        "WrhId": self.warehouse_id,
        "SKU": sku
    }

    # Send the API request
    response = self._send_request(
        method="GET",
        endpoint=ENDPOINTS["stock_status"],
        params=params
    )

    # Process response
    if response["success"] and "data" in response:
        data = response["data"]

        # Handle different response formats
        if isinstance(data, list):
            if len(data) > 0:
                return {
                    "success": True,
                    "stock_details": data
                }
            else:
                return {
                    "success": False,
                    "error": "No stock information found",
                    "stock_details": []
                }
        elif isinstance(data, dict):
            # Check if there's an error message in the response
            for key in data:
                if "Failed" in key or "Error" in key:
                    return {
                        "success": False,
                        "error": key,
                        "raw_response": data
                    }

            # Otherwise, return the dictionary data
            return {
                "success": True,
                "stock_data": data
            }
        else:
            return {
                "success": False,
                "error": "Unexpected response format",
                "raw_response": data
            }

    return response

def verify_passkey(self):
    """
    Verify if the passkey is valid by testing it with the Stock API.
    This is a good way to test connectivity and authorization.

    Returns:
        dict: Verification result with success status
    """
    # Use a common SKU to test the passkey
    common_skus = {
        "KSA": "9771210107001",  # ROMA-RX
        "UAE": "9771210107001",  # ROMA-RX
        "JORDAN": "9771210107001"  # ROMA-RX
    }

    test_sku = common_skus.get(self.country_code, "9771210107001")

    # Try to check stock status with this SKU
    result = self.check_stock_status(test_sku)

    if result["success"]:
        return {
            "success": True,
            "message": f"Passkey '{self.passkey}' is valid for {self.country_code}",
            "credentials": {
                "passkey": self.passkey,
                "customer_id": self.customer_id,
                "warehouse_id": self.warehouse_id
            }
        }
    else:
        return {
            "success": False,
            "message": f"Passkey verification failed: {result.get('error', 'Unknown error')}",
            "credentials": {
                "passkey": self.passkey,
                "customer_id": self.customer_id,
                "warehouse_id": self.warehouse_id
            },
            "details": result
        }

def example_usage():
    """
    Example of how to use the SMSA API client.
    """
    # Create a client for UAE shipments
    client = SMSAApiClient(country_code="UAE")

    # Verify the passkey
    verification = client.verify_passkey()
    if not verification["success"]:
        print(f"Passkey verification failed: {verification['message']}")
        return

    print(f"Passkey verified successfully: {verification['message']}")

    # Create a shipment
    shipment_data = {
        "reference_id": "ORDER-12345",
        "po_number": "PO-12345",
        "recipient_name": "John Doe",
        "recipient_phone": "+971501234567",
        "recipient_address": "Dubai, Business Bay, XYZ Building",
        "recipient_city": "Dubai",
        "recipient_country": "United Arab Emirates",
        "product": "MOR GINSENG CAPSULE",
        "quantity": 1,
        "notes": "Handle with care"
    }

    shipment_result = client.create_shipment(shipment_data)

    if shipment_result["success"]:
        print(f"Shipment created successfully!")
        print(f"Tracking number: {shipment_result['tracking_number']}")
        print(f"Reference ID: {shipment_result['reference_id']}")

        # Track the shipment
        tracking_result = client.track_shipment(shipment_result["tracking_number"])

        if tracking_result["success"]:
            print(f"Tracking information retrieved:")
            print(f"Latest status: {tracking_result['latest_status']}")

            if "tracking_events" in tracking_result:
                for i, event in enumerate(tracking_result["tracking_events"]):
                    print(f"Event {i+1}: {event.get('Status', 'Unknown')} - {event.get('Date', 'Unknown')}")
        else:
            print(f"Tracking failed: {tracking_result.get('error', 'Unknown error')}")

        # Check order confirmation
        confirmation_result = client.check_order_confirmation(shipment_result["reference_id"])

        if confirmation_result["success"]:
            print(f"Order confirmation retrieved.")
            print(f"Confirmation details: {confirmation_result.get('confirmation_details') or confirmation_result.get('confirmation_data')}")
        else:
            print(f"Confirmation check failed: {confirmation_result.get('error', 'Unknown error')}")
    else:
        print(f"Shipment creation failed: {shipment_result.get('error', 'Unknown error')}")

    # Check stock status for a product
    stock_result = client.check_stock_status("8684215140243")  # MOR GINSENG CAPSULE

    if stock_result["success"]:
        print(f"Stock information retrieved.")
        print(f"Stock details: {stock_result.get('stock_details') or stock_result.get('stock_data')}")
    else:
        print(f"Stock status check failed: {stock_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    example_usage()



