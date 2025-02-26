# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, ShipmentViewSet,
    ShippingCompanyViewSet, ShippingCompanyAccountViewSet
)

# إنشاء router للـ API
router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'shipments', ShipmentViewSet)
router.register(r'shipping-companies', ShippingCompanyViewSet)
router.register(r'shipping-accounts', ShippingCompanyAccountViewSet)

urlpatterns = [
    path('', include(router.urls)),
]