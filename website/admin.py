from django.contrib import admin
from website.models import ErrorLog, Faq
# Register your models here.


@admin.register(ErrorLog)
class ContractLogAdmin(admin.ModelAdmin):
    
    readonly_fields = ('id', 'time', 'error','data','notes')


admin.site.register(Faq)