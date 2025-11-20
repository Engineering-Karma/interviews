# Server-Sent Events (SSE)

## Overview

Server-Sent Events (SSE) is a server push technology that enables a server to send real-time updates to clients over a single, long-lived HTTP connection. Unlike WebSocket, communication is unidirectional (server to client only).

## Key Characteristics

- **Unidirectional** - Server to client only.
- **HTTP-based** - Uses standard HTTP/HTTPS.
- **Text format** - UTF-8 encoded text data.
- **Automatic reconnection** - Built-in retry mechanism.
- **Event IDs** - Support for tracking and resuming.
- **Simple** - Easier to implement than WebSocket.
- **Efficient** - Single long-lived connection.

## Connection Flow

```
┌────────┐                                 ┌────────┐
│ Client │                                 │ Server │
└───┬────┘                                 └───┬────┘
    │  GET /events HTTP/1.1                    │
    │  Accept: text/event-stream               │
    │─────────────────────────────────────────▶│
    │  HTTP/1.1 200 OK                         │
    │  Content-Type: text/event-stream         │
    │  Cache-Control: no-cache                 │
    │◀─────────────────────────────────────────│
    │                                          │
    │═══════════ Connection Opened ════════════│
    │                                          │
    │  data: message 1                         │
    │◀─────────────────────────────────────────│
    │  data: message 2                         │
    │◀─────────────────────────────────────────│
    │  (connection lost)                       │
    │                                          │
    │  (automatic reconnection)                │
    │  GET /events?lastEventId=123             │
    │─────────────────────────────────────────▶│
    │                                          │
```

## Message Format

### Basic Message

```
data: Hello, World!

```

### Multi-line Message

```
data: {
data:   "user": "john",
data:   "message": "Hello"
data: }

```

### Complete Event Format

```
: Sample event message.
: Event messages are terminated with a blank line (\n\n), therefore the order of fields does not matter.
id: 123
event: userJoined
retry: 5000
data: {
data:   "userId": "456",
data:   "name": "John"
data: }

```

### Field Descriptions

- **`:`** — Comment line, ignored by clients. Commonly used for keep-alive pings to prevent proxy/firewall timeouts. Not counted toward the event structure.
- **`id`** — Optional event identifier for resuming after disconnection. The browser automatically stores and resends this as the `Last-Event-ID` header when reconnecting, allowing the server to replay missed events.
- **`event`** — Optional event type name (defaults to `"message"` if omitted). Allows clients to listen for specific event types via `addEventListener(eventType, ...)`.
- **`retry`** — Optional reconnection delay in milliseconds, applies to this specific event. If missing, the browser uses the default retry interval (typically 3000ms).
- **`data`** — Optional message payload. Multiple `data:` lines are concatenated with `\n` (newline) characters. Can be plain text or JSON.

## Client Implementation

### JavaScript (Browser)

```javascript
const eventSource = new EventSource('/events');

// Listen to all messages
eventSource.onmessage = (event) => {
  console.log('Message:', event.data);
};

// Listen to specific event types
eventSource.addEventListener('userJoined', (event) => {
  const data = JSON.parse(event.data);
  console.log('User joined:', data.name);
});

// Handle connection opened
eventSource.onopen = () => {
  console.log('Connection open');
};

// Handle errors
eventSource.onerror = (error) => {
  console.error('Error: ', error);
  if (eventSource.readyState === EventSource.CLOSED) {
    console.log('Connection closed');
  }
};

// Close connection manually
eventSource.close();
```

### With Authentication

```javascript
// SSE doesn't support custom headers
// Use query parameters or cookies
const eventSource = new EventSource('/events?token=abc123');
```

## Server Implementation

### Node.js (Express)

```javascript
app.get('/events', (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // Send initial event
  res.write('data: Connected\n\n');
  
  // Send events periodically
  const intervalId = setInterval(() => {
    const data = {
      time: new Date().toISOString(),
      value: Math.random()
    };
    
    res.write(`event: update\n`);
    res.write(`id: ${Date.now()}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }, 1000);
  
  // Keep-alive ping (every 30 seconds)
  const pingId = setInterval(() => {
    res.write(': ping\n\n');
  }, 30000);
  
  // Cleanup on connection close
  req.on('close', () => {
    clearInterval(intervalId);
    clearInterval(pingId);
    res.end();
  });
});
```

### Python (FastAPI)

```python
import asyncio
import json

