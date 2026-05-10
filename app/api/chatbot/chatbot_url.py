from django.urls import path

from . import ChatbotAPIView

urlpatterns = [
    path("chatbot", ChatbotAPIView.as_view(), name="chatbot"),
]