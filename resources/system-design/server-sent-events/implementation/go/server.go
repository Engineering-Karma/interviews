/*
Server-Sent Events (SSE) Implementation with Go and net/http.

Demonstrates:
- Unidirectional server-to-client streaming.
- Event streams with proper format.
- Multiple event types.
- Automatic reconnection with Last-Event-ID.
- Keep-alive heartbeat.

Note:
This implementation serves to illustrate SSE concepts and is not production ready.
*/
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"net/http"
	"strconv"
	"sync"
	"time"
)

const (
	PORT              = 8000
	MAX_HISTORY_SIZE  = 100
	EVENT_SEND_DELAY  = 2 * time.Second
	NOTIF_SEND_DELAY  = 5 * time.Second
	STOCK_SEND_DELAY  = 1 * time.Second
	HEARTBEAT_INTERVAL = 15
)

// Event represents an SSE event.
type Event struct {
	ID   int         `json:"id"`
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

// Global state
var (
	eventHistory   []Event
	eventIDCounter int
	mu             sync.Mutex
)

// getNextEventID returns the next event ID and increments the counter.
func getNextEventID() int {
	mu.Lock()
	defer mu.Unlock()
	eventIDCounter++
	return eventIDCounter
}

// addEventToHistory adds an event to history, maintaining max size.
func addEventToHistory(event Event) {
	mu.Lock()
	defer mu.Unlock()
	eventHistory = append(eventHistory, event)
	if len(eventHistory) > MAX_HISTORY_SIZE {
		eventHistory = eventHistory[1:]
	}
}

// getMissedEvents returns events with ID greater than lastID.
func getMissedEvents(lastID int) []Event {
	mu.Lock()
	defer mu.Unlock()
	var missed []Event
	for _, e := range eventHistory {
		if e.ID > lastID {
			missed = append(missed, e)
		}
	}
	return missed
}

// writeSSEEvent writes an SSE event to the response writer.
func writeSSEEvent(w http.ResponseWriter, id int, eventType string, data interface{}) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		fmt.Fprintf(w, ": error - serialization failed\n\n")
		return
	}
	fmt.Fprintf(w, "id: %d\n", id)
	fmt.Fprintf(w, "event: %s\n", eventType)
	fmt.Fprintf(w, "data: %s\n\n", string(jsonData))
	w.(http.Flusher).Flush()
}

// writeSSEHeartbeat writes an SSE heartbeat (comment line).
func writeSSEHeartbeat(w http.ResponseWriter) {
	fmt.Fprintf(w, ": heartbeat\n\n")
	w.(http.Flusher).Flush()
}

// eventGenerator generates the event stream.
func eventGenerator(w http.ResponseWriter, lastEventID string) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	// Send connection established event
	id := getNextEventID()
	writeSSEEvent(w, id, "connected", map[string]string{
		"message": "Connected to SSE stream.",
	})

	// Replay missed events if Last-Event-ID provided
	if lastEventID != "" {
		if lastID, err := strconv.Atoi(lastEventID); err == nil {
			for _, event := range getMissedEvents(lastID) {
				writeSSEEvent(w, event.ID, event.Type, event.Data)
			}
		}
	}

	// Continuous event stream
	ticker := time.NewTicker(EVENT_SEND_DELAY)
	defer ticker.Stop()

	for range ticker.C {
		id := getNextEventID()
		eventData := map[string]interface{}{
			"timestamp": time.Now().UTC().Format(time.RFC3339),
			"value":     rand.Intn(100) + 1,
			"message":   fmt.Sprintf("Update #%d.", id),
		}

		event := Event{ID: id, Type: "update", Data: eventData}
		addEventToHistory(event)

		writeSSEEvent(w, id, "update", eventData)

		// Periodic heartbeat
		if id%HEARTBEAT_INTERVAL == 0 {
			writeSSEHeartbeat(w)
		}
	}
}