from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get('/events')
async def events():
    async def generate():
        try:
            while True:
                data = {
                    'time': datetime.utcnow().isoformat(),
                    'value': 'update'
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            # Handle client disconnect
            print('Client disconnected')
            raise
    
    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Prevents proxy buffering
        }
    )
```

### Node.js with Redis Pub/Sub (Scaling)

```javascript
import Redis from 'ioredis';

const redis = new Redis();
const subscriber = new Redis();

// Track active connections
const connections = new Set();

app.get('/events', (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  connections.add(res);
  
  // Send initial event
  res.write('data: Connected\n\n');
  
  // Cleanup on connection close
  req.on('close', () => {
    connections.delete(res);
    res.end();
  });
});

// Subscribe to events from Redis
subscriber.subscribe('events', (err) => {
  if (err) console.error('Subscribe error:', err);
});

subscriber.on('message', (channel, message) => {
  // Broadcast to all connected clients
  connections.forEach((client) => {
    try {
      client.write(`data: ${message}\n\n`);
    } catch (err) {
      connections.delete(client);
    }
  });
});

// Example: Publish from another service
app.post('/publish', async (req, res) => {
  const event = { timestamp: Date.now(), data: req.body };
  await redis.publish('events', JSON.stringify(event));
  res.json({ success: true });
});
```

## Architecture Patterns

### Simple SSE Server

```
┌────────┐      SSE      ┌────────────┐
│ Client │◀──────────────│ SSE Server │
└────────┘               └─────┬──────┘
                               │
                               ▼
                         ┌─────────────┐
                         │ Data Source │
                         └─────────────┘
```

### Scalable SSE with Message Broker

```
┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│ Message Producer 1 │ │ Message Producer 2 │ │ Message Producer 3 │
└─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘                      
          │                      │                      │
          └──────────────────────┬──────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Message Broker      │
                    │ (Kafka, RabbitMQ, Redis) │
                    └────────────┬─────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
               ▼                 ▼                 ▼
       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ 
       │ SSE Server 1 │  │ SSE Server 2 │  │ SSE Server 3 │
       └───────┬──────┘  └───────┬──────┘  └───────┬──────┘
               │                 │                 │ 
               └─────────────────┼─────────────────┘
                                 │
                       ┌─────────┴──────────┐
                       │  Load Balancer     │
                       │ (sticky sessions)  │
                       └─────────┬──────────┘
                                 │ SSE
                  ┌──────────────┼──────────────┐
                  │              │              │
                  ▼              ▼              ▼
             ┌────────┐     ┌────────┐     ┌────────┐ 
             │ Client │     │ Client │     │ Client │
             └────────┘     └────────┘     └────────┘
```

## Resuming After Disconnection

### Client Side

```javascript
const eventSource = new EventSource('/events');

