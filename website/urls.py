from django.urls import path
from .views import ContactUsView,FaqListView, PlatformStatsView


urlpatterns = [
    path('contact-us/',ContactUsView.as_view()),
    path('faq/',FaqListView.as_view()),
    path('platform-status/',PlatformStatsView.as_view()),
]