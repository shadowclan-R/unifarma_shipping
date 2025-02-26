# api/serializers.py
from rest_framework import serializers
from orders.models import Order, OrderItem, Shipment
from shippers.models import ShippingCompany, ShippingCompanyAccount

class ShippingCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingCompany
        fields = ['id', 'name', 'code', 'is_active', 'logo', 'website', 'description']

class ShippingCompanyAccountSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField(source='company.name')

    class Meta:
        model = ShippingCompanyAccount
        fields = ['id', 'company', 'company_name', 'title', 'account_type',
                 'is_active', 'specific_countries', 'customer_id', 'warehouse_id']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'passkey': {'write_only': True},
        }

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'sku', 'quantity',
                 'unit_price', 'total_price', 'weight', 'lot_number',
                 'serial_number', 'expiry_date']

class ShipmentSerializer(serializers.ModelSerializer):
    shipping_company_name = serializers.ReadOnlyField(source='shipping_company.name')
    shipping_account_title = serializers.ReadOnlyField(source='shipping_account.title')

    class Meta:
        model = Shipment
        fields = ['id', 'order', 'shipping_company', 'shipping_company_name',
                 'shipping_account', 'shipping_account_title', 'tracking_number',
                 'status', 'created_at', 'updated_at', 'submitted_at',
                 'delivered_at', 'events_log', 'error_message', 'notes']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipments = ShipmentSerializer(many=True, read_only=True)
    shipping_company_name = serializers.ReadOnlyField(source='shipping_company.name')
    shipping_account_title = serializers.ReadOnlyField(source='shipping_account.title')

    class Meta:
        model = Order
        fields = ['id', 'citrix_deal_id', 'reference_number', 'status',
                 'customer_name', 'customer_phone', 'customer_email',
                 'shipping_country', 'shipping_city', 'shipping_address',
                 'shipping_postal_code', 'total_amount', 'cod_amount', 'is_cod',
                 'shipping_company', 'shipping_company_name', 'shipping_account',
                 'shipping_account_title', 'citrix_created_at', 'created_at',
                 'updated_at', 'shipped_at', 'notes', 'items', 'shipments']