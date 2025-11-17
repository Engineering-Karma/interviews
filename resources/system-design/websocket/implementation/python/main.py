"""
WebSocket Implementation with FastAPI

Demonstrates:
- Bidirectional real-time communication
- Connection management
- Broadcasting to multiple clients
- Room/channel subscriptions
- Heartbeat/ping-pong
- Error handling
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, Set
from datetime import datetime
import asyncio
import json
import uuid

app = FastAPI(title="WebSocket Example")

# Connection manager
class ConnectionManager:
    def __init__(self):
        # All active connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Rooms/channels subscriptions
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept and register a new connection"""
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove a connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all rooms
        for room in self.rooms.values():
            room.discard(client_id)
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict, exclude: str = None):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for client_id, connection in self.active_connections.items():
            if client_id == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def broadcast_to_room(self, room: str, message: dict, exclude: str = None):
        """Broadcast message to all clients in a room"""
        if room not in self.rooms:
            return
        
        disconnected = []
        
        for client_id in self.rooms[room]:
            if client_id == exclude:
                continue
            
            if client_id not in self.active_connections:
                disconnected.append(client_id)
                continue
            
            try:
                await self.active_connections[client_id].send_json(message)
            except:
                disconnected.append(client_id)
        
        # Clean up
        for client_id in disconnected:
            self.rooms[room].discard(client_id)
    
    def join_room(self, client_id: str, room: str):
        """Add client to a room"""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(client_id)
    
    def leave_room(self, client_id: str, room: str):
        """Remove client from a room"""
        if room in self.rooms:
            self.rooms[room].discard(client_id)
    
    def get_room_count(self, room: str) -> int:
        """Get number of clients in a room"""
        return len(self.rooms.get(room, set()))


manager = ConnectionManager()


# ============= WebSocket Endpoints =============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint
    
    Message format:
    {
        "type": "message" | "subscribe" | "unsubscribe" | "ping",
        "room": "room_name" (optional),
        "data": {...}
    }
    """
    client_id = await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)
        
        # Broadcast join notification
        await manager.broadcast({
            "type": "user_joined",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=client_id)
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket, client_id))
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "message")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
                
                elif message_type == "subscribe":
                    # Join room
                    room = message.get("room")
                    if room:
                        manager.join_room(client_id, room)
                        await manager.send_personal_message({
                            "type": "subscribed",
                            "room": room,
                            "count": manager.get_room_count(room)
                        }, client_id)
                        
                        # Notify room
                        await manager.broadcast_to_room(room, {
                            "type": "user_joined_room",
                            "client_id": client_id,
                            "room": room
                        }, exclude=client_id)
                
                elif message_type == "unsubscribe":
                    # Leave room
                    room = message.get("room")
                    if room:
                        manager.leave_room(client_id, room)
                        await manager.send_personal_message({
                            "type": "unsubscribed",
                            "room": room
                        }, client_id)
                        
                        # Notify room
                        await manager.broadcast_to_room(room, {
                            "type": "user_left_room",
                            "client_id": client_id,
                            "room": room
                        }, exclude=client_id)
                
                elif message_type == "message":
                    # Handle regular message
                    room = message.get("room")
                    
                    msg_data = {
                        "type": "message",
                        "client_id": client_id,
                        "data": message.get("data"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    if room:
                        # Broadcast to room
                        msg_data["room"] = room
                        await manager.broadcast_to_room(room, msg_data)
                    else:
                        # Broadcast to all
                        await manager.broadcast(msg_data)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "error": "Invalid JSON format"
                }, client_id)
    
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    
    finally:
        # Cleanup
        heartbeat_task.cancel()
        manager.disconnect(client_id)
        
        # Notify others
        await manager.broadcast({
            "type": "user_left",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })


async def send_heartbeat(websocket: WebSocket, client_id: str):
    """Send periodic heartbeat to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            await manager.send_personal_message({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
    except asyncio.CancelledError:
        pass


# ============= Chat Room WebSocket =============

@app.websocket("/ws/chat/{room}")
async def chat_room(websocket: WebSocket, room: str):
    """Dedicated chat room endpoint"""
    client_id = await manager.connect(websocket)
    manager.join_room(client_id, room)
    
    try:
        # Welcome message
        await manager.send_personal_message({
            "type": "joined_room",
            "room": room,
            "client_id": client_id,
            "users_count": manager.get_room_count(room)
        }, client_id)
        
        # Notify room
        await manager.broadcast_to_room(room, {
            "type": "user_joined",
            "client_id": client_id,
            "users_count": manager.get_room_count(room)
        }, exclude=client_id)
        
        while True:
            data = await websocket.receive_text()
            
            # Broadcast to room
            await manager.broadcast_to_room(room, {
                "type": "message",
                "client_id": client_id,
                "room": room,
                "content": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    except WebSocketDisconnect:
        pass
    
    finally:
        manager.leave_room(client_id, room)
        manager.disconnect(client_id)
        
        # Notify room
        await manager.broadcast_to_room(room, {
            "type": "user_left",
            "client_id": client_id,
            "users_count": manager.get_room_count(room)
        })


# ============= HTTP Endpoints =============

@app.get("/")
async def get_index():
    """Serve a simple test client"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test Client</title>
    </head>
    <body>
        <h1>WebSocket Test Client</h1>
        <div>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        <div>
            <input id="room" placeholder="Room name" />
            <button onclick="subscribe()">Subscribe</button>
            <button onclick="unsubscribe()">Unsubscribe</button>
        </div>
        <div>
            <input id="message" placeholder="Message" />
            <button onclick="sendMessage()">Send</button>
        </div>
        <div>
            <h3>Messages:</h3>
            <ul id="messages"></ul>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                ws = new WebSocket("ws://localhost:8000/ws");
                
                ws.onopen = () => {
                    addMessage("Connected");
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    addMessage(`[${data.type}] ${JSON.stringify(data)}`);
                };
                
                ws.onclose = () => {
                    addMessage("Disconnected");
                };
            }
            
            function disconnect() {
                if (ws) ws.close();
            }
            
            function sendMessage() {
                const message = document.getElementById("message").value;
                const room = document.getElementById("room").value;
                
                ws.send(JSON.stringify({
                    type: "message",
                    room: room || null,
                    data: { text: message }
                }));
                
                document.getElementById("message").value = "";
            }
            
            function subscribe() {
                const room = document.getElementById("room").value;
                ws.send(JSON.stringify({
                    type: "subscribe",
                    room: room
                }));
            }
            
            function unsubscribe() {
                const room = document.getElementById("room").value;
                ws.send(JSON.stringify({
                    type: "unsubscribe",
                    room: room
                }));
            }
            
            function addMessage(msg) {
                const messages = document.getElementById("messages");
                const li = document.createElement("li");
                li.textContent = msg;
                messages.appendChild(li);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/stats")
async def get_stats():
    """Get connection statistics"""
    return {
        "total_connections": len(manager.active_connections),
        "rooms": {
            room: len(clients)
            for room, clients in manager.rooms.items()
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("WebSocket server starting...")
    print("Test client: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
