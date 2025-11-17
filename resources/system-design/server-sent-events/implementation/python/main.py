"""
Server-Sent Events (SSE) Implementation with FastAPI

Demonstrates:
- Unidirectional server-to-client streaming
- Event streams with proper format
- Multiple event types
- Automatic reconnection with Last-Event-ID
- Keep-alive heartbeat
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import AsyncGenerator
import asyncio
import json
from datetime import datetime
import random

app = FastAPI(title="Server-Sent Events Example")

# Event storage for replay
event_history = []
event_id_counter = 0


async def event_generator(last_event_id: str = None) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events
    
    SSE format:
    event: event_type\n
    id: event_id\n
    data: event_data\n\n
    """
    global event_id_counter
    
    # Replay missed events if Last-Event-ID provided
    if last_event_id:
        try:
            last_id = int(last_event_id)
            missed_events = [e for e in event_history if e['id'] > last_id]
            
            for event in missed_events:
                yield f"id: {event['id']}\n"
                yield f"event: {event['type']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"
        except (ValueError, KeyError):
            pass
    
    # Send connection established event
    event_id_counter += 1
    yield f"id: {event_id_counter}\n"
    yield f"event: connected\n"
    yield f"data: {json.dumps({'message': 'Connected to SSE stream'})}\n\n"
    
    # Continuous event stream
    while True:
        try:
            # Wait before sending next event
            await asyncio.sleep(2)
            
            # Generate update event
            event_id_counter += 1
            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'value': random.randint(1, 100),
                'message': f'Update #{event_id_counter}'
            }
            
            # Store in history
            event_history.append({
                'id': event_id_counter,
                'type': 'update',
                'data': event_data
            })
            
            # Keep only last 100 events
            if len(event_history) > 100:
                event_history.pop(0)
            
            # Send event
            yield f"id: {event_id_counter}\n"
            yield f"event: update\n"
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Periodic heartbeat (every 30 seconds)
            if event_id_counter % 15 == 0:
                yield f": heartbeat\n\n"
        
        except asyncio.CancelledError:
            # Client disconnected
            break


async def notification_generator(user_id: str) -> AsyncGenerator[str, None]:
    """Generate user-specific notifications"""
    
    # Send welcome
    yield f"event: connected\n"
    yield f"data: {json.dumps({'user_id': user_id, 'message': 'Connected'})}\n\n"
    
    notification_types = ['message', 'alert', 'info']
    
    while True:
        try:
            await asyncio.sleep(5)
            
            notification = {
                'user_id': user_id,
                'type': random.choice(notification_types),
                'content': f'Notification at {datetime.utcnow().isoformat()}',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            yield f"event: notification\n"
            yield f"data: {json.dumps(notification)}\n\n"
        
        except asyncio.CancelledError:
            break


async def stock_ticker_generator() -> AsyncGenerator[str, None]:
    """Simulate stock price updates"""
    
    stocks = {
        'AAPL': 150.00,
        'GOOGL': 2800.00,
        'MSFT': 300.00
    }
    
    while True:
        try:
            await asyncio.sleep(1)
            
            # Random price change
            symbol = random.choice(list(stocks.keys()))
            change = random.uniform(-5, 5)
            stocks[symbol] += change
            
            data = {
                'symbol': symbol,
                'price': round(stocks[symbol], 2),
                'change': round(change, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            yield f"event: price_update\n"
            yield f"data: {json.dumps(data)}\n\n"
        
        except asyncio.CancelledError:
            break


# ============= SSE Endpoints =============

@app.get("/events")
async def sse_endpoint(request: Request):
    """
    Main SSE endpoint with event replay support
    
    Supports Last-Event-ID header for automatic reconnection
    """
    last_event_id = request.headers.get('Last-Event-ID')
    
    return StreamingResponse(
        event_generator(last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@app.get("/notifications/{user_id}")
async def user_notifications(user_id: str):
    """User-specific notification stream"""
    return StreamingResponse(
        notification_generator(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@app.get("/stocks")
async def stock_ticker():
    """Real-time stock price updates"""
    return StreamingResponse(
        stock_ticker_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# ============= HTTP Endpoints =============

@app.get("/")
async def get_index():
    """Serve test client"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server-Sent Events Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .controls { margin: 20px 0; }
            button { margin-right: 10px; }
            #events { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
            .event { margin: 5px 0; padding: 5px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>Server-Sent Events Test Client</h1>
        
        <div class="controls">
            <button onclick="connectEvents()">Connect to Events</button>
            <button onclick="connectNotifications()">Connect to Notifications</button>
            <button onclick="connectStocks()">Connect to Stocks</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div>
            <h3>Event Stream:</h3>
            <div id="events"></div>
        </div>
        
        <script>
            let eventSource = null;
            
            function connectEvents() {
                disconnect();
                eventSource = new EventSource('/events');
                setupEventSource();
            }
            
            function connectNotifications() {
                disconnect();
                eventSource = new EventSource('/notifications/user123');
                setupEventSource();
            }
            
            function connectStocks() {
                disconnect();
                eventSource = new EventSource('/stocks');
                setupEventSource();
            }
            
            function setupEventSource() {
                eventSource.onopen = () => {
                    addEvent('Connection', 'Connected', 'green');
                };
                
                eventSource.onerror = () => {
                    addEvent('Error', 'Connection error', 'red');
                };
                
                // Listen to all event types
                eventSource.addEventListener('connected', (e) => {
                    addEvent('Connected', e.data, 'green');
                });
                
                eventSource.addEventListener('update', (e) => {
                    const data = JSON.parse(e.data);
                    addEvent('Update', `Value: ${data.value}`, 'blue');
                });
                
                eventSource.addEventListener('notification', (e) => {
                    const data = JSON.parse(e.data);
                    addEvent('Notification', data.content, 'orange');
                });
                
                eventSource.addEventListener('price_update', (e) => {
                    const data = JSON.parse(e.data);
                    addEvent('Stock', `${data.symbol}: $${data.price}`, 'purple');
                });
            }
            
            function disconnect() {
                if (eventSource) {
                    eventSource.close();
                    addEvent('Connection', 'Disconnected', 'gray');
                    eventSource = null;
                }
            }
            
            function addEvent(type, message, color) {
                const events = document.getElementById('events');
                const div = document.createElement('div');
                div.className = 'event';
                div.style.borderLeft = `4px solid ${color}`;
                div.innerHTML = `<strong>[${type}]</strong> ${message} <small>(${new Date().toLocaleTimeString()})</small>`;
                events.insertBefore(div, events.firstChild);
                
                // Keep only last 50 events
                while (events.children.length > 50) {
                    events.removeChild(events.lastChild);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_events": len(event_history),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("SSE server starting...")
    print("Test client: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
