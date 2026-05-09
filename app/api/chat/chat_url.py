from django.urls import path

from .chat_view import ChatApiView

urlpatterns = [
    path("chat", ChatApiView.as_view(), name="chat_api"),
    path("chat/<int:chat_id>", ChatApiView.as_view(), name="chat_api_detail"),
]
