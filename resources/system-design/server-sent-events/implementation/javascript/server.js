/**
 * Server-Sent Events (SSE) Implementation with Express.
 *
 * Demonstrates:
 * - Unidirectional server-to-client streaming.
 * - Event streams with proper format.
 * - Multiple event types.
 * - Automatic reconnection with Last-Event-ID.
 * - Keep-alive heartbeat.
 *
 * Note:
 * This implementation serves to illustrate SSE concepts and is not production ready.
 */
const express = require('express');
const path = require('path');

const app = express();
const PORT = 8000;

// Event storage for replay
const MAX_HISTORY_SIZE = 100;
const eventHistory = [];
let eventIdCounter = 0;

/**
 * Generate Server-Sent Events.
 * 
 * SSE format:
 * id: event_id\n
 * event: event_type\n
 * data: event_data\n\n
 */
async function* eventGenerator(lastEventId = null) {
    // Send connection established event
    eventIdCounter++;
    yield `id: ${eventIdCounter}\n`;
    yield `event: connected\n`;
    yield `data: ${JSON.stringify({ message: 'Connected to SSE stream.' })}\n\n`;
    
    // Replay missed events if Last-Event-ID provided
    if (lastEventId) {
        try {
            const lastId = parseInt(lastEventId, 10);
            const missedEvents = eventHistory.filter(e => e.id > lastId);
            
            for (const event of missedEvents) {
                yield `id: ${event.id}\n`;
                yield `event: ${event.type}\n`;
                yield `data: ${JSON.stringify(event.data)}\n\n`;
            }
        } catch (error) {
            // Invalid Last-Event-ID, skip replay
        }
    }
    
    // Continuous event stream
    while (true) {
        // Wait before sending next event
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Generate update event
        eventIdCounter++;
        const eventData = {
            timestamp: new Date().toISOString(),
            value: Math.floor(Math.random() * 100) + 1,
            message: `Update #${eventIdCounter}.`
        };
        
        // Store in history
        eventHistory.push({
            id: eventIdCounter,
            type: 'update',
            data: eventData
        });
        
        // Keep only last N events
        if (eventHistory.length > MAX_HISTORY_SIZE) {
            eventHistory.shift();
        }
        
        // Send update event
        yield `id: ${eventIdCounter}\n`;
        yield `event: update\n`;
        yield `data: ${JSON.stringify(eventData)}\n\n`;
        
        // Periodic heartbeat (every 30 seconds)
        if (eventIdCounter % 15 === 0) {
            yield `: heartbeat\n\n`;
        }
    }
}

/**
 * Generate user-specific notifications.
 */
async function* notificationGenerator(userId) {
    // Send connection established event
    eventIdCounter++;
    yield `id: ${eventIdCounter}\n`;
    yield `event: connected\n`;
    yield `data: ${JSON.stringify({ user_id: userId, message: 'Connected.' })}\n\n`;
    
    const notificationTypes = ['message', 'alert', 'info'];
    
    while (true) {
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Send notification event
        eventIdCounter++;
        const notification = {
            user_id: userId,
            type: notificationTypes[Math.floor(Math.random() * notificationTypes.length)],
            content: `Notification at ${new Date().toISOString()}.`,
            timestamp: new Date().toISOString()
        };
        
        yield `id: ${eventIdCounter}\n`;
        yield `event: notification\n`;
        yield `data: ${JSON.stringify(notification)}\n\n`;
    }
}

/**
 * Simulate stock price updates.
 */
async function* stockTickerGenerator() {
    // Send connection established event
    eventIdCounter++;
    yield `id: ${eventIdCounter}\n`;
    yield `event: connected\n`;
    yield `data: ${JSON.stringify({ message: 'Connected to SSE stream.' })}\n\n`;
    
    const stocks = {
        'AAPL': 150.00,
        'GOOGL': 2800.00,
        'MSFT': 300.00
    };
    
    while (true) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Random price change
        const symbols = Object.keys(stocks);
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];
        const change = (Math.random() * 10) - 5;
        stocks[symbol] += change;
       
        // Send price_update event 
        eventIdCounter++;
        const data = {
            symbol,
            price: Math.round(stocks[symbol] * 100) / 100,
            change: Math.round(change * 100) / 100,
            timestamp: new Date().toISOString()
        };
        
        yield `id: ${eventIdCounter}\n`;
        yield `event: price_update\n`;
        yield `data: ${JSON.stringify(data)}\n\n`;
    }
}

/**
 * Helper to stream async generator to response.
 */
async function streamGenerator(generator, res) {
    try {
        for await (const chunk of generator) {
            res.write(chunk);
        }
    } catch (error) {
        // Client disconnected
        console.log('Client disconnected');
    } finally {
        res.end();
    }
}

// ============= SSE Endpoints =============

/**
 * Main SSE endpoint with event replay support.
 * Supports Last-Event-ID header for automatic reconnection.
 */
app.get('/events', (req, res) => {
    const lastEventId = req.headers['last-event-id'];
    
    // Set SSE headers
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no' // Disable buffering in nginx
    });
    
    streamGenerator(eventGenerator(lastEventId), res);
    
    // Handle client disconnect
    req.on('close', () => {
        console.log('Client closed connection');
    });
});

/**
 * User-specific notification stream.
 */
app.get('/notifications/:userId', (req, res) => {
    const { userId } = req.params;
    
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    
    streamGenerator(notificationGenerator(userId), res);
    
    req.on('close', () => {
        console.log(`Client disconnected from notifications/${userId}`);
    });
});

/**
 * Real-time stock price updates.
 */
app.get('/stocks', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    
    streamGenerator(stockTickerGenerator(), res);
    
    req.on('close', () => {
        console.log('Client disconnected from stocks');
    });
});

// ============= HTTP Endpoints =============

/**
 * Serve test client.
 */
app.get('/', (req, res) => {
    const html = `
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
                    addEvent('Update', \`Value: \${data.value}\`, 'blue');
                });
                
                eventSource.addEventListener('notification', (e) => {
                    const data = JSON.parse(e.data);
                    addEvent('Notification', data.content, 'orange');
                });
                
                eventSource.addEventListener('price_update', (e) => {
                    const data = JSON.parse(e.data);
                    addEvent('Stock', \`\${data.symbol}: $\${data.price}\`, 'purple');
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
                div.style.borderLeft = \`4px solid \${color}\`;
                div.innerHTML = \`<strong>[\${type}]</strong> \${message} <small>(\${new Date().toLocaleTimeString()})</small>\`;
                events.insertBefore(div, events.firstChild);
                
                // Keep only last 50 events
                while (events.children.length > 50) {
                    events.removeChild(events.lastChild);
                }
            }
        </script>
    </body>
    </html>
    `;
    res.send(html);
});

/**
 * Health check endpoint.
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        active_events: eventHistory.length,
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log('SSE server starting...');
    console.log(`Test client: http://localhost:${PORT}`);
});
