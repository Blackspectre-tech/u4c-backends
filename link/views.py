# from django.shortcuts import render
# from utils import get_retail_rates
# from rest_framework import generics, status, permissions
# from rest_framework.response import Response
# from .serializers import RetailRatesserializer

# # Create your views here.



# class RetailRatesView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = RetailRatesserializer

#     def post(self, request):
#         # trx_type = request.data.get('trx_type')
#         # if not trx_type:
#         #     return Response( {"error": "trx_type is rerquired"}, status=status.HTTP_400_BAD_REQUEST )
            
