from urllib.parse import quote_plus

from django.conf import settings
from django.db.models.fields.composite import json
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

from . import ChatbotMessage, ChatbotSession


class RAGQueryService:
    def query(self, session_id: str, user_text: str):
        # Recuperar la session y guardar el mensaje del usuario en la base de datos
        session = ChatbotSession.objects.get(id=session_id)
        ChatbotMessage.objects.create(session=session, role="user", content=user_text)

        # Configurar la conexión a la base de datos para PGVector
        password = quote_plus(settings.DATABASES["rag"]["PASSWORD"])
        VECTOR_DB_URL = f"postgresql://{settings.DATABASES['rag']['USER']}:{password}@{settings.DATABASES['rag']['HOST']}:{settings.DATABASES['rag']['PORT']}/{settings.DATABASES['rag']['NAME']}"

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2", api_key=settings.GOOGLE_API_KEY
        )
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="product_embeddings",
            connection=VECTOR_DB_URL,
            use_jsonb=True,
        )

        # Realizar la búsqueda vectorial de similitud en PGVector
        retriever = vector_store.similarity_search(user_text, k=5)
        contexto = "\n\n".join([doc.page_content for doc in retriever])

        # Construir el historial de mensajes para el modelo de lenguaje
        db_messages = session.messages.order_by("created_at").values("role", "content")
        messages: list[BaseMessage] = [
            SystemMessage(
                content=f"Eres un asistente de ventas para un ecommerce de materiales de construccion. Usa este contexto de productos para responder:\n{contexto}\nSi la info no está en el contexto, dilo amablemente."
            ),
        ]

        # Agregar los mensajes anteriores de la sesión al historial
        for msg in db_messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        # Configurar el modelo de lenguaje de Google Gemini
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", api_key=settings.GOOGLE_API_KEY
        )

        # Generar la respuesta del asistente utilizando el modelo de lenguaje
        completed_response = ""
        for chunk in llm.stream(messages):
            content_piece = chunk.content

            # Acumular la respuesta completa a medida que se reciben los fragmentos
            if isinstance(content_piece, str):
                completed_response += content_piece

            payload = json.dumps({"response": chunk.content})
            yield f"data: {payload}\n\n"

        # Guardar la respuesta del asistente en la base de datos
        ChatbotMessage.objects.create(
            session=session, role="assistant", content=completed_response
        )

        yield "data: [DONE]\n\n"
