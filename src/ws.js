// Minimal WebSocket helper for the frontend
export default class WSClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Set();
    this.closed = false;
  }

  connect() {
    if (this.ws || this.closed) return;
    this.ws = new WebSocket(this.url);
    this.ws.addEventListener('open', () => void 0);
    this.ws.addEventListener('message', (ev) => {
      try {
        const data = ev.data;
        this.listeners.forEach((l) => l(data));
      } catch {
        void 0;
      }
    });
    this.ws.addEventListener('close', () => {
      this.ws = null;
      if (!this.closed) setTimeout(() => this.connect(), 1000);
    });
    this.ws.addEventListener('error', () => void 0);
  }

  send(text) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
    this.ws.send(text);
    return true;
  }

  onMessage(cb) {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  close() {
    this.closed = true;
    if (this.ws) this.ws.close();
  }
}
