# REST API

## Overview

REST (Representational State Transfer) is an architectural style for designing networked applications. It relies on stateless, client-server communication using HTTP.

## Key Characteristics

- **Stateless** - Each request contains all information needed to process it.
- **Client-Server** - Separation of concerns between UI and data storage.
- **Cacheable** - Responses can be cached to improve performance.
- **Uniform Interface** - Standardized way of communicating between client and server.
- **Layered System** - Architecture can be composed of hierarchical layers.

## HTTP Methods

```
|---------|--------------------------|------------|------|
| Method  | Purpose                  | Idempotent | Safe |
|---------|--------------------------|------------|------|
| GET     | Retrieve resource.       | Yes        | Yes  |
| POST    | Create resource.         | No         | No   |
| PUT     | Update/Replace resource. | Yes        | No   |
| PATCH   | Partial update.          | No         | No   |
| DELETE  | Remove resource.         | Yes        | No   |
| HEAD    | Get metadata only.       | Yes        | Yes  |
| OPTIONS | Get supported methods.   | Yes        | Yes  |
|---------|--------------------------|------------|------|
```

## Status Codes

### Success (2xx)
- **200 OK** - Request succeeded.
- **201 Created** - Resource created successfully.
- **204 No Content** - Success with no response body.

### Client Errors (4xx)
- **400 Bad Request** - Invalid request format.
- **401 Unauthorized** - Authentication required.
- **403 Forbidden** - Authenticated but not authorized.
- **404 Not Found** - Resource doesn't exist.
- **429 Too Many Requests** - Rate limit exceeded.

### Server Errors (5xx)
- **500 Internal Server Error** - Generic server error.
- **502 Bad Gateway** - Invalid response from upstream.
- **503 Service Unavailable** - Temporary overload/maintenance.

## URL Design Patterns

```
Good:
  GET /users              # List users
  GET /users/123          # Get specific user
  POST /users             # Create user
  PUT /users/123          # Update user
  DELETE /users/123       # Delete user
  GET /users/123/orders   # Get user's orders

Bad:
  GET /getUser?id=123     # Non-RESTful
  POST /createUser        # Verb in URL
  GET /users/delete/123   # Wrong method
```

## Request/Response Format

### Request Example

```http
POST /api/v1/users HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGc...

{
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Response Example

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/users/456

{
  "id": 456,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Pagination

### Offset-based

```
GET /users?offset=20&limit=10
```

### Cursor-based (preferred for large datasets)

```
GET /users?cursor=eyJpZCI6MTIzfQ&limit=10

Response:
{
  "data": [...],
  "next_cursor": "eyJpZCI6MTMzfQ",
  "has_more": true
}
```

## Filtering & Sorting

```
GET /users?status=active&role=admin&sort=-created_at,name
```

## Versioning Strategies

1. **URL Path** - `/api/v1/users` (most common).
2. **Header** - `Accept: application/vnd.company.v1+json`.
3. **Query Parameter** - `/users?version=1` (least preferred).

## Architecture Diagram

```
┌─────────┐                ┌──────────────┐                ┌──────────┐
│ Client  │───── HTTP ────▶│  API Gateway │───────────────▶│ Service  │
│         │◀──── REST ─────│              │◀───────────────│  Layer   │
└─────────┘                └──────────────┘                └──────────┘
                                  │                             │
                                  ▼                             ▼
                            ┌────────────┐                 ┌──────────┐
                            │   Cache    │                 │ Database │
                            │  (Redis)   │                 │          │
                            └────────────┘                 └──────────┘
```

## When to Use REST

### ✅ Good For:

- CRUD operations.
- Public APIs.
- Simple resource-based systems.
- When HTTP caching is important.
- Mobile apps with intermittent connectivity.

### ❌ Less Ideal For:

- Real-time bidirectional communication.
- Complex queries spanning multiple resources.
- When you need strong typing/contracts.
- Very high-frequency updates.

## System Design Considerations

### Scalability

- **Stateless design** enables horizontal scaling.
- Use **load balancers** to distribute requests.
- Implement **caching** at multiple layers (CDN, API Gateway, Application).
- Consider **rate limiting** to prevent abuse.

### Security

- Use **HTTPS** for all communications.
- Implement **authentication** (OAuth 2.0, JWT).
- Apply **rate limiting** per user/IP.
- Validate and sanitize all inputs.
- Use **CORS** policies appropriately.

### Performance

- Enable **HTTP caching** headers (ETag, Cache-Control).
- Use **compression** (gzip, brotli).
- Implement **pagination** for large datasets.
- Consider **partial responses** (field filtering).
- Add **CDN** for static/cacheable content.

### Reliability

- Implement **retry logic** with exponential backoff.
- Use **circuit breakers** for downstream services.
- Design **idempotent** operations when possible.
- Implement **health check endpoints**.
- Use **timeouts** appropriately.

## Common Interview Questions

1. **How would you design a RESTful API for [X system]?**
   - Define resources and their relationships.
   - Choose appropriate HTTP methods.
   - Design URL structure.
   - Consider pagination, filtering, versioning.

2. **How do you handle rate limiting?**
   - Token bucket / leaky bucket algorithms.
   - Redis-based counters.
   - Return 429 status with Retry-After header.

3. **REST vs GraphQL vs gRPC?**
   - REST: Simple, cacheable, wide support.
   - GraphQL: Flexible queries, reduces over-fetching.
   - gRPC: High performance, binary protocol, streaming.

4. **How do you ensure API backwards compatibility?**
   - Versioning strategy.
   - Additive changes only.
   - Deprecation notices.
   - Support multiple versions simultaneously.

## Best Practices

- Use nouns for resources, not verbs.
- Return appropriate status codes.
- Use plural names for collections (`/users`, not `/user`).
- Implement HATEOAS for discoverability (optional).
- Document your API (OpenAPI/Swagger).
- Use consistent naming conventions (snake_case or camelCase).
- Include request IDs for tracing.
- Version your API from day one.

## Trade-offs

```
|---------------|-----------------------------------|-------------------------------------|
| Aspect        | Advantage                         | Disadvantage                        |
|---------------|-----------------------------------|-------------------------------------|
| Simplicity    | Easy to understand and implement. | Can be verbose for complex queries. |
| Caching       | HTTP caching well-understood.     | Cache invalidation can be complex.  |
| Tooling       | Extensive tooling support.        | No built-in schema validation.      |
| Over-fetching | Fixed endpoints.                  | May need multiple requests.         |
|---------------|-----------------------------------|-------------------------------------|
```

## Related Patterns

- [GraphQL](../graphql/README.md) - Alternative query language.
- [gRPC](../grpc/README.md) - High-performance RPC.
- [WebSocket](../websocket/README.md) - Real-time bidirectional.
- [Server-Sent Events](../server-sent-events/README.md) - Server push.
- [Webhooks](../webhook/README.md) - Event-driven notifications.
