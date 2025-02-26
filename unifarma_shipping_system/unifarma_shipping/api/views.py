# api/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from orders.models import Order, Shipment
from shippers.models import ShippingCompany, ShippingCompanyAccount
from orders.services import ShipmentService
from .serializers import (
    OrderSerializer, ShipmentSerializer,
    ShippingCompanySerializer, ShippingCompanyAccountSerializer
)

class ShippingCompanyViewSet(viewsets.ModelViewSet):
    """API للتعامل مع شركات الشحن"""
    queryset = ShippingCompany.objects.all()
    serializer_class = ShippingCompanySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']

class ShippingCompanyAccountViewSet(viewsets.ModelViewSet):
    """API للتعامل مع حسابات شركات الشحن"""
    queryset = ShippingCompanyAccount.objects.all()
    serializer_class = ShippingCompanyAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'is_active', 'account_type']
    search_fields = ['title', 'customer_id']
    ordering_fields = ['company__name', 'title', 'created_at']

class OrderViewSet(viewsets.ModelViewSet):
    """API للتعامل مع الطلبات"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'shipping_country', 'shipping_company', 'shipping_account']
    search_fields = ['reference_number', 'citrix_deal_id', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'updated_at', 'citrix_created_at']

    @action(detail=True, methods=['post'])
    def create_shipment(self, request, pk=None):
        """إنشاء شحنة جديدة للطلب"""
        order = self.get_object()

        # التحقق من وجود شركة شحن محددة
        if not order.shipping_company or not order.shipping_account:
            return Response({
                'success': False,
                'error': 'لا توجد شركة شحن محددة للطلب'
            }, status=400)

        # إنشاء الشحنة
        service = ShipmentService()
        shipment = service.create_shipment_for_order(order)

        if not shipment:
            return Response({
                'success': False,
                'error': 'فشل في إنشاء الشحنة'
            }, status=500)

        if shipment.status == 'error':
            return Response({
                'success': False,
                'error': shipment.error_message
            }, status=400)

        # إرجاع بيانات الشحنة
        serializer = ShipmentSerializer(shipment)
        return Response({
            'success': True,
            'shipment': serializer.data
        })

class ShipmentViewSet(viewsets.ModelViewSet):
    """API للتعامل مع الشحنات"""
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'shipping_company', 'shipping_account']
    search_fields = ['tracking_number', 'order__reference_number']
    ordering_fields = ['created_at', 'updated_at', 'submitted_at']

    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        """تحديث معلومات تتبع الشحنة"""
        shipment = self.get_object()

        # التحقق من وجود رقم تتبع
        if not shipment.tracking_number:
            return Response({
                'success': False,
                'error': 'لا يوجد رقم تتبع للشحنة'
            }, status=400)

        # تحديث معلومات التتبع
        service = ShipmentService()
        updated = service.update_shipment_tracking(shipment)

        if not updated:
            return Response({
                'success': False,
                'error': 'فشل في تحديث معلومات التتبع'
            }, status=500)

        # إرجاع بيانات الشحنة المحدثة
        serializer = ShipmentSerializer(shipment)
        return Response({
            'success': True,
            'shipment': serializer.data
        })