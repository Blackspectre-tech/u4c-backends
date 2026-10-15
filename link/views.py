
from rest_framework.response import Response
from rest_framework import generics, status
from django.db import transaction
from .models import LinkioTransaction
from . import serializers, utils


class SupportedBanksView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        currency = request.query_params.get('currency', 'NGN')
        data, status_code = utils.get_supported_banks(currency)
        return Response(data, status=status_code)

class VendorListView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        currency = request.query_params.get('currency', 'NGN')
        data, status_code = utils.get_vendors_list(currency)
        return Response(data, status=status_code)

class RetailRateView(generics.GenericAPIView):
    serializer_class = serializers.RateQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        trx_type = serializer.validated_data['trx_type']
        data, status_code = utils.get_retail_rates(trx_type)
        return Response(data, status=status_code)

# class InitiateOnrampView(generics.GenericAPIView):
#     serializer_class = serializers.OnrampSerializer

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         data, status_code = utils.initiate_onramp(serializer.validated_data)
#         return Response(data, status=status_code)

# class InitiateOfframpView(generics.GenericAPIView):
#     serializer_class = serializers.OfframpSerializer

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         data, status_code = utils.initiate_offramp(serializer.validated_data)
#         return Response(data, status=status_code)










# --- ONRAMP (User is Buying USDC with NGN) ---
class InitiateOnrampView(generics.GenericAPIView):
    serializer_class = serializers.OnrampSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call Linkio (utils.py)
        response_data, status_code = utils.initiate_onramp(serializer.validated_data)
        
        # Linkio's success code is "TXN_SUCCESSFUL" and status is "Success"
        if status_code == 200 and response_data.get("code") == "TXN_SUCCESSFUL":
            trx_data = response_data.get("transaction", {})
            
            LinkioTransaction.objects.create(
                transaction_id=trx_data.get("transaction_id"),
                reference=trx_data.get("reference"),
                transaction_type=LinkioTransaction.TransactionType.ONRAMP,
                amount=trx_data.get("amount"),
                payout_amount=trx_data.get("payout_amount"),
                rate=trx_data.get("onramp_rate"),
                wallet_address=trx_data.get("wallet_address"),
                
                # Save the Linkio bank details so user knows where to pay
                link_account_name=trx_data.get("link_account_name"),
                link_account_number=trx_data.get("link_account_number"),
                link_bank_name=trx_data.get("link_bank_name"),
            )
            
        return Response(response_data, status=status_code)


# --- OFFRAMP (User is Selling USDC for NGN) ---
class InitiateOfframpView(generics.GenericAPIView):
    serializer_class = serializers.OfframpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call Linkio (utils.py)
        response_data, status_code = utils.initiate_offramp(serializer.validated_data)
        
        # Check for success
        if status_code == 200 and response_data.get("code") == "TXN_SUCCESSFUL":
            trx_data = response_data.get("transaction", {})
            
            LinkioTransaction.objects.create(
                transaction_id=trx_data.get("transaction_id"),
                reference=trx_data.get("reference"),
                transaction_type=LinkioTransaction.TransactionType.OFFRAMP,
                amount=trx_data.get("amount"),
                payout_amount=trx_data.get("payout_amount"),
                rate=trx_data.get("offramp_rate"),
                
                # Save user's receiving bank details
                user_account_number=trx_data.get("account_number"),
                user_bank_name=trx_data.get("bank_name"),
            )
            
        return Response(response_data, status=status_code)

# --- WEBHOOK (Linkio tells us when it's done) ---
class LinkioWebhookView(generics.GenericAPIView):
    authentication_classes = [] 
    permission_classes = [] 

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # 1. Verify webhook signature (from utils.py)
        if not utils.verify_linkio_webhook(request):
            return Response({"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)
        
        payload = request.data
        
        # Based on typical Linkio webhook payloads, data is inside a 'data' key
        trx_data = payload.get('data', payload) 
        
        # Linkio might send webhook updates using either reference or transaction_id
        t_id = trx_data.get("transaction_id")
        ref = trx_data.get("reference")
        
        # Their response uses "transaction_status", so webhook likely does too
        new_status = trx_data.get("transaction_status", "").upper() 

        if not t_id and not ref:
            return Response({"error": "Missing identifiers"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Look up the transaction using EITHER reference or transaction_id
            if t_id:
                trx = LinkioTransaction.objects.select_for_update().get(transaction_id=t_id)
            else:
                trx = LinkioTransaction.objects.select_for_update().get(reference=ref)
            
            # 3. Map Linkio's status to our database status
            # Linkio often uses "Success", "Failed", "Pending", "Processing"
            if new_status in ["SUCCESS", "SUCCESSFUL"]:
                trx.status = LinkioTransaction.Status.SUCCESSFUL
            elif new_status in ["FAILED", "REJECTED", "CANCELLED"]:
                trx.status = LinkioTransaction.Status.FAILED
            elif new_status in ["PENDING", "PROCESSING"]:
                trx.status = LinkioTransaction.Status.PENDING
            
            # Save the full webhook payload for future auditing
            trx.webhook_data = payload 
            trx.save()
            
            return Response({"message": "Webhook processed"}, status=status.HTTP_200_OK)
            
        except LinkioTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)













class FetchTransactionView(generics.GenericAPIView):
    serializer_class = serializers.TransactionQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        trx_ref = serializer.validated_data['trx_ref']
        data, status_code = utils.fetch_transaction(trx_ref)
        return Response(data, status=status_code)

class PayoutStatusView(generics.GenericAPIView):
    serializer_class = serializers.TransactionQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        trx_ref = serializer.validated_data['trx_ref']
        data, status_code = utils.get_payout_status(trx_ref)
        return Response(data, status=status_code)
    