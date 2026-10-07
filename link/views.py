from rest_framework import generics
from rest_framework.response import Response
from . import serializers
from . import utils

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

class InitiateOnrampView(generics.GenericAPIView):
    serializer_class = serializers.OnrampSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data, status_code = utils.initiate_onramp(serializer.validated_data)
        return Response(data, status=status_code)

class InitiateOfframpView(generics.GenericAPIView):
    serializer_class = serializers.OfframpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data, status_code = utils.initiate_offramp(serializer.validated_data)
        return Response(data, status=status_code)

class TransactionStatusView(generics.GenericAPIView):
    serializer_class = serializers.TransactionStatusSerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        trx_ref = serializer.validated_data['trx_ref']
        data, status_code = utils.get_transaction_status(trx_ref)
        return Response(data, status=status_code)