
from rest_framework.response import Response
from rest_framework import generics, status
from django.db import transaction
from .models import LinkioTransaction
from . import serializers, utils
from rest_framework import permissions
from accounts.models import Wallet
from projects.paginations import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q


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


class GetDepositWalletView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        data, status_code = utils.get_deposit_wallets()
        return Response(data, status=status_code)



class RetailRateView(generics.GenericAPIView):
    serializer_class = serializers.RateQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        trx_type = serializer.validated_data['trx_type']
        data, status_code = utils.get_retail_rates(trx_type)
        return Response(data, status=status_code)





class VerifyAccountNumberView(generics.GenericAPIView):
    serializer_class = serializers.VerifyAccountNumberSerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        account_number = serializer.validated_data['account_number']
        bank_code = serializer.validated_data['bank_code']
        data, status_code = utils.verify_account_number(account_number, bank_code)
        return Response(data, status=status_code)





# --- ONRAMP (User is Buying USDC with NGN) ---
class InitiateOnrampView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OnrampSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        account_number = data.get('account_number')
        bank_name = data.get('bank_name')
        # Call Linkio (utils.py)
        response_data, status_code = utils.initiate_onramp(data)
        
        # Linkio's success code is "TXN_SUCCESSFUL" and status is "Success"
        if status_code == 201 and response_data.get("code") == "TXN_SUCCESSFUL":
            trx_data = response_data.get("transaction", {})

            payload_wallet = data.get("wallet_address")
            print(payload_wallet)
            wallet, created = Wallet.objects.get_or_create(
                address__iexact=payload_wallet,
                defaults={'address': payload_wallet}
            )


            LinkioTransaction.objects.create(
                transaction_id=trx_data.get("transaction_id"),
                reference=trx_data.get("reference"),
                transaction_type=LinkioTransaction.TransactionType.ONRAMP,
                amount=trx_data.get("amount"),
                payout_amount=trx_data.get("payout_amount"),
                rate=trx_data.get("onramp_rate"),
                wallet = wallet,
                # Save the Linkio bank details so user knows where to pay
                link_account_name=trx_data.get("link_account_name"),
                link_account_number=trx_data.get("link_account_number"),
                link_bank_name=trx_data.get("link_bank_name"),
                user_bank_name = bank_name,
                user_account_number = account_number,
            )
            
        return Response(response_data, status=status_code)


# --- OFFRAMP (User is Selling USDC for NGN) ---
class InitiateOfframpView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OfframpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Call Linkio (utils.py)
        response_data, status_code = utils.initiate_offramp(data)
        wallet = data.get('wallet_address')
        # Check for success
        if status_code == 201 and response_data.get("code") == "TXN_SUCCESSFUL":
            trx_data = response_data.get("transaction", {})

            payload_wallet = data.get("wallet_address")
            wallet, created = Wallet.objects.get_or_create(
                address__iexact=payload_wallet,
                defaults={'address': payload_wallet}
            )
            
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
                wallet= wallet,
            )
            
        return Response(response_data, status=status_code)


# --- WEBHOOK (Linkio tells us when it's done) ---
class LinkioWebhookView(generics.GenericAPIView):
    authentication_classes = [] 
    permission_classes = [] 

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # 1. Verify webhook signature (Comment out for local testing without valid signature)
        if not utils.verify_linkio_webhook(request):
            return Response({"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Linkio payload structure
        webhook_body = request.data
        print(webhook_body)
        
        # Extract the inner 'payload' dict based on your provided JSON
        trx_payload = webhook_body.get('payload', {}) 
        
        t_id = trx_payload.get("transaction_id")
        ref = trx_payload.get("reference")
        
        # Get the exact status string from Linkio (Pending, Processing, Completed)
        incoming_status = trx_payload.get("transaction_status", "").upper()

        if not t_id and not ref:
            return Response({"error": "Missing transaction identifiers"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Look up the transaction using EITHER transaction_id OR reference
            # Using Q objects allows us to match whichever one is available safely
            trx = LinkioTransaction.objects.select_for_update().get(
                Q(transaction_id=t_id) | Q(reference=ref)
            )
            
            # 3. Explicitly map Linkio's status to our database status choices
            if incoming_status == "COMPLETED":
                trx.status = LinkioTransaction.Status.SUCCESSFUL
                
            elif incoming_status == "PROCESSING":
                trx.status = LinkioTransaction.Status.PROCESSING
                
            elif incoming_status == "PENDING":
                trx.status = LinkioTransaction.Status.PENDING
                
            # Fallbacks just in case Linkio ever sends a failure event
            elif incoming_status in ["FAILED", "REJECTED", "CANCELLED"]:
                trx.status = LinkioTransaction.Status.FAILED
            
            # Save the full webhook payload into the JSONField for debugging/auditing
            trx.webhook_data = webhook_body
            trx.save()
            
            return Response({"message": "Webhook processed successfully"}, status=status.HTTP_200_OK)
            
        except LinkioTransaction.DoesNotExist:
            # If the webhook reaches us before the initial API creation resolves (rare, but happens),
            # returning 404 is standard. 
            return Response({"error": "Transaction not found in database"}, status=status.HTTP_404_NOT_FOUND)











class FetchTransactionView(generics.GenericAPIView):
    serializer_class = serializers.TransactionQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        trx_ref = serializer.validated_data['trx_ref']
        data, status_code = utils.fetch_transaction(trx_ref)
        return Response(data, status=status_code)

class PayoutStatusView(generics.GenericAPIView):
    serializer_class = serializers.TransactionQuerySerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        trx_ref = serializer.validated_data['trx_ref']
        data, status_code = utils.get_payout_status(trx_ref)
        return Response(data, status=status_code)



class LinkTransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.LinkTransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend,]
    filterset_fields = ['wallet__address', 'transaction_type', 'status']

    def get_queryset(self):
        wallets= self.request.user.wallets.all()

        return LinkioTransaction.objects.filter(wallet__in=wallets).distinct()
