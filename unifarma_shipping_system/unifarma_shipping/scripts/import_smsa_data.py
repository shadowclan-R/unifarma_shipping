# scripts/import_smsa_data.py
import os
import django
import sys
import csv
from collections import defaultdict

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unifarma_shipping.settings')
django.setup()

from shippers.models import ShippingCompany, WarehouseMapping, ProductSKUMapping

def import_warehouses():
    """Import warehouse data from the attached file."""
    print("Importing warehouse data...")

    # Get or create the SMSA shipping company
    smsa, created = ShippingCompany.objects.get_or_create(
        code="smsa",
        defaults={
            "name": "SMSA Express",
            "is_active": True
        }
    )

    # Warehouse data from the attached file
    warehouses_data = [
        # UAE
        {
            'country_code': 'UAE',
            'country_name': 'United Arab Emirates',
            'warehouse_id': 'SMSA AE',
            'warehouse_name': 'SMSA UAE',
            'is_domestic': False,
            'is_cargo': False
        },
        {
            'country_code': 'UAE',
            'country_name': 'United Arab Emirates',
            'warehouse_id': 'SMSA DOM AE CARGO',
            'warehouse_name': 'SMSA UAE Domestic Cargo',
            'is_domestic': True,
            'is_cargo': True
        },
        # KSA
        {
            'country_code': 'KSA',
            'country_name': 'Saudi Arabia',
            'warehouse_id': 'SMSA DOM KSA',
            'warehouse_name': 'SMSA KSA Domestic',
            'is_domestic': True,
            'is_cargo': False
        },
        {
            'country_code': 'KSA',
            'country_name': 'Saudi Arabia',
            'warehouse_id': 'SMSA DOM KSA CARGO',
            'warehouse_name': 'SMSA KSA Domestic Cargo',
            'is_domestic': True,
            'is_cargo': True
        },
        # JORDAN
        {
            'country_code': 'JORDAN',
            'country_name': 'Jordan',
            'warehouse_id': 'SMSA JO',
            'warehouse_name': 'SMSA Jordan',
            'is_domestic': False,
            'is_cargo': False
        },
        {
            'country_code': 'JORDAN',
            'country_name': 'Jordan',
            'warehouse_id': 'SMSA DOM JO CARGO',
            'warehouse_name': 'SMSA Jordan Domestic Cargo',
            'is_domestic': True,
            'is_cargo': True
        }
    ]

    # Add or update warehouse data
    for warehouse_data in warehouses_data:
        warehouse, created = WarehouseMapping.objects.update_or_create(
            shipping_company=smsa,
            country_code=warehouse_data['country_code'],
            warehouse_id=warehouse_data['warehouse_id'],
            defaults={
                'country_name': warehouse_data['country_name'],
                'warehouse_name': warehouse_data['warehouse_name'],
                'is_domestic': warehouse_data['is_domestic'],
                'is_cargo': warehouse_data['is_cargo'],
                'is_active': True
            }
        )

        action = "Created" if created else "Updated"
        print(f"{action} warehouse: {warehouse}")

    print(f"Successfully imported {len(warehouses_data)} warehouses.")


