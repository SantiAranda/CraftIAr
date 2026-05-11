from urllib.parse import quote_plus

from django.conf import settings
from django.db.models.fields.composite import json
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
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
        internet_context = ""
        if not retriever or not contexto.strip():
            internet_context = self._search_internet(user_text)

        # Construir el historial de mensajes para el modelo de lenguaje
        db_messages = session.messages.order_by("created_at").values("role", "content")
        messages: list[BaseMessage] = [
            SystemMessage(
                content=(
                    "Eres un Asesor Experto para un e-commerce de construcción y herramientas. "
                    "Tu objetivo es ayudar al cliente de forma amable, profesional y directa.\n\n"
                    "REGLA DE ORO: CLASIFICACIÓN DEL MENSAJE\n"
                    "Antes de responder, analiza qué está pidiendo el usuario y aplica SOLO las reglas del caso correspondiente:\n\n"
                    "--- CASO A: CONSULTA SIMPLE (Stock, Precios, Dudas puntuales) ---\n"
                    "Si el usuario pregunta si hay un producto, su precio, o características generales:\n"
                    "- Acción: Responde de manera natural, directa y concisa.\n"
                    "- Formato: Un saludo breve, la respuesta basada en el catálogo y una pregunta de cierre (ej. '¿Te ayudo con algo más?'). NO generes presupuestos ni guías de armado.\n\n"
                    "--- CASO B: CONSULTA EN DOMINIO SIN STOCK (Construcción/Herramientas pero no en catálogo) ---\n"
                    "Si la pregunta SI es sobre construcción, ferretería o herramientas, pero NO aparece en el catálogo:\n"
                    "- Acción: Responde con información general útil (definición, uso común, nombres alternativos), SIN inventar precios ni afirmar stock.\n"
                    "- Formato: Un saludo breve, la explicación general y una pregunta de cierre. Si corresponde, indica que no está en el catálogo o no hay stock.\n\n"
                    "--- CASO C: PROYECTOS DIY (Ej: 'Cómo construir un escritorio', 'Quiero hacer una pared') ---\n"
                    "Si el usuario pide ayuda para fabricar, armar o construir algo:\n"
                    "- Acción: Asume el rol de 'Asesor de Proyectos'.\n"
                    "- Estructura Obligatoria para este caso:\n"
                    "  1. SALUDO: Saluda y pide medidas si no las dio.\n"
                    "  2. MATERIALES: Lista separando lo que SÍ vendemos (con precio) de lo que NO vendemos. Usa guiones simples '-'.\n"
                    "  3. PRESUPUESTO: Suma total de los productos que sí tenemos.\n"
                    "  4. GUÍA: Paso a paso lógico del armado.\n\n"
                    "--- CASO D: FUERA DE CONTEXTO (Ej: Recetas de cocina, política, programación) ---\n"
                    "Si la pregunta no tiene relación con construcción, ferretería o proyectos de hogar:\n"
                    "- Acción: Negación educada.\n"
                    "- Formato: 'Soy un asistente especializado en materiales de construcción y herramientas. No puedo ayudarte con [tema del usuario], pero si necesitas materiales para tu hogar o taller, estoy aquí para ayudarte.'\n\n"
                    "REGLAS DE FORMATO GENERALES (Para todos los casos):\n"
                    "1. NO uses Markdown. Están prohibidos los asteriscos (*), negritas (**), cursivas o numerales (#).\n"
                    "2. Usa DOBLE salto de línea para separar los párrafos.\n"
                    "3. Cuando uses el catálogo, respeta el contexto de productos. NO inventes productos ni precios.\n"
                    "4. Si la consulta es del dominio pero no está en el catálogo, puedes responder con conocimiento general sin precios.\n"
                    "5. Si hay contexto de internet, úsalo SOLO cuando el catálogo esté vacío y la consulta sea simple sobre un producto. Aclara que el stock no está confirmado.\n"
                    "6. Si usas internet, NO digas que buscaste en internet; solo responde con la informacion.\n\n"
                    f"--- CONTEXTO DE PRODUCTOS DISPONIBLES ---\n{contexto}\n\n"
                    f"--- CONTEXTO DE INTERNET (si aplica) ---\n{internet_context}"
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
            model="gemini-2.5-flash", api_key=settings.GOOGLE_API_KEY
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

    def _search_internet(self, user_text: str) -> str:
        try:
            search = DuckDuckGoSearchAPIWrapper()
            results = search.results(user_text, max_results=3)
        except Exception:
            return ""

        lines = []
        for index, result in enumerate(results, start=1):
            title = result.get("title", "").strip()
            snippet = result.get("snippet", "").strip()
            link = result.get("link", "").strip()
            if not title and not snippet and not link:
                continue
            parts = []
            if title:
                parts.append(title)
            if snippet:
                parts.append(snippet)
            if link:
                parts.append(f"Fuente: {link}")
            lines.append(f"Resultado {index}: " + ". ".join(parts))
        return "\n".join(lines)
