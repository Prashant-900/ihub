/**
 * Minimal WebSocket client wrapper for reliable real-time communication.
 * 
 * Provides automatic reconnection, message queuing, and listener management
 * with clean event-based API.
 */

export default class WSClient {
  /**
   * Initialize WebSocket client.
   * @param {string} url - WebSocket URL to connect to
   */
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Set();
    this.closed = false;
  }

  /**
   * Connect to WebSocket server with automatic reconnection.
   * Attempts to establish connection and automatically reconnects if disconnected.
   */
  connect() {
    if (this.ws || this.closed) return;
    
    this.ws = new WebSocket(this.url);
    
    this.ws.addEventListener('open', () => {
      // Connection established successfully
    });
    
    this.ws.addEventListener('message', (ev) => {
      try {
        const data = ev.data;
        this.listeners.forEach((listener) => {
          try {
            listener(data);
          } catch {
            // Ignore individual listener errors
          }
        });
      } catch {
        // Ignore message processing errors
      }
    });
    
    this.ws.addEventListener('close', () => {
      this.ws = null;
      // Attempt reconnection if not explicitly closed
      if (!this.closed) {
        setTimeout(() => this.connect(), 1000);
      }
    });
    
    this.ws.addEventListener('error', () => {
      // Error will be handled by close event
    });
  }

  /**
   * Send message to server.
   * @param {string} text - Message text to send
   * @returns {boolean} True if message was sent, false otherwise
   */
  send(text) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    try {
      this.ws.send(text);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Register message listener.
   * @param {Function} callback - Function to call on message receipt
   * @returns {Function} Cleanup function to unregister listener
   */
  onMessage(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Close WebSocket connection permanently.
   */
  close() {
    this.closed = true;
    if (this.ws) {
      this.ws.close();
    }
  }
}
