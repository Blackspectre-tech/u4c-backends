from .serializers import ContactUsSerializer,FaqSerializer
from rest_framework import generics,status
from rest_framework.response import Response
from .models import Faq
from projects.models import Donation,Project
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']



User = get_user_model()
class PlatformStatsView(APIView):
    """
    An endpoint that returns basic platform metrics.
    """
    def get(self, request, *args, **kwargs):
        # 1. Grab your dynamic values
        # Call the @classmethod directly on the Donation class with ()
        total_donation = Donation.total() 
        
        total_members = User.objects.count()
        # total_campaigns = Project.objects.filter(deployed=True).count()
        completed_campaigns = Project.objects.filter(status=Project.Completed).count()
        # 2. Build the payload dict
        data = {
            "total_donations": total_donation,
            "total_members": total_members,
            # "total_campaigns": total_campaigns
            "completed_campaigns" : completed_campaigns
        }
        
        # 3. Return response
        return Response(data, status=status.HTTP_200_OK)