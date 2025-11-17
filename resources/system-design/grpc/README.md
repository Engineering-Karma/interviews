# gRPC

## Overview

gRPC (gRPC Remote Procedure Call) is a high-performance, open-source RPC framework developed by Google. It uses HTTP/2 for transport, Protocol Buffers as the interface description language, and provides features like authentication, load balancing, and more.

## Key Characteristics

- **High performance** - Binary serialization with Protocol Buffers.
- **HTTP/2 based** - Multiplexing, flow control, header compression.
- **Strongly typed** - Contract-first API development.
- **Streaming** - Client, server, and bidirectional streaming.
- **Code generation** - Auto-generate client/server code.
- **Language agnostic** - Support for many programming languages.

## Communication Patterns

### 1. Unary RPC (Request-Response)

```
Client ──── request ────▶ Server
Client ◀─── response ──── Server
```

### 2. Server Streaming

```
Client ──── request ───▶ Server
Client ◀─── stream ───── Server
Client ◀─── stream ───── Server
Client ◀─── stream ───── Server
```

### 3. Client Streaming

```
Client ──── stream ─────▶ Server
Client ──── stream ─────▶ Server
Client ──── stream ─────▶ Server
Client ◀─── response ──── Server
```

### 4. Bidirectional Streaming

```
Client ──── stream ───▶ Server
Client ◀─── stream ──── Server
Client ──── stream ───▶ Server
Client ◀─── stream ──── Server
```

## Protocol Buffers Definition

```protobuf
syntax = "proto3";

package user;

service UserService {
  // Unary
  rpc GetUser(GetUserRequest) returns (User);
  
  // Server streaming
  rpc ListUsers(ListUsersRequest) returns (stream User);
  
  // Client streaming
  rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
  
  // Bidirectional streaming
  rpc ChatStream(stream ChatMessage) returns (stream ChatMessage);
}

message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
  int64 created_at = 4;
}

message GetUserRequest {
  int32 id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
}
```

## Architecture Diagram

```
┌──────────────┐              ┌──────────────┐
│    Client    │              │    Server    │
│              │              │              │
│  ┌────────┐  │   HTTP/2     │  ┌────────┐  │
│  │  Stub  │  │─────────────▶│  │Service │  │
│  │(Proto) │  │◀─────────────│  │ Impl   │  │
│  └────────┘  │  Protocol    │  └────────┘  │
│              │   Buffers    │              │
└──────────────┘              └──────┬───────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  Database   │
                              └─────────────┘
```

## gRPC vs REST vs GraphQL

```
|-----------------|-------------------|---------------------|---------------|
| Feature         | gRPC              | REST                | GraphQL       |
|-----------------|-------------------|---------------------|---------------|
| Protocol        | HTTP/2            | HTTP/1.1            | HTTP/1.1      |
| Payload         | Binary (Protobuf) | JSON/XML            | JSON          |
| API contract    | Strong (.proto)   | Loose (docs)        | Schema (SDL)  |
| Streaming       | Yes (4 types)     | No (SSE workaround) | Subscriptions |
| Browser support | Limited           | Native              | Native        |
| Performance     | Excellent         | Good                | Good          |
| Tooling         | Good              | Excellent           | Excellent     |
| Learning curve  | Steep             | Easy                | Moderate      |
|-----------------|-------------------|---------------------|---------------|
```

## HTTP/2 Benefits

### Multiplexing
- Multiple requests over single connection
- No head-of-line blocking
- Better resource utilization

### Header Compression
- HPACK compression reduces overhead
- Significant for many small requests

### Server Push
- Server can proactively send resources
- Reduces latency for dependent data

### Flow Control
- Per-stream flow control
- Prevents resource exhaustion

## Error Handling

### Status Codes
```
OK                  = 0
CANCELLED           = 1
UNKNOWN             = 2
INVALID_ARGUMENT    = 3
DEADLINE_EXCEEDED   = 4
NOT_FOUND           = 5
ALREADY_EXISTS      = 6
PERMISSION_DENIED   = 7
RESOURCE_EXHAUSTED  = 8
FAILED_PRECONDITION = 9
ABORTED             = 10
OUT_OF_RANGE        = 11
UNIMPLEMENTED       = 12
INTERNAL            = 13
UNAVAILABLE         = 14
DATA_LOSS           = 15
UNAUTHENTICATED     = 16
```

### Error Response
```protobuf
message Error {
  int32 code = 1;
  string message = 2;
  repeated ErrorDetail details = 3;
}

message ErrorDetail {
  string field = 1;
  string description = 2;
}
```

## Load Balancing Strategies

### 1. Proxy Load Balancing
```
         ┌─────────┐
         │   LB    │
         └────┬────┘
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│Server 1│ │Server 2│ │Server 3│
└────────┘ └────────┘ └────────┘
```

### 2. Client-Side Load Balancing
```
┌──────────┐
│  Client  │
│  (with   │
│ resolver)│
└─────┬────┘
  ┌───┼───┐
  ▼   ▼   ▼
┌────┐ ┌────┐ ┌────┐
│ S1 │ │ S2 │ │ S3 │
└────┘ └────┘ └────┘
```

### 3. Service Mesh (e.g., Istio)
```
┌──────┐     ┌──────┐     ┌──────┐
│Client│────▶│Proxy │────▶│Server│
└──────┘     │(Envoy)     └──────┘
             └──────┘
        (handles routing,
         auth, metrics)
```

