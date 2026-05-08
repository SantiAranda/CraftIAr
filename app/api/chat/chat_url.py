from django.urls import path
from . import ChatApiView

urlpatterns = [
    path('chat/', ChatApiView.as_view(), name='chat_api'),
    path('chat/<int:id>/', ChatApiView.as_view(), name='chat_api_detail'),
]