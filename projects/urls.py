from django.urls import path
from .views import (
    ProjectCreateView,
    PostUpdateView
)

urlpatterns = [
    path('create/', ProjectCreateView.as_view()),
    path('<int:pk>/post-update', PostUpdateView.as_view()),
]
