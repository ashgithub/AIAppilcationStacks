import { A2UIClient } from "./client.js";
import { v0_8 } from "@a2ui/lit";
import { createContext } from "@lit/context";

export class A2UIRouter extends EventTarget {
  private clients = new Map<string, A2UIClient>();
  private sessions = new Map<string, string>(); // serverUrl -> sessionId

  // Get or create an A2UIClient for the given server URL
  private getClient(serverUrl: string): A2UIClient {
    if (!this.clients.has(serverUrl)) {
      const client = new A2UIClient(serverUrl);

      // Forward all streaming events from the client
      client.addEventListener('streaming-event', (event: any) => {
        // Re-dispatch the event with server URL context. important to filter events
        this.dispatchEvent(new CustomEvent('streaming-event', {
          detail: {
            ...event.detail,
            serverUrl
          },
          bubbles: true,
          composed: true
        }));
      });

      this.clients.set(serverUrl, client);
    }
    return this.clients.get(serverUrl)!;
  }

  /**
   * Send a message to the server
   * @param serverUrl The server URL to send to
   * @param message The message to send (string for text, A2UI object for structured)
   * @param useSession Whether to include session ID for memory persistence
   */
  async sendMessage(
    serverUrl: string,
    message: v0_8.Types.A2UIClientEventMessage | string,
    useSession: boolean = true
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    const client = this.getClient(serverUrl);
    const sessionId = useSession ? this.getSessionId(serverUrl) : undefined;
    return client.send(message, sessionId);
  }

  /**
   * Send a text message to the server
   * @param serverUrl The server URL to send to
   * @param text The text message to send
   */
  async sendTextMessage(serverUrl: string, text: string): Promise<v0_8.Types.ServerToClientMessage[]> {
    // Emit message-sent event for timing
    this.dispatchEvent(new CustomEvent('message-sent', {
      detail: {
        serverUrl,
        message: text,
        timestamp: Date.now()
      },
      bubbles: true,
      composed: true
    }));

    return this.sendMessage(serverUrl, text);
  }

  /**
   * Send an A2UI structured message to the server
   * @param serverUrl The server URL to send to
   * @param message The A2UI message to send
   */
  async sendA2UIMessage(
    serverUrl: string,
    message: v0_8.Types.A2UIClientEventMessage
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    // Emit message-sent event for timing
    this.dispatchEvent(new CustomEvent('message-sent', {
      detail: {
        serverUrl,
        timestamp: Date.now()
      },
      bubbles: true,
      composed: true
    }));

    return this.sendMessage(serverUrl, message);
  }

  // Gets all active server URLs (endpoints from starlette app)
  getActiveServers(): string[] {
    return Array.from(this.clients.keys());
  }

  getSessionId(serverUrl: string): string {
    if (!this.sessions.has(serverUrl)) {
      this.sessions.set(serverUrl, crypto.randomUUID());
    }
    return this.sessions.get(serverUrl)!;
  }

  resetSession(serverUrl: string): string {
    const newSessionId = crypto.randomUUID();
    this.sessions.set(serverUrl, newSessionId);
    return newSessionId;
  }

  resetAllSessions(): void {
    this.sessions.clear();
  }

  // This function is in case the client needs to close SSe
  cleanup(serverUrl: string): void {
    const client = this.clients.get(serverUrl);
    if (client) {
      // Note: A2UIClient doesn't have a disconnect method yet
      // TODO: This is a placeholder for future cleanup
      // Missing to add the logic to close server
      this.clients.delete(serverUrl);
    }
    this.sessions.delete(serverUrl);
  }
}

// Create a singleton instance
export const a2uiRouter = new A2UIRouter();

// Context for dependency injection
export const routerContext = createContext<A2UIRouter>('a2ui-router');
