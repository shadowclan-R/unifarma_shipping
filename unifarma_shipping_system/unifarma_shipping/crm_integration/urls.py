# crm_integration/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhook/citrix/', views.citrix_webhook, name='citrix_webhook'),
]