// notificationGenerator generates user-specific notifications.
func notificationGenerator(w http.ResponseWriter, userID string) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	// Send connection established event
	id := getNextEventID()
	writeSSEEvent(w, id, "connected", map[string]string{
		"user_id": userID,
		"message": "Connected.",
	})

	notificationTypes := []string{"message", "alert", "info"}
	ticker := time.NewTicker(NOTIF_SEND_DELAY)
	defer ticker.Stop()

	for range ticker.C {
		id := getNextEventID()
		notification := map[string]interface{}{
			"user_id":   userID,
			"type":      notificationTypes[rand.Intn(len(notificationTypes))],
			"content":   fmt.Sprintf("Notification at %s.", time.Now().UTC().Format(time.RFC3339)),
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		}

		writeSSEEvent(w, id, "notification", notification)
	}
}

// stockTickerGenerator simulates stock price updates.
func stockTickerGenerator(w http.ResponseWriter) {
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")

	// Send connection established event
	id := getNextEventID()
	writeSSEEvent(w, id, "connected", map[string]string{
		"message": "Connected to SSE stream.",
	})

	stocks := map[string]float64{
		"AAPL":  150.00,
		"GOOGL": 2800.00,
		"MSFT":  300.00,
	}

	ticker := time.NewTicker(STOCK_SEND_DELAY)
	defer ticker.Stop()

	symbols := []string{"AAPL", "GOOGL", "MSFT"}

	for range ticker.C {
		id := getNextEventID()

		// Random price change
		symbol := symbols[rand.Intn(len(symbols))]
		change := (rand.Float64() * 10) - 5
		stocks[symbol] += change

		data := map[string]interface{}{
			"symbol":    symbol,
			"price":     math.Round(stocks[symbol]*100) / 100,
			"change":    math.Round(change*100) / 100,
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		}

		writeSSEEvent(w, id, "price_update", data)
	}
}

// ============= SSE Endpoints =============

// /events endpoint with event replay support
func handleEvents(w http.ResponseWriter, r *http.Request) {
	lastEventID := r.Header.Get("Last-Event-ID")
	eventGenerator(w, lastEventID)
}

// /notifications endpoint for user-specific notifications
func handleNotifications(w http.ResponseWriter, r *http.Request) {
	userID := r.URL.Query().Get("user_id")
	if userID == "" {
		userID = "user123"
	}
	notificationGenerator(w, userID)
}

// /stocks endpoint for real-time stock price updates
func handleStocks(w http.ResponseWriter, r *http.Request) {
	stockTickerGenerator(w)
}

// ============= HTTP Endpoints =============

// / endpoint serves the test client HTML
func handleIndex(w http.ResponseWriter, r *http.Request) {
	html := `
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
				eventSource = new EventSource('/notifications?user_id=user123');
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
					addEvent('Update', 'Value: ' + data.value, 'blue');
				});
				
				eventSource.addEventListener('notification', (e) => {
					const data = JSON.parse(e.data);
					addEvent('Notification', data.content, 'orange');
				});
				
				eventSource.addEventListener('price_update', (e) => {
					const data = JSON.parse(e.data);
					addEvent('Stock', data.symbol + ': $' + data.price, 'purple');
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
				div.style.borderLeft = '4px solid ' + color;
				div.innerHTML = '<strong>[' + type + ']</strong> ' + message + ' <small>(' + new Date().toLocaleTimeString() + ')</small>';
				events.insertBefore(div, events.firstChild);
				
				// Keep only last 50 events
				while (events.children.length > 50) {
					events.removeChild(events.lastChild);
				}
			}
		</script>
	</body>
	</html>
	`
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, html)
}

// /health endpoint for health checks
func handleHealth(w http.ResponseWriter, r *http.Request) {
	mu.Lock()
	activeEvents := len(eventHistory)
	mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":         "healthy",
		"active_events":  activeEvents,
		"timestamp":      time.Now().UTC().Format(time.RFC3339),
	})
}

func main() {
	rand.Seed(time.Now().UnixNano())

	http.HandleFunc("/events", handleEvents)
	http.HandleFunc("/notifications", handleNotifications)
	http.HandleFunc("/stocks", handleStocks)
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/health", handleHealth)

	addr := fmt.Sprintf(":%d", PORT)
	log.Printf("SSE server starting...\n")
	log.Printf("Test client: http://localhost:%d\n", PORT)
	log.Fatal(http.ListenAndServe(addr, nil))
}
