from django.urls import path

from . import chatbot_view

urlpatterns = [
    # GET /api/chat/ - Listar sesiones
    # POST /api/chat/ - Crear un nuevo chat
    path("chat/", chatbot_view.ChatSessionListCreateView.as_view(), name="chat-session-list-create"),

    # GET /api/chat/<uuid>/ - Para ver historial
    # DELETE /api/chat/<uuid>/ - Borrar sesion
    path("chat/<uuid:pk>/", chatbot_view.ChatSessionDetailView.as_view(), name="chat-session-detail"),

    # POST /api/chat/<uuid>/message/ - Para enviar un mensaje y recibir respuesta
    path("chat/<uuid:pk>/stream/", chatbot_view.ChatMessageStreamView.as_view(), name="chat-message-stream"),
]
