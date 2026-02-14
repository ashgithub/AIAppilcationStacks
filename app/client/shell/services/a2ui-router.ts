import { A2UIClient } from "./client.js";
import { v0_8 } from "@a2ui/lit";
import { createContext } from "@lit/context";

export class A2UIRouter extends EventTarget {
  private clients = new Map<string, A2UIClient>();

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
   */
  async sendMessage(
    serverUrl: string,
    message: v0_8.Types.A2UIClientEventMessage | string
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    const client = this.getClient(serverUrl);
    return client.send(message);
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

  // This function is in case the client needs to close SSe
  cleanup(serverUrl: string): void {
    const client = this.clients.get(serverUrl);
    if (client) {
      // Note: A2UIClient doesn't have a disconnect method yet
      // TODO: This is a placeholder for future cleanup
      // Missing to add the logic to close server
      this.clients.delete(serverUrl);
    }
  }
}

// Create a singleton instance
export const a2uiRouter = new A2UIRouter();

// Context for dependency injection
export const routerContext = createContext<A2UIRouter>('a2ui-router');