def import_skus():
    """Import SKU data from the attached file."""
    print("Importing SKU data...")

    # SKU data from the attached file
    skus_data = [
        {
            'product_name': 'MOR BALANCE SOFTGEL CAPSULE GARLIC OIL',
            'sku_internal': 'BLNC',
            'sku_smsa_ksa': '8682655606701',
            'sku_smsa_uae': '8682655606701',
            'sku_smsa_jordan': None,
            'sku_naqel': 'BLNC'
        },
        {
            'product_name': 'MOR GINSENG CAPSULE 500MG',
            'sku_internal': 'MOR',
            'sku_smsa_ksa': '8684215140243',
            'sku_smsa_uae': '8684215140243',
            'sku_smsa_jordan': None,
            'sku_naqel': 'MOR'
        },
        {
            'product_name': 'MOR PROSTAMIN PROSTATE CAPSULE',
            'sku_internal': 'PROSTA',
            'sku_smsa_ksa': '8684215140861',
            'sku_smsa_uae': '8684215140861',
            'sku_smsa_jordan': None,
            'sku_naqel': 'PROSTA'
        },
        {
            'product_name': 'Mor diavitta for diabetes capsule 30',
            'sku_internal': 'VITTA',
            'sku_smsa_ksa': '8684215140878',
            'sku_smsa_uae': '8684215140878',
            'sku_smsa_jordan': None,
            'sku_naqel': 'VITTA'
        },
        {
            'product_name': 'LIFE STREAM ROMA-RX LUBRICANT GEL',
            'sku_internal': 'ROMA-RX',
            'sku_smsa_ksa': '9771210107001',
            'sku_smsa_uae': '9771210107001',
            'sku_smsa_jordan': None,
            'sku_naqel': 'ROMA-RX'
        },
        {
            'product_name': 'SUPPLEMENT FOOD Alıç',
            'sku_internal': 'ALC',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957000103',
            'sku_smsa_jordan': None,
            'sku_naqel': 'ALC'
        },
        {
            'product_name': 'BITTER MELON PROPOLIS',
            'sku_internal': 'BITT',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957000707',
            'sku_smsa_jordan': None,
            'sku_naqel': 'BITT'
        },
        {
            'product_name': 'CREM Hitman Delay',
            'sku_internal': 'DELA',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8683020070387',
            'sku_smsa_jordan': None,
            'sku_naqel': 'DELA'
        },
        {
            'product_name': 'SUPPLEMENT FOOD DIAPLUS',
            'sku_internal': 'DIA',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957005061',
            'sku_smsa_jordan': None,
            'sku_naqel': 'DIA'
        },
        {
            'product_name': 'DOOM FIT',
            'sku_internal': 'DOOM',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': 'DOOM',
            'sku_smsa_jordan': '20957',
            'sku_naqel': 'DOOM'
        },
        {
            'product_name': 'CREM Hitman Erection',
            'sku_internal': 'EREC',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8683020070493',
            'sku_smsa_jordan': None,
            'sku_naqel': 'EREC'
        },
        {
            'product_name': 'SUPPLEMENT FOOD',
            'sku_internal': 'GNS',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957980047',
            'sku_smsa_jordan': None,
            'sku_naqel': 'GNS'
        },
        {
            'product_name': 'SUPPLEMENT FOOD HEMOUT',
            'sku_internal': 'HEMO',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957003975',
            'sku_smsa_jordan': None,
            'sku_naqel': 'HMT'
        },
        {
            'product_name': 'LOTUS PREMIUM HONEY',
            'sku_internal': 'LOTU',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8697623204964',
            'sku_smsa_jordan': None,
            'sku_naqel': 'LOTU'
        },
        {
            'product_name': 'BALEN OPTIMAC VITAMIN',
            'sku_internal': 'OPT',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': '8690957002909',
            'sku_smsa_jordan': None,
            'sku_naqel': 'OPT'
        },
        {
            'product_name': 'SUPPLEMENT FOOD Perst',
            'sku_internal': 'PERS',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': None,
            'sku_smsa_jordan': None,
            'sku_naqel': 'PERS'
        },
        {
            'product_name': 'FILL HAGE FILLER',
            'sku_internal': 'FLR',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': None,
            'sku_smsa_jordan': None,
            'sku_naqel': None
        },
        {
            'product_name': 'COSAKONDR',
            'sku_internal': 'COSA',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': 'cosakondrin',
            'sku_smsa_jordan': '8697595872338',
            'sku_naqel': None
        },
        {
            'product_name': 'GREEN LABLE PROPIOTIC',
            'sku_internal': 'GRL',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': None,
            'sku_smsa_jordan': None,
            'sku_naqel': None
        },
        {
            'product_name': 'TRIBULUS',
            'sku_internal': 'TRBS',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': None,
            'sku_smsa_jordan': None,
            'sku_naqel': None
        },
        {
            'product_name': 'BRAZILIAN SLIMMING',
            'sku_internal': 'BRZ',
            'sku_smsa_ksa': None,
            'sku_smsa_uae': 'Brazilan slimming fat capsule',
            'sku_smsa_jordan': None,
            'sku_naqel': None
        }
    ]

    # Add or update SKU data
    for sku_data in skus_data:
        product_id = sku_data['sku_internal']  # Use the internal SKU as the product ID

        sku, created = ProductSKUMapping.objects.update_or_create(
            product_id=product_id,
            defaults={
                'product_name': sku_data['product_name'],
                'sku_internal': sku_data['sku_internal'],
                'sku_smsa_ksa': sku_data['sku_smsa_ksa'],
                'sku_smsa_uae': sku_data['sku_smsa_uae'],
                'sku_smsa_jordan': sku_data['sku_smsa_jordan'],
                'sku_naqel': sku_data['sku_naqel']
            }
        )

        action = "Created" if created else "Updated"
        print(f"{action} SKU: {sku}")

    print(f"Successfully imported {len(skus_data)} SKUs.")

if __name__ == "__main__":
    import_warehouses()
    import_skus()
