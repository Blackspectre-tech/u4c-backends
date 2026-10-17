# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Wallet

User = get_user_model()

class LinkioTransaction(models.Model):
    class TransactionType(models.TextChoices):
        ONRAMP = 'ONRAMP', 'Onramp (Buy)'
        OFFRAMP = 'OFFRAMP', 'Offramp (Sell)'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'

    # Linkio returns both. It's best to save both.
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    
    # Store exact strings like "15000 NGN" and "10.89 USDC"
    amount = models.CharField(max_length=50)
    payout_amount = models.CharField(max_length=50, null=True, blank=True)
    
    # Store the exchange rate used
    rate = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    
    # The user's destination (Wallet for Onramp, Bank for Offramp)
    wallet = models.ForeignKey(Wallet,related_name='link_transactions', blank=True,null=True, on_delete=models.CASCADE)
    user_bank_name = models.CharField(max_length=100, null=True, blank=True)
    user_account_number = models.CharField(max_length=50, null=True, blank=True)
    
    # LINKIO'S Bank Details (Crucial for Onramp: User needs to transfer money here)
    link_account_name = models.CharField(max_length=255, null=True, blank=True)
    link_account_number = models.CharField(max_length=50, null=True, blank=True)
    link_bank_name = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    webhook_data = models.JSONField(null=True, blank=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type} | {self.reference} | {self.status}"