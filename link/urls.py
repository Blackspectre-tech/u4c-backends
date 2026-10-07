from django.urls import path
from . import views

urlpatterns = [
    path('banks/', views.SupportedBanksView.as_view(), name='linkio-banks'),
    path('vendors/', views.VendorListView.as_view(), name='linkio-vendors'),
    path('rates/', views.RetailRateView.as_view(), name='linkio-rates'),
    path('onramp/', views.InitiateOnrampView.as_view(), name='linkio-onramp'),
    path('offramp/', views.InitiateOfframpView.as_view(), name='linkio-offramp'),
    path('status/', views.TransactionStatusView.as_view(), name='linkio-status'),
]