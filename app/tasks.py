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
def update_product_embeddings(product_ids=None):
    from .api.products.product_model import ProductModel

    if product_ids:
        queryset = ProductModel.objects.filter(id__in=product_ids)
    else:
        queryset = ProductModel.objects.filter(embedding__isnull=True)

    products = list(
        queryset.values(
            "id",
            "name",
            "description",
            "category",
            "price",
            "stock",
            "is_active",
        )
    )

    texts = []
    metadatas = []
    document_ids = []
    for product in products:
        texts.append(
            f"Product name: {product['name']}\n"
            f"Product description: {product['description']}\n"
            f"Category: {product['category']}\n"
            f"Price: {product['price']}\n"
            f"Stock: {product['stock']}\n"
            f"Active: {product['is_active']}"
        )
        metadatas.append(
            {
                "original_id": str(product["id"]),
                "category": product["category"],
            }
        )
        document_ids.append(str(product["id"]))

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="product_embeddings",
        connection=VECTOR_DB_URL,
        use_jsonb=True,
    )

    if texts:
        for text, metadata, doc_id in zip(texts, metadatas, document_ids, strict=False):
            vector_store.add_texts(texts=[text], metadatas=[metadata], ids=[doc_id])

        product_ids = [meta["original_id"] for meta in metadatas]
        ProductModel.objects.filter(id__in=product_ids).update(embedding="true")

    return f"Updated embeddings for {len(texts)} products"
