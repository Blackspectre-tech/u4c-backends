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