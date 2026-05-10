# RAG Django (catalogo ecommerce)

Proyecto base para un modulo RAG en Django + PostgreSQL (pgvector), con Redis, Celery y Channels.
Este repositorio solo configura el entorno y la estructura inicial para integrarse a un ecommerce.

## Requisitos

- Docker y Docker Compose

## Configuracion rapida

1) Copia variables de entorno

```bash
cp .env.example .env
```

2) Levanta los servicios

```bash
docker compose up --build
```

## Servicios

- app: Django + Uvicorn
- db: PostgreSQL con pgvector
- redis: cache y broker
- celery: worker
- celery-beat: scheduler

## Endpoints

no hay todavia xd

## Notas

- Configura `GOOGLE_API_KEY` y define `RAG_EMBEDDINGS_PROVIDER`/`RAG_LLM_PROVIDER`.
