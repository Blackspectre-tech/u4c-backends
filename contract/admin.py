from django.contrib import admin
from .models import ContractLog
# Register your models here.


@admin.register(ContractLog)
class ContractLogAdmin(admin.ModelAdmin):
    
    readonly_fields = ('id', 'time', 'error','data','notes')