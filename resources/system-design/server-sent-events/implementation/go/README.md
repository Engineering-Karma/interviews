# Server-Sent Events (SSE) - Go Implementation

This is a Go implementation of Server-Sent Events, demonstrating real-time server-to-client streaming using the standard library's `net/http` package.

## Features

- **Unidirectional Streaming** - Server-to-client real-time data streaming.
- **Multiple Event Types** - Support for different event types (connected, update, notification, price_update).
- **Event Replay** - Automatic reconnection with Last-Event-ID header support.
- **Event History** - Stores last 100 events for replay on reconnection.
- **Keep-Alive Heartbeat** - Periodic heartbeat comments to maintain connection.
- **Thread-Safe** - Mutex-protected access to shared state.
- **Multiple Endpoints**
  - `/events` - Main event stream with replay support.
  - `/notifications` - User-specific notifications (with `user_id` query parameter).
  - `/stocks` - Real-time stock price updates.
  - `/health` - Health check endpoint.

## Installation

Ensure you have Go 1.16 or later installed.

```bash
go mod init sse
```

## Usage

Start the server.

```bash
go run server.go
```

Or build and run the binary.

```bash
go build -o sse server.go
./sse
```

## Testing

Open your browser to `http://localhost:8000` to access the test client.

## Endpoints

### SSE Endpoints

- `GET /events` - Main event stream with automatic reconnection support.
- `GET /notifications?user_id=user123` - User-specific notification stream.
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
