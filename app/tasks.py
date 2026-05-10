import psycopg2
from urllib.parse import quote_plus
from . import app
from django.conf import settings
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2", api_key=settings.GOOGLE_API_KEY
)

password = quote_plus(settings.DATABASES["rag"]["PASSWORD"])
VECTOR_DB_URL = f"postgresql+psycopg://{settings.DATABASES['rag']['USER']}:{password}@{settings.DATABASES['rag']['HOST']}:{settings.DATABASES['rag']['PORT']}/{settings.DATABASES['rag']['NAME']}"


@app.task
def update_product_embeddings():
    conn = psycopg2.connect(
        dbname=settings.DATABASES["default"]["NAME"],
        user=settings.DATABASES["default"]["USER"],
        password=settings.DATABASES["default"]["PASSWORD"],
        host=settings.DATABASES["default"]["HOST"],
        port=settings.DATABASES["default"]["PORT"],
    )
    cursor = conn.cursor()

    # cursor.execute(
  #       "SELECT id, name, description, category, price, stock, is_active FROM products WHERE embedding IS NULL OR embedding = '' AND updated_at < NOW() - INTERVAL '1 day'"
    # )
    cursor.execute(
        "SELECT id, name, description, category, price, stock, is_active FROM products WHERE embedding IS NULL"
    )
    products = cursor.fetchall()

    documents = []
    for product in products:
        id, name, description, category = product
        doc = Document(
            page_content=f"Product name: {name}\nProduct description: {description}",
            metadata={
                "original_id": id,
                "category": category,
            },
        )
        documents.append(doc)

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="product_embeddings",
        connection=VECTOR_DB_URL,
        use_jsonb=True,
    )

    if documents:
        vector_store.add_documents(documents)

        products_ids = [doc.metadata["original_id"] for doc in documents]
        cursor.execute(
            "UPDATE products SET embedding = TRUE WHERE id IN %s",
            (tuple(products_ids),),
        )
        conn.commit()

    cursor.close()
    conn.close()

    return f"Updated embeddings for {len(documents)} products"
