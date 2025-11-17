# Webhooks

## Overview

Webhooks are user-defined HTTP callbacks that are triggered by specific events. When an event occurs, the source system makes an HTTP request to the URL configured for the webhook, allowing real-time notifications and integrations between systems.

## Key Characteristics

- **Event-driven**: Triggered by specific events
- **Push-based**: Server pushes data to client
- **HTTP POST**: Typically use POST requests
- **Asynchronous**: Fire-and-forget or acknowledgment-based
- **Reverse API**: Client provides endpoint, server calls it
- **Decoupled**: Loose coupling between systems

## Webhook Flow

```
┌───────────────────┐
│  Source System   │
│  (e.g., GitHub)  │
└────────┬─────────┘
         │
         │ 1. Event occurs
         │    (e.g., push to repo)
         ▼
┌───────────────────┐
│  Webhook Queue   │
└────────┬─────────┘
         │
         │ 2. HTTP POST
         ▼
┌───────────────────┐
│ Client Endpoint │
│ (your server)   │
└────────┬─────────┘
         │
         │ 3. Process event
         ▼
┌───────────────────┐
│ Return 200 OK   │
└────────┬─────────┘
         │
         │ 4. Acknowledge
         ▼
┌───────────────────┐
│  Mark Success   │
└───────────────────┘
```

## Webhook Request Example

### GitHub Push Event
```http
POST /webhook/github HTTP/1.1
Host: your-app.com
Content-Type: application/json
X-GitHub-Event: push
X-GitHub-Delivery: 12345
X-Hub-Signature-256: sha256=abc123...

{
  "ref": "refs/heads/main",
  "before": "abc123...",
  "after": "def456...",
  "repository": {
    "id": 123,
    "name": "my-repo",
    "url": "https://github.com/user/my-repo"
  },
  "pusher": {
    "name": "john",
    "email": "john@example.com"
  },
  "commits": [
    {
      "id": "def456...",
      "message": "Fix bug",
      "author": {...}
    }
  ]
}
```

### Stripe Payment Event
```http
POST /webhook/stripe HTTP/1.1
Host: your-app.com
Content-Type: application/json
Stripe-Signature: t=123,v1=abc...

{
  "id": "evt_123",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_123",
      "amount": 1000,
      "currency": "usd",
      "status": "succeeded"
    }
  }
}
```

## Webhook Receiver Implementation

### Node.js (Express)
```javascript
const express = require('express');
const crypto = require('crypto');

app.post('/webhook/github', express.json(), async (req, res) => {
  try {
    // 1. Verify signature
    const signature = req.headers['x-hub-signature-256'];
    const isValid = verifySignature(req.body, signature);
    
    if (!isValid) {
      return res.status(401).send('Invalid signature');
    }
    
    // 2. Check event type
    const eventType = req.headers['x-github-event'];
    
    // 3. Process idempotently (check if already processed)
    const deliveryId = req.headers['x-github-delivery'];
    if (await isProcessed(deliveryId)) {
      return res.status(200).send('Already processed');
    }
    
    // 4. Acknowledge immediately (return 200)
    res.status(200).send('Received');
    
    // 5. Process asynchronously
    processWebhookAsync(eventType, req.body, deliveryId)
      .catch(err => console.error('Webhook processing failed:', err));
    
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).send('Internal error');
  }
});

function verifySignature(payload, signature) {
  const secret = process.env.GITHUB_WEBHOOK_SECRET;
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(JSON.stringify(payload)).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
}
```