eventSource.onmessage = (event) => {
  // Browser automatically sends Last-Event-ID header
  console.log('Last ID:', event.lastEventId);
};
```

### Server Side

```javascript
app.get('/events', (req, res) => {
  const lastEventId = req.headers['last-event-id'];
  
  // Send missed events since lastEventId
  if (lastEventId) {
    const missedEvents = getEventsSince(lastEventId);
    missedEvents.forEach(event => {
      res.write(`id: ${event.id}\n`);
      res.write(`data: ${JSON.stringify(event.data)}\n\n`);
    });
  }
  
  // Continue with live events
  // ...
});
```

## Scaling Challenges

### 1. Sticky Connections

- Each client maintains connection to specific server.
- Load balancer must support long-lived connections.
- Use IP hash or session-based routing.

### 2. Event Distribution

- Use message broker (Redis Pub/Sub, Kafka, RabbitMQ).
- All servers subscribe to event channels.
- Broadcast to connected clients.

### 3. Connection State

- Track active connections per server.
- Store last event ID for resumption.
- Monitor connection count.

### 4. Resource Management

- Each connection holds server resources.
- Implement connection limits.
- Set timeouts for inactive connections.

## When to Use SSE

### ✅ Good For:

- Live feeds (news, social media).
- Real-time notifications.
- Stock tickers/live scores.
- Progress updates (uploads, processing).
- Server monitoring dashboards.
- Logging/event streams.
- One-way data flow from server.

### ❌ Less Ideal For:

- Bidirectional communication (use WebSocket).
- Binary data (text-only).
- Extremely high-frequency updates.
- When client needs to send data frequently.
- IE/old browsers (no support).

## System Design Considerations

### Scalability

- **Horizontal scaling** - Use message broker for coordination.
- **Sticky sessions** - Configure load balancer.
- **Connection limits** - Set per-server maximums.
- **Keep-alive** - Prevent proxy/firewall timeouts.

### Reliability
- **Automatic reconnection** - Built into browser.
- **Event IDs** - Enable event replay.
- **Retry field** - Control reconnection timing.
- **Heartbeat** - Send periodic comments.

### Performance
- **Compression** - Use gzip for text data.
- **Event batching** - Combine related events.
- **Connection throttling** - Limit connections per client.
- **Efficient encoding** - Minimize message size.

### Security
- **HTTPS** - Encrypt data in transit.
- **Authentication** - Token in URL or cookies.
- **CORS** - Configure properly.
- **Rate limiting** - Prevent abuse.
- **Input validation** - Sanitize event data.

## Comparison with Alternatives

| Feature | SSE | WebSocket | Long Polling |
|---------|-----|-----------|-------------|
| Direction | Server→Client | Bidirectional | Bidirectional |
| Protocol | HTTP | WebSocket | HTTP |
| Reconnection | Automatic | Manual | Manual |
| Event tracking | Yes (IDs) | No | No |
| Browser support | Good (not IE) | Excellent | Universal |
| Complexity | Low | Medium | Low |
| Overhead | Low | Very Low | High |
| Proxy-friendly | Yes | Moderate | Yes |

## Best Practices

- Always use HTTPS in production.
- Implement keep-alive pings (every 15-30 seconds).
- Set connection limits per server.
- Use event IDs for all events.
- Configure appropriate retry intervals.
- Monitor connection metrics.
- Handle reconnection gracefully.
- Compress data when possible.
- Set proper CORS headers.
- Implement rate limiting.
- Use message broker for scaling.
- Test with proxy servers.

## Limitations

- **Text only** - No native binary support.
- **Browser limit** - ~6 connections per domain.
- **No IE support** - Internet Explorer doesn't support SSE.
- **Unidirectional** - Server to client only.
- **Custom headers** - Cannot set custom request headers.

### Browser Connection Limit Details

Most browsers limit concurrent HTTP connections to approximately 6 per domain. This means:

- Each SSE connection counts against this limit.
- Multiple SSE streams to the same domain will quickly hit the limit.
- Additional connections will be queued and delayed until existing connections close.
- Solutions:
  - Use different subdomains for different SSE endpoints.
  - Multiplex events into a single connection (send all events through one SSE stream).
  - Use a CDN with a different domain to serve static assets (frees up connections for SSE).
  - Consider WebSocket for applications needing many simultaneous connections.

## Proxy Considerations

### Buffering Issues

Some proxies buffer responses.
Solution:
- Send initial data immediately.
- Periodic keep-alive comments.
- Configure proxy (X-Accel-Buffering: no).

### Timeout Issues

Proxies may close idle connections.
Solution:
- Send heartbeat every 15-30 seconds.
- Use comment lines as keep-alive.
- Configure appropriate timeouts.

## Trade-offs

| Aspect | Advantage | Disadvantage |
|--------|-----------|-------------|
| Simplicity | Easy to implement | Unidirectional only |
| Reconnection | Automatic with event replay | Not as flexible as WebSocket |
| Compatibility | Works over HTTP | No IE support |
| Infrastructure | Standard HTTP, proxy-friendly | Browser connection limits |
| Protocol | Lightweight | Text-only format |

## Common Interview Questions

1. **When would you use SSE over WebSocket?**
   - Unidirectional data flow (server to client).
   - Simpler implementation.
   - Need automatic reconnection.
   - HTTP infrastructure/caching benefits.

2. **How do you scale SSE servers?**
   - Use message broker (Redis Pub/Sub).
   - Sticky sessions on load balancer.
   - Track connections per server.
   - Implement connection limits.

3. **How does reconnection work?**
   - Browser automatically reconnects.
   - Sends Last-Event-ID header.
   - Server replays missed events.
   - Configurable retry interval.

4. **SSE vs Long Polling?**
   - SSE: Single connection, lower overhead.
   - Long Polling: More overhead, better compatibility.
   - SSE: Built-in reconnection.
   - Long Polling: Manual reconnection logic.

5. **How do you authenticate SSE connections?**
   - Cannot set custom headers.
   - Use query parameters.
   - Use cookies (set via API call first).
   - Validate on initial connection.

## Related Patterns

- [WebSocket](../websocket/README.md) - Bidirectional real-time.
- [REST API](../rest-api/README.md) - Request-response pattern.
- [Webhooks](../webhook/README.md) - Event-driven callbacks.
- [Long Polling](https://en.wikipedia.org/wiki/Push_technology#Long_polling) - Alternative push method.

## References & Further Reading

### Specifications

- [Server-Sent Events (W3C)](https://html.spec.whatwg.org/multipage/server-sent-events.html) - Official SSE specification.
- [EventSource API (W3C)](https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface) - Browser API standard.
- [MIME Type text/event-stream](https://www.iana.org/assignments/media-types/text/event-stream) - SSE content type.

### Official Documentation

- [MDN Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) - Comprehensive browser guide.
- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) - API reference.
- [Using Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) - MDN tutorial.

### Implementation Guides

- [Node.js SSE Guide](https://nodejs.org/en/learn/modules/anatomy-of-an-http-transaction) - Building SSE in Node.js.
- [Express SSE Middleware](https://www.npmjs.com/package/express-sse) - Express integration.
- [FastAPI SSE](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse) - Python/FastAPI implementation.
- [Spring WebFlux SSE](https://docs.spring.io/spring-framework/reference/web/webflux/reactive-spring.html#webflux-sse) - Java implementation.

### Articles & Tutorials

- [Stream Updates with Server-Sent Events](https://web.dev/eventsource-basics/) - Web.dev guide.
- [Server-Sent Events: The Alternative to WebSocket](https://germano.dev/sse-websockets/) - Comparison and use cases.
- [Real-Time Communication with SSE](https://www.smashingmagazine.com/2018/02/sse-websockets-data-flow-http2/) - Smashing Magazine.
- [Building Real-Time Apps with SSE](https://www.youtube.com/watch?v=4HlNv1qpZFY) - Video tutorial.

### Architecture & Scaling

- [Scaling Server-Sent Events](https://ably.com/topic/server-sent-events) - Ably's SSE guide.
- [Redis Pub/Sub with SSE](https://redis.io/docs/interact/pubsub/) - Using Redis for SSE scaling.
- [Load Balancing SSE](https://www.haproxy.com/blog/websockets-load-balancing-with-haproxy) - HAProxy SSE configuration.
- [NGINX SSE Configuration](https://www.nginx.com/blog/nginx-nodejs-websockets-socketio/) - Proxy setup.

### Comparison Articles

- [SSE vs WebSocket vs Polling](https://ably.com/blog/websockets-vs-long-polling) - Detailed comparison.
- [When to Use Server-Sent Events](https://germano.dev/sse-websockets/) - Decision guide.
- [Real-Time Technologies Compared](https://rxdb.info/articles/websockets-sse-polling-webrtc-webtransport.html) - Comprehensive comparison.

### Browser Compatibility

- [Can I Use: Server-Sent Events](https://caniuse.com/eventsource) - Browser support matrix.
- [EventSource Polyfill](https://github.com/Yaffle/EventSource) - Polyfill for older browsers.

### Real-World Examples

- [Mercure Hub](https://mercure.rocks/) - SSE-based pub/sub system.
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging) - Uses SSE for web push.
- [OpenAI Streaming](https://platform.openai.com/docs/api-reference/streaming) - ChatGPT streaming with SSE.

### Libraries & Tools

- [express-sse](https://www.npmjs.com/package/express-sse) - Node.js/Express SSE.
- [sse-channel](https://github.com/rexxars/sse-channel) - SSE server implementation.
- [EventSource (npm)](https://www.npmjs.com/package/eventsource) - Node.js EventSource client.
- [Server-Sent Events Client (Go)](https://github.com/r3labs/sse) - Go SSE client.

### Testing & Debugging

- [SSE Test Server](https://sse.dev/) - Online SSE testing tool.
- [Chrome DevTools Network](https://developer.chrome.com/docs/devtools/network/) - Debugging SSE connections.
- [curl for SSE](https://curl.se/) - Testing SSE endpoints with curl.

### Standards & Protocols

- [HTTP/1.1 Chunked Transfer Encoding](https://tools.ietf.org/html/rfc7230#section-4.1) - Underlying mechanism.
- [CORS for SSE](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) - Cross-origin SSE.
