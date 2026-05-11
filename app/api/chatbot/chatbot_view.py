from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.renderers import BaseRenderer
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


class ChatSessionListCreateView(generics.ListCreateAPIView):
    queryset = ChatbotSession.objects.all()
    serializer_class = ChatbotSessionSerializer
    permission_classes = [AllowAny]


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    queryset = ChatbotSession.objects.all()
    serializer_class = ChatbotSessionSerializer
    permission_classes = [AllowAny]


class ChatMessageStreamView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rag_service = RAGQueryService()

    permission_classes = [AllowAny]

    class ServerSentEventsRenderer(BaseRenderer):
        media_type = "text/event-stream"
        format = "sse"
        charset = "utf-8"

        def render(self, data, media_type=None, renderer_context=None):
            return data

    renderer_classes = [ServerSentEventsRenderer]

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
