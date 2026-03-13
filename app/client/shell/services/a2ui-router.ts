import { A2UIClient } from "./client.js";
import { v0_8 } from "@a2ui/lit";
import { createContext } from "@lit/context";

export class A2UIRouter extends EventTarget {
  private clients = new Map<string, A2UIClient>();
  private sessions = new Map<string, string>();

  private getClient(serverUrl: string): A2UIClient {
    if (!this.clients.has(serverUrl)) {
      const client = new A2UIClient(serverUrl);

      client.addEventListener('streaming-event', (event: any) => {
        // Attach source server so each module can filter events.
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

  /** Sends text or structured A2UI messages to the target server. */
  async sendMessage(
    serverUrl: string,
    message: v0_8.Types.A2UIClientEventMessage | string,
    useSession: boolean = true
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    const client = this.getClient(serverUrl);
    const sessionId = useSession ? this.getSessionId(serverUrl) : undefined;
    return client.send(message, sessionId);
  }

  /** Sends a plain text prompt. */
  async sendTextMessage(serverUrl: string, text: string): Promise<v0_8.Types.ServerToClientMessage[]> {
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

  /** Sends a structured A2UI event payload. */
  async sendA2UIMessage(
    serverUrl: string,
    message: v0_8.Types.A2UIClientEventMessage
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
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

  cleanup(serverUrl: string): void {
    const client = this.clients.get(serverUrl);
    if (client) {
      // TODO: close the active stream once SDK adds a disconnect API.
      this.clients.delete(serverUrl);
    }
    this.sessions.delete(serverUrl);
  }
}

export const a2uiRouter = new A2UIRouter();

export const routerContext = createContext<A2UIRouter>('a2ui-router');
