# core/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
import django.contrib.admin.sites
from contract.blockchain import vault_bal, platform_wallet_bal
from contract.blockchain import contract, send_owner_tx
User = get_user_model()

class MyAdminSite(AdminSite):
    site_header = "My Custom Admin"
    site_title = "My Admin Portal"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["user_count"] = User.objects.count()
        extra_context["treasury_balance"] = platform_wallet_bal()
        extra_context["vault_balance"] = vault_bal()
        extra_context["total_campaigns"] = contract.functions.campaignCount().call()
        extra_context["platform_wallet"] = contract.functions.platformWallet().call()
        extra_context["owner"] = contract.functions.owner().call()
        extra_context["paused"] = contract.functions.paused().call()
        extra_context["fee_bps"] = contract.functions.feeBps().call()
        
        return super().index(request, extra_context=extra_context)

# ✅ Save the default site before replacing it
default_site = admin.site

# ✅ Create your custom site
my_admin_site = MyAdminSite(name="myadmin")

# ✅ Copy over all registered models
my_admin_site._registry = default_site._registry.copy()

# # ✅ Replace Django’s global admin site
# admin.site = my_admin_site
# django.contrib.admin.sites.site = my_admin_site
