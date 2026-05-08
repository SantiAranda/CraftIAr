from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class ChatApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "GET request received"}, status=status.HTTP_200_OK)

    def post(self, request):
        return Response({"message": "POST request received"}, status=status.HTTP_201_CREATED)