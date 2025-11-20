# Server-Sent Events (SSE) - Python Implementation

This is a Python/FastAPI implementation of Server-Sent Events, demonstrating real-time server-to-client streaming.

## Features

- **Unidirectional Streaming** - Server-to-client real-time data streaming.
- **Multiple Event Types** - Support for different event types (connected, update, notification, price_update).
- **Event Replay** - Automatic reconnection with Last-Event-ID header support.
- **Event History** - Stores last 100 events for replay on reconnection.
- **Keep-Alive Heartbeat** - Periodic heartbeat comments to maintain connection.
- **Multiple Endpoints**
  - `/events` - Main event stream with replay support.
  - `/notifications/{userId}` - User-specific notifications.
  - `/stocks` - Real-time stock price updates.
  - `/health` - Health check endpoint.

## Installation

Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Start the server.

```bash
python server.py
```

Or using uvicorn directly.

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Testing

Open your browser to `http://localhost:8000` to access the test client.

## Endpoints

### SSE Endpoints

- `GET /events` - Main event stream with automatic reconnection support.
- `GET /notifications/{user_id}` - User-specific notification stream.
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

