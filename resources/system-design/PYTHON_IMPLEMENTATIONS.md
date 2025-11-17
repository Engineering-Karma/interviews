# Python API Implementations

Complete FastAPI implementations of all API patterns for system design interview preparation.

## Implementations

### ✅ Completed

1. **REST API** (`rest-api/implementation/python/`)
   - Full CRUD with proper HTTP methods
   - Pagination, sorting, filtering
   - Rate limiting and authentication
   - Auto-generated OpenAPI docs
   
2. **WebSocket** (`websocket/implementation/python/`)
   - Bidirectional real-time communication
   - Room/channel subscriptions
   - Broadcasting and private messages
   - Heartbeat and connection management
   
3. **Server-Sent Events** (`server-sent-events/implementation/python/`)
   - Unidirectional server push
   - Event replay with Last-Event-ID
   - Multiple event streams
   - Stock ticker and notifications examples

### 🚧 Pending (Template Provided)

4. **GraphQL** (`graphql/implementation/python/`)
   - Use Strawberry or Graphene
   - Query, mutations, subscriptions
   - DataLoader for N+1 prevention
   
5. **gRPC** (`grpc/implementation/python/`)
   - Protocol Buffers definitions
   - Unary and streaming RPCs
   - Interceptors for middleware
   
6. **Webhooks** (`webhook/implementation/python/`)
   - Webhook receiver with signature verification
   - Webhook sender with retry logic
   - Async processing with queues

## Quick Start

### Installation

```bash
# Navigate to any implementation directory
cd rest-api/implementation/python/

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

### Common Requirements

All implementations use:
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

## REST API

**Port**: 8000  
**Docs**: http://localhost:8000/docs

```bash
cd rest-api/implementation/python/
python main.py
```

**Key Endpoints**:
- `GET /api/v1/users` - List users (paginated)
- `POST /api/v1/users` - Create user (auth required)
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user (full)
- `PATCH /api/v1/users/{id}` - Partial update
- `DELETE /api/v1/users/{id}` - Delete user

**Test**:
```bash
curl http://localhost:8000/api/v1/users
```

## WebSocket

**Port**: 8000  
**Test Client**: http://localhost:8000

```bash
cd websocket/implementation/python/
python main.py
```

**Endpoints**:
- `ws://localhost:8000/ws` - Main WebSocket
- `ws://localhost:8000/ws/chat/{room}` - Chat room

**Message Format**:
```json
{
  "type": "message|subscribe|unsubscribe|ping",
  "room": "room_name",
  "data": {...}
}
```

**Test with wscat**:
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws
```

## Server-Sent Events

**Port**: 8000  
**Test Client**: http://localhost:8000

```bash
cd server-sent-events/implementation/python/
python main.py
```

**Endpoints**:
- `/events` - General event stream
- `/notifications/{user_id}` - User notifications
- `/stocks` - Stock price updates

**Test**:
```bash
curl -N http://localhost:8000/events
```

## Interview Talking Points

### REST API
- Stateless design for horizontal scaling
- HTTP caching with proper headers
- Idempotent operations (PUT, DELETE)
- Rate limiting strategies
- Pagination patterns (offset vs cursor)

### WebSocket
- Connection management at scale
- Broadcasting patterns
- Sticky sessions for load balancing
- Message broker for multi-server (Redis Pub/Sub)
- Heartbeat for dead connection detection

### Server-Sent Events
- Simpler than WebSocket for one-way push
- Automatic reconnection built-in
- Event replay with Last-Event-ID
- Proxy-friendly (HTTP-based)
- Browser connection limits (~6 per domain)

### GraphQL (To Implement)
- Solving over-fetching and under-fetching
- N+1 query problem and DataLoader solution
- Query complexity analysis
- Schema-first development

### gRPC (To Implement)
- Binary protocol for performance
- HTTP/2 multiplexing
- Strong typing with Protocol Buffers
- Streaming (unary, server, client, bidirectional)

### Webhooks (To Implement)
- Event-driven architecture
- Retry with exponential backoff
- HMAC signature verification
- Idempotency with delivery IDs
- Dead letter queues for failures

## Production Considerations

### All Implementations Need:
1. **Database**: Replace in-memory storage with PostgreSQL/MongoDB
2. **Caching**: Redis for sessions, rate limiting, pub/sub
3. **Authentication**: OAuth 2.0, JWT tokens
4. **Monitoring**: Prometheus metrics, logging
5. **Load Balancing**: NGINX, HAProxy
6. **Message Queue**: RabbitMQ, Kafka for async processing
7. **Service Mesh**: Istio for gRPC
8. **API Gateway**: Kong, Tyk for centralized management

### Scaling Patterns:
- **Horizontal**: Stateless services, load balancers
- **Caching**: Multi-layer (CDN, Application, Database)
- **Database**: Read replicas, sharding
- **Async**: Message queues for long-running tasks

## Testing

### Unit Tests
```bash
pip install pytest pytest-asyncio httpx
pytest tests/
```

### Load Testing
```bash
pip install locust
locust -f locustfile.py
```

### Integration Tests
```bash
# Use pytest with FastAPI TestClient
from fastapi.testclient import TestClient
```

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- Uvicorn: https://www.uvicorn.org/
- WebSocket Testing: https://github.com/websockets/wscat

## Next Steps

To complete the remaining implementations:

1. **GraphQL**: Use Strawberry (`pip install strawberry-graphql`)
2. **gRPC**: Use grpcio and protobuf compiler
3. **Webhooks**: Implement both sender and receiver patterns

Each should follow the same structure:
- `main.py` - Main application
- `requirements.txt` - Dependencies
- `README.md` - Usage instructions
- Test client (HTML or CLI)
