from django.urls import path
from .views import HomeApiView

urlpatterns = [
    path('home/', HomeApiView.as_view(), name='home'),
    path('home/<int:id>/', HomeApiView.as_view(), name='home-detail-update-delete'),
]