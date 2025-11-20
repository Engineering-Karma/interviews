# Server-Sent Events (SSE) - JavaScript Implementation

This is a Node.js/Express implementation of Server-Sent Events, demonstrating real-time server-to-client streaming.

## Features

- **Unidirectional Streaming** - Server-to-client real-time data streaming.
- **Multiple Event Types** - Support for different event types (connected, update, notification, price_update).
- **Event Replay** - Automatic reconnection with Last-Event-ID header support.
- **Event History** - Stores last 100 events for replay on reconnection.
- **Keep-Alive Heartbeat** - Periodic heartbeat comments to maintain connection.
- **Multiple Endpoints** - .
  - `/events` - Main event stream with replay support.
  - `/notifications/{userId}` - User-specific notifications.
  - `/stocks` - Real-time stock price updates.
  - `/health` - Health check endpoint.

## Installation

```bash
npm install
```

## Usage

Start the server.

```bash
npm start
```

For development with auto-reload.

```bash
npm run dev
```

## Testing

Open your browser to `http://localhost:8000` to access the test client.

## Endpoints

### SSE Endpoints

- `GET /events` - Main event stream with automatic reconnection support.
- `GET /notifications/:userId` - User-specific notification stream.
- `GET /stocks` - Real-time stock ticker.

### HTTP Endpoints

- `GET /` - Test client web interface.
- `GET /health` - Health check.

## SSE Format

Events follow the standard SSE format.

```
id: event_id
event: event_type
data: {"json": "data"}

```

