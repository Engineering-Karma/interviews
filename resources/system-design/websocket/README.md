# WebSocket

## Overview

WebSocket is a protocol providing full-duplex communication channels over a single TCP connection. It enables real-time, bidirectional communication between client and server with lower overhead than HTTP.

## Key Characteristics

- **Full-duplex**: Both client and server can send messages simultaneously
- **Persistent connection**: Single long-lived connection vs multiple HTTP requests
- **Low latency**: No HTTP overhead after initial handshake
- **Real-time**: Instant message delivery in both directions
- **Efficient**: Lower bandwidth usage compared to polling

## Connection Lifecycle

```
┌────────┐                                    ┌────────┐
│ Client │                                    │ Server │
└───┬────┘                                    └───┬────┘
    │                                             │
    │  HTTP Upgrade Request                       │
    │  GET /chat HTTP/1.1                         │
    │  Upgrade: websocket                         │
    │  Connection: Upgrade                        │
    │────────────────────────────────────────────▶│
    │                                             │
    │  HTTP 101 Switching Protocols               │
    │◀────────────────────────────────────────────│
    │                                             │
    │════════════ WebSocket Connection ═══════════│
    │                                             │
    │  Message (client → server)                  │
    │────────────────────────────────────────────▶│
    │                                             │
    │  Message (server → client)                  │
    │◀────────────────────────────────────────────│
    │                                             │
    │  Ping                                       │
    │────────────────────────────────────────────▶│
    │  Pong                                       │
    │◀────────────────────────────────────────────│
    │                                             │
    │  Close Frame                                │
    │────────────────────────────────────────────▶│
    │  Close Frame                                │
    │◀────────────────────────────────────────────│
    │                                             │
```

## Handshake Process

### Client Request
```http
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: http://example.com
```

### Server Response
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

## Message Types

- **Text frames**: UTF-8 encoded text data
- **Binary frames**: Raw binary data
- **Control frames**: 
  - Ping/Pong: Keep-alive and latency measurement
  - Close: Graceful connection termination

## Architecture Patterns

### Simple WebSocket Server
```
┌─────────┐     WebSocket     ┌────────────────┐
│ Client  │◀─────────────────▶│  WS Server     │
└─────────┘                   │  (stateful)    │
                              └────────┬───────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │    Database    │
                              └────────────────┘
```

### Scalable WebSocket Architecture
```
┌─────────┐                  ┌────────────────┐
│ Client  │◀────────────────▶│  WS Server 1   │
└─────────┘                  └───────┬────────┘
                                     │
┌─────────┐                  ┌───────┴────────┐      ┌─────────────┐
│ Client  │◀────────────────▶│  Load Balancer │      │   Message   │
└─────────┘                  └───────┬────────┘      │   Broker    │
                                     │               │  (Redis/    │
┌─────────┐                  ┌───────┴────────┐      │   Kafka)    │
│ Client  │◀────────────────▶│  WS Server 2   │      └──────┬──────┘
└─────────┘                  └───────┬────────┘             │
                                     │                      │
                                     └──────────────────────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │    Database      │
                                    └──────────────────┘
```

## Connection Management