### Python (Flask)
```python
import hmac
import hashlib
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    # 1. Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return 'Invalid signature', 401
    
    # 2. Get event type
    event_type = request.headers.get('X-GitHub-Event')
    delivery_id = request.headers.get('X-GitHub-Delivery')
    
    # 3. Check idempotency
    if is_processed(delivery_id):
        return 'Already processed', 200
    
    # 4. Acknowledge immediately
    payload = request.json
    
    # 5. Queue for async processing
    queue_webhook_processing(event_type, payload, delivery_id)
    
    return 'Received', 200

def verify_signature(payload, signature):
    secret = os.environ['GITHUB_WEBHOOK_SECRET']
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    expected = 'sha256=' + mac.hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Webhook Sender Implementation

### Basic Webhook Delivery
```javascript
class WebhookService {
  async deliverWebhook(url, event, payload, secret) {
    const signature = this.generateSignature(payload, secret);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Event-Type': event,
          'X-Signature': signature,
          'User-Agent': 'MyApp-Webhooks/1.0'
        },
        body: JSON.stringify(payload),
        timeout: 30000 // 30 second timeout
      });
      
      if (response.status >= 200 && response.status < 300) {
        return { success: true };
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  
  generateSignature(payload, secret) {
    const hmac = crypto.createHmac('sha256', secret);
    return hmac.update(JSON.stringify(payload)).digest('hex');
  }
}
```

### With Retry Logic
```javascript
class WebhookDelivery {
  async deliver(webhook) {
    const maxRetries = 5;
    const backoffMs = [1000, 5000, 30000, 120000, 600000]; // Exponential backoff
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const result = await this.send(webhook);
        
        if (result.success) {
          await this.markSuccess(webhook.id);
          return;
        }
        
        // Retry on 5xx errors
        if (result.statusCode >= 500 && attempt < maxRetries - 1) {
          await this.sleep(backoffMs[attempt]);
          continue;
        }
        
        // Don't retry on 4xx errors
        if (result.statusCode >= 400 && result.statusCode < 500) {
          await this.markFailed(webhook.id, result.error);
          return;
        }
        
      } catch (error) {
        if (attempt === maxRetries - 1) {
          await this.markFailed(webhook.id, error.message);
        } else {
          await this.sleep(backoffMs[attempt]);
        }
      }
    }
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Architecture Patterns

### Simple Webhook System
```
┌─────────────┐
│ Application │
└──────┬──────┘
       │
       │ Event occurs
       ▼
┌─────────────┐
│ Webhook    │
│ Sender     │
└──────┬──────┘
       │
       │ HTTP POST
       ▼
┌─────────────┐
│ Customer   │
│ Endpoint   │
└─────────────┘
```

### Scalable Webhook System
```
┌──────────────┐
│  Application  │
└──────┬───────┘
       │
       │ Publish event
       ▼
┌──────────────┐      ┌────────────────┐
│ Event Queue  │─────▶│  Webhook DB   │
│ (Kafka/SQS) │      │  (subscribers)│
└──────┬───────┘      └────────────────┘
       │
       │ Consume
       ▼
┌──────────────┐
│ Webhook     │
│ Worker Pool │
└──────┬───────┘
       │
       │ HTTP POST (with retries)
       ▼
┌──────────────┐
│  Customer    │
│  Endpoints   │
└──────────────┘
       │
       │ Status updates
       ▼
┌──────────────┐
│ Delivery Log│
└──────────────┘
```

## Security Best Practices

### 1. Signature Verification
```javascript
// Always verify HMAC signature
function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}
```

### 2. Timestamp Validation
```javascript
// Reject old webhooks to prevent replay attacks
function isTimestampValid(timestamp, maxAgeSeconds = 300) {
  const now = Math.floor(Date.now() / 1000);
  return Math.abs(now - timestamp) < maxAgeSeconds;
}
```

### 3. IP Allowlisting
```javascript
// Restrict to known source IPs
const ALLOWED_IPS = ['192.0.2.1', '198.51.100.0/24'];

function isIPAllowed(ip) {
  return ALLOWED_IPS.some(allowed => ipInRange(ip, allowed));
}
```

## When to Use Webhooks

### ✅ Good For:
- Event notifications (payments, orders, deploys)
- System integrations (CI/CD, monitoring)
- Real-time updates to external systems
- Triggering workflows
- Reducing polling overhead
- Loosely coupled architectures

### ❌ Less Ideal For:
- High-frequency events (use streams)
- When immediate consistency is required
- Sensitive data without encryption
- Untrusted receivers
- Bidirectional communication (use API)

## System Design Considerations

### Reliability
- **Retry mechanism**: Exponential backoff
- **Idempotency**: Include unique delivery ID
- **Timeouts**: Set reasonable request timeouts
- **Dead letter queue**: Store failed deliveries
- **Circuit breaker**: Stop delivery to failing endpoints

