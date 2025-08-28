# core/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
import django.contrib.admin.sites
from transactions.blockchain import vault_bal, platform_wallet_bal

User = get_user_model()

class MyAdminSite(AdminSite):
    site_header = "My Custom Admin"
    site_title = "My Admin Portal"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["user_count"] = User.objects.count()
        extra_context["treasury_balance"] = 0 #platform_wallet_bal()
        extra_context["vault_balance"] = 0#vault_bal()
        extra_context["total_campaigns"] = 0
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
