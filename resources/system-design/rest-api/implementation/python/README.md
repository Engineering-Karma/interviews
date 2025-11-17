# REST API - Python Implementation

A production-ready REST API implementation using FastAPI demonstrating best practices for system design interviews.

## Features

- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- ✅ Request/response validation with Pydantic
- ✅ Pagination and sorting
- ✅ Rate limiting
- ✅ Authentication (Bearer token)
- ✅ Error handling
- ✅ Automatic OpenAPI documentation
- ✅ Health check endpoint

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8000
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Usage

### List Users
```bash
curl http://localhost:8000/api/v1/users?limit=10&offset=0
```

### Get User by ID
```bash
curl http://localhost:8000/api/v1/users/{user_id}
```

### Create User (requires auth)
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com"}'
```

### Update User (PUT - full replacement)
```bash
curl -X PUT http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","email":"jane.smith@example.com"}'
```

### Partial Update (PATCH)
```bash
curl -X PATCH http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Updated"}'
```

### Delete User
```bash
curl -X DELETE http://localhost:8000/api/v1/users/{user_id} \
  -H "Authorization: Bearer your-token-here"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Key Concepts Demonstrated

### 1. HTTP Methods & Status Codes
- **GET**: Retrieve resources (200 OK, 404 Not Found)
- **POST**: Create resources (201 Created)
- **PUT**: Full update (200 OK)
- **PATCH**: Partial update (200 OK)
- **DELETE**: Remove resources (204 No Content)

### 2. Pagination
```
GET /api/v1/users?limit=10&offset=20&sort=-created_at
```

### 3. Nested Resources
```
GET /api/v1/users/{user_id}/posts
POST /api/v1/users/{user_id}/posts
```

### 4. Error Responses
```json
{
  "detail": "User not found"
}
```

### 5. Rate Limiting
- 100 requests per hour for read operations
- 20 requests per hour for write operations

## Interview Talking Points

1. **Stateless Design**: Each request contains all necessary information
2. **Idempotency**: PUT and DELETE are idempotent
3. **Resource-Based URLs**: `/users`, `/posts` (nouns, not verbs)
4. **HTTP Semantics**: Proper use of methods and status codes
5. **Scalability**: Stateless design enables horizontal scaling
6. **Caching**: GET requests can be cached
7. **Versioning**: API versioned at `/api/v1/`
8. **Pagination**: Prevents large data transfers
9. **Rate Limiting**: Protects against abuse
10. **Documentation**: Auto-generated OpenAPI docs

## Production Considerations

For production use, consider:
- Real database (PostgreSQL, MySQL)
- Proper authentication/authorization (OAuth 2.0, JWT)
- Redis for rate limiting
- CORS configuration
- HTTPS/TLS
- Logging and monitoring
- Connection pooling
- Caching layer (Redis, Memcached)
- API Gateway (rate limiting, auth)
- Load balancer
