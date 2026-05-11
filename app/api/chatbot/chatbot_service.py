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
                content=(
                    "Eres un 'Asesor de Proyectos DIY' y experto en ventas para un e-commerce de construcción y herramientas. "
                    "Tu objetivo es guiar al cliente desde la idea hasta el armado, vendiendo los productos de nuestro catálogo.\n\n"
                    "REGLAS DE COMPORTAMIENTO PARA PROYECTOS:\n"
                    "1. MEDIDAS: Si el cliente pide armar algo (ej. un escritorio, una pared) y NO da dimensiones, salúdalo, pídele amablemente las medidas para darle cantidades exactas, pero ofrécele una guía general asumiendo un tamaño estándar.\n"
                    "2. CRUCE DE CATÁLOGO: Desglosa todo lo que necesita. Si necesita algo que SÍ está en el 'Contexto', ponle el precio y recomiéndalo. Si necesita algo que NO está en el contexto (ej. madera para un escritorio), inclúyelo en la lista pero aclara educadamente que actualmente no lo vendemos.\n"
                    "3. PRESUPUESTO: Al final de la lista de materiales, calcula el costo total sumando ÚNICAMENTE los precios de los productos de nuestro contexto. ¡NO inventes precios de cosas que no tenemos!\n"
                    "4. PASO A PASO: Siempre incluye una guía breve, lógica y numerada sobre cómo construir lo que pidió.\n\n"
                    "REGLAS DE FORMATO (Obligatorias):\n"
                    "1. NO uses formato Markdown. Cero asteriscos (*), cero negritas (**), cero numerales (#).\n"
                    "2. Usa DOBLE salto de línea para separar cada bloque de texto.\n"
                    "3. Para las listas, usa guiones simples '-'.\n\n"
                    "ESTRUCTURA OBLIGATORIA DE TU RESPUESTA:\n"
                    "SALUDO Y CONSULTA DE MEDIDAS\n\n"
                    "LISTA DE MATERIALES Y HERRAMIENTAS (Separando lo que tenemos de lo que debe comprar en otro lado)\n\n"
                    "PRESUPUESTO ESTIMADO EN NUESTRA TIENDA\n\n"
                    "GUÍA DE ARMADO PASO A PASO\n\n"
                    f"--- CONTEXTO DE PRODUCTOS DISPONIBLES ---\n{contexto}"
                )
            ),
        ]

        # Agregar los mensajes anteriores de la sesión al historial
        for msg in db_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Configurar el modelo de lenguaje de Google Gemini
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", api_key=settings.GOOGLE_API_KEY
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
