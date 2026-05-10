from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist

from . import (
    # ChatbotMessage,
    # ChatbotMessageSerializer,
    ChatbotSession,
    ChatbotSessionSerializer,
    RAGQueryService,
)


class ChatSessionCreateView(generics.CreateAPIView):
    queryset = ChatbotSession.objects.all()
    serializer_class = ChatbotSessionSerializer
    permission_classes = [AllowAny]


class ChatSessionDetailView(generics.RetrieveAPIView):
    queryset = ChatbotSession.objects.all()
    serializer_class = ChatbotSessionSerializer
    permission_classes = [AllowAny]


class ChatMessageStreamView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rag_service = RAGQueryService()

    permission_classes = [AllowAny]

    def post(self, request, pk):
        user_text = request.data.get("message")

        if not user_text:
            return Response(
                {"error": "Message content is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stream = self.rag_service.query(session_id=pk, user_text=user_text)

            response = StreamingHttpResponse(stream, content_type="text/event-stream")

            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'  # Deshabilitar el buffering en Nginx

            return response
        except ObjectDoesNotExist:
            return Response(
                {"error": "Chat session not found."}, status=status.HTTP_404_NOT_FOUND
            )
