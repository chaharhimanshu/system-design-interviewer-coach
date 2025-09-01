import type { WebSocketMessage, SessionMessage } from './types';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<Function>> = new Map();
  private sessionId: string | null = null;

  constructor() {
    // Initialize listeners map
    this.listeners.set('message', new Set());
    this.listeners.set('status', new Set());
    this.listeners.set('error', new Set());
    this.listeners.set('connected', new Set());
    this.listeners.set('disconnected', new Set());
  }

  // Connect to WebSocket for a specific session
  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.sessionId = sessionId;
      const wsUrl = `ws://localhost:8000/ws/session/${sessionId}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.emit('connected', { sessionId });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.emit(message.type, message.data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            this.emit('error', { error: 'Invalid message format' });
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          // Attempt to reconnect if not closed intentionally
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', { error: 'Connection error' });
          reject(error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  // Disconnect from WebSocket
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
      this.sessionId = null;
    }
  }

  // Send a message
  sendMessage(message: string, type: 'text' | 'audio' | 'file' = 'text', metadata?: any) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    const wsMessage: WebSocketMessage = {
      type: 'message',
      data: {
        content: message,
        messageType: type,
        metadata,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    };

    this.ws.send(JSON.stringify(wsMessage));
  }

  // Send typing indicator
  sendTyping(isTyping: boolean) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const wsMessage: WebSocketMessage = {
      type: 'typing',
      data: { isTyping },
      timestamp: new Date().toISOString()
    };

    this.ws.send(JSON.stringify(wsMessage));
  }

  // Send session status update
  sendStatus(status: string, data?: any) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const wsMessage: WebSocketMessage = {
      type: 'status',
      data: { status, ...data },
      timestamp: new Date().toISOString()
    };

    this.ws.send(JSON.stringify(wsMessage));
  }

  // Add event listener
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
  }

  // Remove event listener
  off(event: string, callback?: Function) {
    if (callback) {
      this.listeners.get(event)?.delete(callback);
    } else {
      this.listeners.get(event)?.clear();
    }
  }

  // Emit event to all listeners
  protected emit(event: string, data: any) {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in WebSocket event listener:', error);
      }
    });
  }

  // Schedule reconnection attempt
  private scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.sessionId) {
        this.connect(this.sessionId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  // Get connection status
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Get current session ID
  get currentSessionId(): string | null {
    return this.sessionId;
  }
}

// Singleton instance
export const webSocketService = new WebSocketService();

// Mock WebSocket simulation for development
export class MockWebSocketService extends WebSocketService {
  private mockResponses = [
    "That's a great approach! Can you elaborate on how you would handle the database design?",
    "I see you're thinking about scalability. What about caching strategies?",
    "Excellent point about load balancing. How would you handle database sharding?",
    "That's a solid solution. Let's discuss the trade-offs of your approach.",
    "Good thinking on the API design. How would you handle rate limiting?",
    "I like your consideration of security. What about data consistency?",
    "That's an interesting approach to handling failures. Can you walk through a specific scenario?",
    "Great system design! Let's dive deeper into the monitoring and alerting strategy."
  ];

  connect(sessionId: string): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.emit('connected', { sessionId });
        resolve();
      }, 500);
    });
  }

  sendMessage(message: string): void {
    // Simulate user message being processed
    setTimeout(() => {
      this.emit('message', {
        id: Date.now().toString(),
        type: 'user',
        content: message,
        timestamp: new Date().toISOString()
      } as SessionMessage);
    }, 100);

    // Simulate AI typing
    setTimeout(() => {
      this.emit('typing', { isTyping: true, sender: 'ai' });
    }, 500);

    // Simulate AI response
    setTimeout(() => {
      this.emit('typing', { isTyping: false, sender: 'ai' });
      
      const randomResponse = this.mockResponses[Math.floor(Math.random() * this.mockResponses.length)];
      this.emit('message', {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: randomResponse,
        timestamp: new Date().toISOString()
      } as SessionMessage);
    }, 2000 + Math.random() * 2000); // Random delay between 2-4 seconds
  }

  disconnect() {
    this.emit('disconnected', { code: 1000, reason: 'Client disconnect' });
  }

  get isConnected(): boolean {
    return true; // Always connected in mock mode
  }
}

// Use mock service in development
export const wsService = import.meta.env.DEV 
  ? new MockWebSocketService() 
  : webSocketService;
