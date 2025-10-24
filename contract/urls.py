from django.urls import path
from . import views
from .webhook import alchemy_webhook
app_name = 'contract'

urlpatterns = [
    path('webhook/', alchemy_webhook),
    path('set-platform-wallet/', views.set_platform_wallet, name='set_platform_wallet'),
    path('set-allowed-token/', views.set_allowed_token, name='set_allowed_token'),
    path('transfer-ownership/', views.transfer_ownership, name='transfer_ownership'),
    path('pause/', views.pause, name='pause'),
    path('unpause/', views.unpause, name='unpause'),
    path('set-fee-bps/', views.set_fee_bps, name='set_fee_bps'),
]