### Heartbeat/Ping-Pong
```javascript
// Client side
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

### Reconnection Strategy
```javascript
function connectWithRetry(url, maxRetries = 5) {
  let retries = 0;
  
  function connect() {
    const ws = new WebSocket(url);
    
    ws.onclose = () => {
      if (retries < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retries), 30000);
        setTimeout(connect, delay);
        retries++;
      }
    };
    
    ws.onopen = () => {
      retries = 0; // Reset on success
    };
  }
  
  connect();
}
```

## Scaling Challenges

### 1. Sticky Sessions
- Load balancers must route client to same server
- Use IP hash or session cookies
- Limits horizontal scalability

### 2. Message Broadcasting
- Need pub/sub system (Redis, Kafka, RabbitMQ)
- Each server subscribes to message channels
- Broadcasts to connected clients

### 3. Connection State
- Each server maintains active connections
- State stored in memory (not in database)
- Need connection registry for presence

### 4. Resource Usage
- Each connection consumes server resources
- Monitor: open connections, memory, CPU
- Implement connection limits per server

## Message Protocol Design

```json
{
  "type": "message",
  "id": "msg_12345",
  "timestamp": 1234567890,
  "data": {
    "room": "general",
    "user": "john",
    "content": "Hello, world!"
  }
}
```

### Common Message Types
- `auth`: Authentication after connection
- `subscribe`: Join room/channel
- `unsubscribe`: Leave room/channel
- `message`: User message
- `ping/pong`: Keep-alive
- `error`: Error notification
- `ack`: Message acknowledgment

## When to Use WebSocket

### ✅ Good For:
- Chat applications
- Real-time gaming
- Live sports scores/trading platforms
- Collaborative editing (Google Docs)
- Live dashboards and monitoring
- IoT device communication
- Real-time notifications

### ❌ Less Ideal For:
- Simple request-response patterns
- When HTTP caching is important
- Infrequent updates (use SSE or polling)
- When client is behind restrictive proxies
- RESTful CRUD operations

## System Design Considerations

### Scalability
- **Horizontal scaling**: Use message broker for cross-server communication
- **Connection limits**: Set max connections per server instance
- **Sticky sessions**: Configure load balancer appropriately
- **Health checks**: Implement connection health monitoring
- **Auto-scaling**: Scale based on connection count and CPU/memory

### Reliability
- **Heartbeat mechanism**: Detect dead connections
- **Automatic reconnection**: Client-side exponential backoff
- **Message acknowledgment**: Ensure delivery with ACKs
- **Message queuing**: Buffer messages during disconnection
- **Graceful degradation**: Fall back to long polling

### Security
- Use **WSS** (WebSocket Secure) over TLS
- **Authenticate** connections (token in handshake)
- **Validate origin** to prevent CSRF
- **Rate limiting** to prevent abuse
- **Input validation** on all messages
- **Connection limits** per user/IP

### Performance
- **Binary frames** for smaller payload size
- **Message compression**: Use permessage-deflate extension
- **Connection pooling**: Reuse connections when possible
- **Efficient serialization**: Protocol Buffers, MessagePack
- **Memory management**: Clear inactive connections

## Comparison with Alternatives

| Feature | WebSocket | SSE | Long Polling | REST |
|---------|-----------|-----|--------------|------|
| Bidirectional | Yes | No | Yes | No |
| Real-time | Yes | Yes | Moderate | No |
| Overhead | Low | Low | High | High |
| Browser support | Excellent | Good | Universal | Universal |
| Complexity | High | Low | Medium | Low |
| Proxy-friendly | Moderate | Good | Excellent | Excellent |

## Common Interview Questions

1. **How do you scale WebSocket servers horizontally?**
   - Use sticky sessions or consistent hashing
   - Implement pub/sub with Redis/Kafka
   - Store connection registry in shared cache
   - Handle cross-server message routing

2. **How do you handle connection failures?**
   - Client-side reconnection with exponential backoff
   - Message queuing during disconnection
   - Heartbeat/ping-pong for detection
   - Idempotent message handling

3. **WebSocket vs Server-Sent Events?**
   - WebSocket: Bidirectional, more complex, better for chat
   - SSE: Unidirectional (server→client), simpler, automatic reconnection

4. **How do you authenticate WebSocket connections?**
   - Send token in initial handshake (query param or header)
   - Authenticate first message after connection
   - Use short-lived tokens, refresh periodically
   - Close connection on auth failure

5. **How do you implement a chat room system?**
   - User connects and authenticates
   - Subscribe to room channels
   - Use pub/sub for message distribution
   - Broadcast to all room subscribers
   - Track online presence

## Best Practices

- Always use WSS (secure WebSocket) in production
- Implement heartbeat mechanism (30-60 second interval)
- Set connection and message size limits
- Handle reconnection on client side
- Use message acknowledgments for critical data
- Implement proper error handling and logging
- Monitor connection metrics (count, duration, errors)
- Design clear message protocol with versioning
- Implement graceful shutdown handling
- Use binary frames for non-text data

## Trade-offs

| Aspect | Advantage | Disadvantage |
|--------|-----------|-------------|
| Latency | Very low latency | Complex to scale horizontally |
| Overhead | Minimal after handshake | Initial setup more complex |
| Statefulness | Persistent connection | Harder to load balance |
| Complexity | Rich real-time features | More moving parts to maintain |
| Resource usage | Efficient for high-frequency | Holds server resources per connection |

## Related Patterns

- [Server-Sent Events](../server-sent-events/README.md) - Unidirectional server push
- [REST API](../rest-api/README.md) - Request-response pattern
- [gRPC](../grpc/README.md) - Bidirectional streaming
- [Webhooks](../webhook/README.md) - Event-driven HTTP callbacks