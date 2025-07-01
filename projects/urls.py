from django.urls import path
from .views import (
    ProjectCreateView
)

urlpatterns = [
    path('create/', ProjectCreateView.as_view()),
]
