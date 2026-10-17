from django.urls import path
from . import views

urlpatterns = [
    path('banks/', views.SupportedBanksView.as_view(), name='linkio-banks'),
    path('vendors/', views.VendorListView.as_view(), name='linkio-vendors'),
    path('rates/', views.RetailRateView.as_view(), name='linkio-rates'),
    path('onramp/', views.InitiateOnrampView.as_view(), name='linkio-onramp'),
    path('offramp/', views.InitiateOfframpView.as_view(), name='linkio-offramp'),
    path('transaction/', views.FetchTransactionView.as_view(), name='linkio-fetch-trx'),
    path('payout-status/', views.PayoutStatusView.as_view(), name='linkio-payout-status'),
    path('transaction-history/', views.LinkTransactionListView.as_view(), name='linkio-transactions'),
    
    ]