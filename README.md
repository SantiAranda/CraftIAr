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

Base URL: `/api`

### Productos

`GET /api/products`

- Uso: listar productos.
- Query params: ninguno.
- Response 200: lista de productos.

Ejemplo de request

```bash
curl http://localhost:8000/api/products
```

Ejemplo de response 200

```json
[
  {
    "id": 1,
    "sku": "SKU-001",
    "name": "Cemento Portland",
    "description": "Bolsa 50kg",
    "category": "cemento",
    "price": "12.50",
    "stock": 20,
    "is_active": true,
    "created_at": "2026-05-10T10:00:00Z",
    "updated_at": "2026-05-10T10:00:00Z"
  }
]
```

`POST /api/products`

- Uso: crear producto.
- Body JSON requerido:
  - `sku` (string, sin espacios, max 64)
  - `name` (string, max 255)
  - `price` (decimal > 0)
  - `stock` (integer >= 0)
- Body JSON opcional:
  - `description` (string)
  - `category` (string)
  - `is_active` (boolean, default true)
- Response 201: producto creado.
- Response 400: errores de validacion.

Ejemplo de request

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-002","name":"Arena fina","price":"8.90","stock":50,"description":"Bolsa 25kg","category":"arena"}' \
  http://localhost:8000/api/products
```

Ejemplo de response 201

```json
{
  "id": 2,
  "sku": "SKU-002",
  "name": "Arena fina",
  "description": "Bolsa 25kg",
  "category": "arena",
  "price": "8.90",
  "stock": 50,
  "is_active": true,
  "created_at": "2026-05-10T10:05:00Z",
  "updated_at": "2026-05-10T10:05:00Z"
}
```

`GET /api/products/<product_id>`

- Uso: obtener un producto por id.
- Response 200: producto.
- Response 404: no encontrado.

Ejemplo de request

```bash
curl http://localhost:8000/api/products/1
```

Ejemplo de response 404

```json
{
  "detail": "Not found."
}
```

`PUT /api/products/<product_id>`

- Uso: reemplazar un producto completo.
- Body JSON requerido: mismos campos que en POST.
- Response 200: producto actualizado.
- Response 400: errores de validacion.
- Response 404: no encontrado.

Ejemplo de request

```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"sku":"SKU-001","name":"Cemento Portland","price":"13.00","stock":18,"description":"Bolsa 50kg","category":"cemento","is_active":true}' \
  http://localhost:8000/api/products/1
```

Ejemplo de response 200

```json
{
  "id": 1,
  "sku": "SKU-001",
  "name": "Cemento Portland",
  "description": "Bolsa 50kg",
  "category": "cemento",
  "price": "13.00",
  "stock": 18,
  "is_active": true,
  "created_at": "2026-05-10T10:00:00Z",
  "updated_at": "2026-05-10T10:10:00Z"
}
```

`PATCH /api/products/<product_id>`

- Uso: actualizar parcialmente.
- Body JSON: cualquier subset de los campos del POST.
- Response 200: producto actualizado.
- Response 400: errores de validacion.
- Response 404: no encontrado.

Ejemplo de request

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"stock":15}' \
  http://localhost:8000/api/products/1
```

`DELETE /api/products/<product_id>`

- Uso: eliminar producto.
- Response 204: sin contenido.
- Response 404: no encontrado.

Ejemplo de request

```bash
curl -X DELETE http://localhost:8000/api/products/1
```

Producto (response JSON)

```json
{
  "id": 1,
  "sku": "SKU-001",
  "name": "Cemento Portland",
  "description": "Bolsa 50kg",
  "category": "cemento",
  "price": "12.50",
  "stock": 20,
  "is_active": true,
  "created_at": "2026-05-10T10:00:00Z",
  "updated_at": "2026-05-10T10:00:00Z"
}
```

Errores de validacion (response JSON)

```json
{
  "price": ["Price must be greater than 0."]
}
```

### Chat (RAG)

`POST /api/chat/`

- Uso: crear una sesion de chat.
- Body: vacio.
- Response 201:

```json
{
  "id": "b7c4b2e6-6f2a-4b5b-9c22-2c6a9f8f6b1a",
  "created_at": "2026-05-10T10:00:00Z",
  "messages": []
}
```

`GET /api/chat/<uuid>/`

- Uso: obtener el historial de la sesion.
- Response 200:

```json
{
  "id": "b7c4b2e6-6f2a-4b5b-9c22-2c6a9f8f6b1a",
  "created_at": "2026-05-10T10:00:00Z",
  "messages": [
    {
      "id": 1,
      "session": "b7c4b2e6-6f2a-4b5b-9c22-2c6a9f8f6b1a",
      "role": "user",
      "content": "Busco cemento para obra",
      "created_at": "2026-05-10T10:01:00Z"
    }
  ]
}
```

- Response 404: no encontrado.

`POST /api/chat/<uuid>/stream/`

- Uso: enviar mensaje y recibir respuesta en streaming (SSE).
- Headers recomendados:
  - `Content-Type: application/json`
  - `Accept: text/event-stream`
- Body JSON requerido:
  - `message` (string)
- Response 200: stream SSE con eventos `data: {"response": "..."}` y cierre `data: [DONE]`.
- Response 400: falta `message`.
- Response 404: sesion no encontrada.

Ejemplo de request

```bash
curl -N -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"Necesito ladrillos huecos"}' \
  http://localhost:8000/api/chat/<uuid>/stream/
```

## Notas

- Configura `GOOGLE_API_KEY` y define `RAG_EMBEDDINGS_PROVIDER`/`RAG_LLM_PROVIDER`.