### Scalability
- **Queue-based**: Async processing with workers
- **Horizontal scaling**: Multiple workers
- **Rate limiting**: Per-endpoint limits
- **Batching**: Group related events (optional)
- **Fanout**: Deliver to multiple subscribers

### Security
- **HTTPS only**: Encrypt data in transit
- **Signature verification**: HMAC validation
- **Timestamp check**: Prevent replay attacks
- **IP allowlisting**: Restrict sources
- **Secrets rotation**: Periodic key updates
- **Payload validation**: Sanitize inputs

### Observability
- **Delivery logs**: Track all attempts
- **Success/failure metrics**: Monitor rates
- **Latency tracking**: Response times
- **Alerting**: Failed deliveries
- **Webhook dashboard**: User-facing status

## Common Patterns

### Registration
```javascript
// User registers webhook
POST /api/webhooks
{
  "url": "https://customer.com/webhook",
  "events": ["payment.success", "order.created"],
  "secret": "user-generated-secret"
}
```

### Verification
```javascript
// Challenge-response verification
GET /webhook/verify?challenge=abc123
Response: abc123
```

### Deduplication
```javascript
// Use delivery ID to prevent duplicate processing
const deliveryId = req.headers['x-delivery-id'];
if (await redis.get(`webhook:${deliveryId}`)) {
  return res.status(200).send('Already processed');
}
await redis.setex(`webhook:${deliveryId}`, 86400, '1');
```

## Common Interview Questions

1. **How do you ensure webhook delivery reliability?**
   - Retry with exponential backoff
   - Queue-based async processing
   - Dead letter queue for failures
   - Idempotency keys
   - Circuit breakers

2. **How do you secure webhooks?**
   - HMAC signature verification
   - Timestamp validation (prevent replay)
   - HTTPS only
   - IP allowlisting
   - Secrets management

3. **How do you handle webhook failures?**
   - Automatic retries (5-10 attempts)
   - Exponential backoff
   - Alert on repeated failures
   - Disable endpoint after threshold
   - Provide replay mechanism

4. **Webhooks vs Polling?**
   - Webhooks: Real-time, efficient, push-based
   - Polling: Simpler, more reliable, pull-based
   - Webhooks: Lower latency and bandwidth
   - Polling: No endpoint management needed

5. **How do you scale webhook delivery?**
   - Queue-based architecture
   - Worker pool for parallel delivery
   - Rate limiting per endpoint
   - Separate workers by priority
   - Monitor and auto-scale workers

## Best Practices

- Always use HTTPS for webhook URLs
- Implement signature verification
- Respond with 200 OK immediately
- Process webhooks asynchronously
- Implement idempotency
- Set reasonable timeouts (5-30 seconds)
- Retry with exponential backoff
- Log all delivery attempts
- Provide webhook testing tools
- Document payload schemas
- Version your webhook payloads
- Allow users to replay missed events
- Implement circuit breakers
- Monitor delivery success rates

## Trade-offs

| Aspect | Advantage | Disadvantage |
|--------|-----------|-------------|
| Real-time | Immediate notifications | Requires endpoint management |
| Efficiency | No polling overhead | Delivery failures possible |
| Simplicity | Standard HTTP | More complex than polling |
| Scalability | Async, queue-based | Requires retry logic |
| Coupling | Loose coupling | Network dependencies |

## Debugging Webhooks

### Testing Tools
- **webhook.site**: Inspect webhook payloads
- **ngrok**: Expose local server for testing
- **Postman**: Simulate webhook delivery
- **RequestBin**: Capture and inspect requests

### Common Issues
- Incorrect signature verification
- Firewall blocking requests
- Slow response times (timeouts)
- Missing idempotency handling
- Not handling retries

## Related Patterns

- [REST API](../rest-api/README.md) - Request-response pattern
- [Server-Sent Events](../server-sent-events/README.md) - Server push
- [WebSocket](../websocket/README.md) - Bidirectional real-time
- [Message Queue](https://en.wikipedia.org/wiki/Message_queue) - Async messaging