## When to Use gRPC

### ✅ Good For:
- Microservices communication
- Real-time streaming data
- Mobile clients (bandwidth efficiency)
- Polyglot environments
- High-performance requirements
- Internal APIs with defined contracts
- Point-to-point communication

### ❌ Less Ideal For:
- Browser-based applications (limited support)
- External public APIs
- When human-readable format needed
- Simple CRUD operations
- When REST ecosystem/tooling is required

## System Design Considerations

### Scalability
- **Stateless services**: Enable horizontal scaling
- **Connection pooling**: Reuse connections efficiently
- **Load balancing**: Client-side or proxy-based
- **Service discovery**: Integrate with Consul, etcd, Kubernetes
- **Sharding**: Partition data across services

### Performance
- **Binary serialization**: Smaller payloads than JSON
- **HTTP/2 multiplexing**: Efficient connection usage
- **Streaming**: Reduce latency for large datasets
- **Connection reuse**: Persistent connections
- **Deadline propagation**: Cancel unnecessary work

### Reliability
- **Retries**: Built-in retry mechanisms
- **Deadlines/Timeouts**: Prevent cascading failures
- **Circuit breakers**: Fail fast when service is down
- **Health checks**: Monitor service availability
- **Interceptors**: Add cross-cutting concerns (logging, auth)

### Security
- **TLS/SSL**: Encrypt data in transit
- **Token-based auth**: JWT, OAuth tokens
- **Interceptors**: Validate authentication
- **mTLS**: Mutual authentication between services
- **Authorization**: Role-based access control

## Advanced Features

### Metadata
```go
// Add metadata to request
md := metadata.Pairs(
    "authorization", "Bearer token123",
    "request-id", "req-456",
)
ctx := metadata.NewOutgoingContext(context.Background(), md)
```

### Deadlines/Timeouts
```go
// Set deadline for request
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

resp, err := client.GetUser(ctx, req)
```

### Interceptors (Middleware)
```go
// Logging interceptor
func loggingInterceptor(ctx context.Context, req interface{}, 
    info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (
    interface{}, error) {
    
    start := time.Now()
    resp, err := handler(ctx, req)
    log.Printf("Method: %s, Duration: %s", 
        info.FullMethod, time.Since(start))
    
    return resp, err
}
```

## Versioning Strategies

### 1. Add New Service
```protobuf
service UserServiceV1 { ... }
service UserServiceV2 { ... }
```

### 2. Add New Methods
```protobuf
service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc GetUserV2(GetUserV2Request) returns (UserV2);
}
```

### 3. Backward Compatible Changes
```protobuf
// Add optional fields (backward compatible)
message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
  optional string phone = 4;  // New field
}
```

## Common Interview Questions

1. **How does gRPC achieve high performance?**
   - Binary serialization (Protocol Buffers)
   - HTTP/2 multiplexing and compression
   - Connection reuse
   - Efficient encoding/decoding

2. **When would you choose gRPC over REST?**
   - Microservices internal communication
   - Need for streaming
   - Performance-critical applications
   - Strong typing requirements
   - Polyglot environment

3. **How do you handle versioning in gRPC?**
   - Add new methods/services
   - Use optional fields
   - Maintain backward compatibility
   - Deprecated fields with comments

4. **How do you implement authentication in gRPC?**
   - Metadata with JWT tokens
   - Interceptors for validation
   - TLS for transport security
   - mTLS for mutual authentication

5. **How do you handle load balancing in gRPC?**
   - Client-side LB with resolver
   - Proxy-based LB (L4/L7)
   - Service mesh (Istio, Linkerd)
   - Round-robin, least-connection algorithms

## Best Practices

- Use semantic versioning for .proto files
- Never reuse field numbers in protobuf
- Always set deadlines/timeouts
- Implement proper error handling
- Use interceptors for cross-cutting concerns
- Enable connection pooling
- Implement health checks
- Use streaming for large data transfers
- Monitor metrics (latency, errors, throughput)
- Document your service contracts
- Use code generation for type safety

## Trade-offs

| Aspect | Advantage | Disadvantage |
|--------|-----------|-------------|
| Performance | Very high performance | Browser support limited |
| Type safety | Strong contracts | Steeper learning curve |
| Streaming | Native streaming support | More complex than REST |
| Tooling | Auto code generation | Less mature than REST ecosystem |
| Efficiency | Binary format | Not human-readable |

## Protobuf Best Practices

- Use `optional` for fields that might not be set
- Reserve deleted field numbers
- Use enums for fixed value sets
- Keep messages small and focused
- Use `repeated` for lists
- Don't change field types
- Use wrapper types for nullable primitives

## Monitoring & Observability

- **Metrics**: Request count, latency, error rate
- **Tracing**: Distributed tracing with OpenTelemetry
- **Logging**: Structured logs with request context
- **Health checks**: Implement health service
- **Interceptors**: Add observability at middleware layer

## Related Patterns

- [REST API](../rest-api/README.md) - HTTP-based API design
- [WebSocket](../websocket/README.md) - Bidirectional persistent connection
- [GraphQL](../graphql/README.md) - Flexible query language
- [Server-Sent Events](../server-sent-events/README.md) - Server push over HTTP
