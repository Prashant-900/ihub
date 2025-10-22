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
    this.ws.addEventListener('open', () => console.log('WS open', this.url));
    this.ws.addEventListener('message', (ev) => {
      try {
        const data = ev.data;
        this.listeners.forEach((l) => l(data));
      } catch (e) {
        console.warn('ws msg parse error', e);
      }
    });
    this.ws.addEventListener('close', () => {
      console.log('WS closed');
      this.ws = null;
      if (!this.closed) setTimeout(() => this.connect(), 1000);
    });
    this.ws.addEventListener('error', (e) => console.warn('WS error', e));
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
