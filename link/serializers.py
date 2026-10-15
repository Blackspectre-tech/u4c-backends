from rest_framework import serializers

class RateQuerySerializer(serializers.Serializer):
    trx_type = serializers.ChoiceField(choices=[('onramp', 'Onramp'), ('offramp', 'Offramp')])

class OnrampSerializer(serializers.Serializer):
    currency = serializers.CharField(default="NGN", max_length=10)
    amount = serializers.CharField()
    vendor_bank = serializers.CharField()
    vendor_number = serializers.CharField()
    vendor_name = serializers.CharField()
    wallet_address = serializers.CharField()
    bank_name = serializers.CharField()
    account_number = serializers.CharField()
    network = serializers.CharField(default="polygon")
    stables = serializers.CharField(default="USDC")

class OfframpSerializer(serializers.Serializer):
    currency = serializers.CharField(default="NGN", max_length=10)
    amount = serializers.CharField()
    wallet_address = serializers.CharField()
    bank_name = serializers.CharField()
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    network = serializers.CharField(default="polygon")
    stables = serializers.CharField(default="USDC")

class TransactionQuerySerializer(serializers.Serializer):
    trx_ref = serializers.CharField(
        help_text="The transaction reference or ID returned by Linkio upon initiation"
    )



# class LinkioWebhookSerializer(serializers.Serializer):
#     # The exact field names depend on Linkio's webhook payload structure.
#     # Adjust 'trx_ref' and 'status' if Linkio names them 'id' or 'transaction_status'
#     trx_ref = serializers.CharField(required=True)
#     status = serializers.CharField(required=True)
#     event_type = serializers.CharField(required=False)
    
#     # Using DRF's write-only properties to handle the DB update cleanly inside the serializer
#     def process_webhook(self, validated_data):
#         from .models import LinkioTransaction
        
#         trx_ref = validated_data.get('trx_ref')
#         status = validated_data.get('status').lower()
        
#         try:
#             transaction = LinkioTransaction.objects.get(trx_ref=trx_ref)
            
#             # Map Linkio's various success/failure statuses to your DB choices
#             if status in ['successful', 'completed', 'success']:
#                 transaction.status = 'successful'
#                 # TODO: Trigger logic here (e.g., credit user wallet, release tokens)
                
#             elif status in ['failed', 'cancelled', 'declined']:
#                 transaction.status = 'failed'
                
#             transaction.save()
#             return transaction
            
#         except LinkioTransaction.DoesNotExist:
#             return None