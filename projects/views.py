from django.shortcuts import render
from .serializers import CreateProjectSerializer
from rest_framework import generics, status,exceptions, permissions
from rest_framework.response import Response

from accounts.permissions import Is_Organization, Is_Donor
# Create your views here.

class ProjectCreateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,Is_Organization]

    def post(self, request):
        serializer = CreateProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

