from django.contrib import admin
from .models import ErrorLog, Faq, SiteConfiguration
from solo.admin import SingletonModelAdmin
# Register your models here.


admin.site.register(SiteConfiguration, SingletonModelAdmin)

@admin.register(ErrorLog)
class ContractLogAdmin(admin.ModelAdmin):
    
    readonly_fields = ('id', 'time', 'error','data','notes')


admin.site.register(Faq)