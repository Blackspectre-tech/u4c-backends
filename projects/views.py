from django.shortcuts import render
from .serializers import (
    ProjectSerializer,
    UpdateSerializer,
    )
from rest_framework import generics, status,exceptions, permissions, parsers
from rest_framework.response import Response
from drf_nested_multipart.parser import NestedMultipartAndFileParser
from accounts.permissions import Is_Organization, Is_Donor
from .models import Project
from rest_framework.views import APIView
import pprint
# Create your views here.

class ProjectCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated,Is_Organization]
    parser_classes=[NestedMultipartAndFileParser]

    def post(self, request):
        organization = request.user.organization
        serializer = ProjectSerializer(data=request.data, context={'request': request}) 
        serializer.is_valid(raise_exception=True)
        serializer.save(organization=organization)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostUpdateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,Is_Organization]
    parser_classes=[parsers.MultiPartParser]
    serializer_class = UpdateSerializer
    def perform_create(self, serializer):
        pk = self.kwargs['pk']
        project=Project.ojects.get(pk=pk)
        serializer.save(project=project)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

        


