from django.urls import path
from .views import ContactUsView,FaqListView


urlpatterns = [
    path('contact-us/',ContactUsView.as_view()),
    path('faq/',FaqListView.as_view()),
]