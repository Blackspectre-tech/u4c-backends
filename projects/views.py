from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework import generics, status,exceptions, permissions, parsers
from rest_framework.response import Response
from drf_nested_multipart.parser import NestedMultipartAndFileParser

from accounts.permissions import Is_Org, Is_Donor,isOrgObjOwner,isDonorObjOwner
from .models import Project, Update,Expense,Milestone,Organization,Comment, MilestoneImage
from .paginations import StandardResultsSetPagination
from .serializers import (
    ProjectSerializer,
    PostUpdateSerializer,
    MiliestoneImagesSerializer,
    MilestoneSerializer,
    ExpensesSerializer,
    CommentSerializer,
    ProjectListSerializer,
    )

# Create your views here.

class ProjectCreateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,Is_Org,]
    parser_classes=[NestedMultipartAndFileParser]
    serializer_class = ProjectSerializer

    def post(self, request):
        org = request.user.organization
        if org.approval_status != Organization.APPROVED:
            raise ValidationError({'Organization':'Organization is not approved to post projects'})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(organization=org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class listApprovedProjectsView(generics.ListAPIView):
    queryset = Project.objects.filter(approval_status=Project.APPROVED)
    serializer_class = ProjectListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categories__name','status']
    search_fields = ['title']
    pagination_class = StandardResultsSetPagination



class listOrgProjectsView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        org = get_object_or_404(Organization,self.kwargs['pk'])
        org_projects = Project.objects.filter(organization=org)
        return org_projects



class RetrieveProjectsView(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'pk'




class PostUpdateView(generics.CreateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        Is_Org,
        isOrgObjOwner
        ]
    parser_classes=[NestedMultipartAndFileParser]
    serializer_class = PostUpdateSerializer
    def perform_create(self, serializer):
        pk = self.kwargs['pk']
        project = get_object_or_404(Project, pk=pk)
        self.check_object_permissions(self.request, project)
        serializer.save(project=project)


class PostMilestoneImages(generics.GenericAPIView):
    parser_classes=[parsers.MultiPartParser]
    permission_classes = [
        permissions.IsAuthenticated,
        Is_Org]
    serializer_class = MiliestoneImagesSerializer
    
    def post(self, request, **kwargs):
        print (request.data)
        milestone = get_object_or_404(Milestone, pk=kwargs['pk'])
        if milestone.project.organization != request.user.organization:
            raise ValidationError ({'message':'only project creators can update images'})
        serializer = self.get_serializer(data = request.data, context={'milestone':milestone})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'images uploaded successfully'},status=status.HTTP_201_CREATED)

        
class MilestoneRetrieveView(generics.RetrieveAPIView):
    queryset = Milestone.objects.all()
    serializer_class =MilestoneSerializer
    lookup_field = 'pk'


class ExpensesCreateView(generics.CreateAPIView):
    parser_classes=[NestedMultipartAndFileParser]
    permission_classes = [permissions.IsAuthenticated,Is_Org,isOrgObjOwner]
    serializer_class = ExpensesSerializer
    
    def perform_create(self, serializer):
        milestone = get_object_or_404(Milestone, id=self.kwargs['pk'])
        org = milestone.project 
        self.check_object_permissions(self.request, org)
        serializer.save(milestone=milestone) 



class CommentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, Is_Donor]
    serializer_class = CommentSerializer
    def perform_create(self, serializer):
        profile=self.request.user.profile
        project = get_object_or_404(Project,pk=self.kwargs['pk'])
        serializer.save(profile=profile, project=project)



class listCommentsByProjectsView(generics.ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        project = get_object_or_404(Project,pk=self.kwargs['pk'])
        comments = Comment.objects.filter(Project=project)
        return comments




class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        Is_Donor,isDonorObjOwner]
    lookup_field = 'pk'




class MilestoneImagesRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MilestoneImage.objects.all()
    serializer_class = MiliestoneImagesSerializer
    permission_classes = [permissions.IsAuthenticated,Is_Org]
    parser_classes = [parsers.MultiPartParser]
    def perform_destroy(self, instance):
        if instance.milestone.project.organization != self.request.user.organization:
            raise ValidationError({'message':'you are not permited to delete this item'})
        return super().perform_destroy(instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.milestone.project.organization != self.request.user.organization:
            raise ValidationError({'message':'you are not permited to delete this item'})
        
        return super().perform_update(serializer)
