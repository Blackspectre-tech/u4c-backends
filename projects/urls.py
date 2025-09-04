from django.urls import path
from .views import (
    ProjectCreateView,
    PostUpdateView,
    listApprovedProjectsView,
    RetrieveProjectsView,
    listOrgProjectsView,
    PostMilestoneImages,
    MilestoneImagesRetrieveUpdateDestroyAPIView,
    MilestoneRetrieveView,
    ExpensesCreateView,
    CommentCreateView,
    CommentRetrieveUpdateDestroyView,
    listCommentsByProjectsView,
    MyProjectListView,
)

urlpatterns = [
    path('create/', ProjectCreateView.as_view()),
    path('', listApprovedProjectsView.as_view()),
    path('my-projects/', MyProjectListView.as_view()),
    path('<int:pk>/', RetrieveProjectsView.as_view()),
    path('organization/<int:pk>/', listOrgProjectsView.as_view()),
    path('<int:pk>/comments/', listCommentsByProjectsView.as_view()),
    path('<int:pk>/comments/add/', CommentCreateView.as_view()),
    path('<int:pk>/post-update/', PostUpdateView.as_view()),
    path('comments/<int:pk>/', CommentRetrieveUpdateDestroyView.as_view()),
    path('milestones/<int:pk>/', MilestoneRetrieveView.as_view()),
    path('milestones/<int:pk>/post-images/', PostMilestoneImages.as_view()),
    path('milestones/<int:pk>/add-expenses/', ExpensesCreateView.as_view()),
    path('milestones/images/<int:pk>/', MilestoneImagesRetrieveUpdateDestroyAPIView.as_view()),
]
