# core/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
import django.contrib.admin.sites
from contract.blockchain import vault_bal, platform_wallet_bal
from contract.blockchain import contract, send_owner_tx
from accounts.models import Donor

class MyAdminSite(AdminSite):
    site_header = "My Custom Admin"
    site_title = "My Admin Portal"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["total_donors"] = Donor.objects.count()

        # Safe blockchain calls
        try:
            extra_context["treasury_balance"] = platform_wallet_bal()
        except Exception:
            extra_context["treasury_balance"] = "alchemy error"

        try:
            extra_context["vault_balance"] = vault_bal()
        except Exception:
            extra_context["vault_balance"] = "alchemy error"

        # Contract function calls
        def safe_call(func, default="alchemy error"):
            try:
                return func()
            except Exception:
                return default

        extra_context["total_campaigns"] = safe_call(lambda: contract.functions.campaignCount().call())
        extra_context["platform_wallet"] = safe_call(lambda: contract.functions.platformWallet().call())
        extra_context["owner"] = safe_call(lambda: contract.functions.owner().call())
        extra_context["paused"] = safe_call(lambda: contract.functions.paused().call())
        extra_context["fee_bps"] = safe_call(lambda: contract.functions.feeBps().call())

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
