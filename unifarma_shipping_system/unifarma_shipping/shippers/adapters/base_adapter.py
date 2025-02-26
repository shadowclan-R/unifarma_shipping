# shippers/adapters/base_adapter.py
from abc import ABC, abstractmethod

class ShippingAdapter(ABC):
    """الواجهة الأساسية لمحولات شركات الشحن"""

    @abstractmethod
    def create_shipment(self, shipment):
        """
        إنشاء شحنة جديدة مع شركة الشحن

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة العملية (success, tracking_number, response_data, error)
        """
        pass

    @abstractmethod
    def track_shipment(self, shipment):
        """
        تتبع حالة الشحنة

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة التتبع (success, status, details, error)
        """
        pass

    @abstractmethod
    def cancel_shipment(self, shipment):
        """
        إلغاء شحنة

        المعلمات:
            shipment (Shipment): كائن الشحنة

        العائد:
            dict: نتيجة الإلغاء (success, response_data, error)
        """
        pass