from .serializers import ContactUsSerializer,FaqSerializer
from rest_framework import generics,status
from rest_framework.response import Response
from .models import Faq
# Create your views here.

class ContactUsView(generics.GenericAPIView):
    serializer_class = ContactUsSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "mail sent successfully"},
            status= status.HTTP_200_OK)

class FaqListView(generics.ListAPIView):
    serializer_class = FaqSerializer
    queryset = Faq.objects.all()

