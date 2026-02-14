import { LitElement, html, css } from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { marked } from "marked"
import { unsafeHTML } from "lit/directives/unsafe-html.js"
import "./stat_bar.js"
import { chatConfig } from "../configs/chat_config.js"

@customElement("chat-module")
export class ChatModule extends LitElement {
  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @property({ type: String })
  accessor title = ""

  @property({ type: String })
  accessor subtitle = ""

  @property({ type: String })
  accessor color = "#334155"

  @state()
  accessor response = ""

  @state()
  accessor status = "Ready"

  @state()
  accessor #startTime: number | null = null;

  @state()
  accessor #elapsedTime: number | null = null;

  // Default server URL for this module
  private defaultServerUrl = "http://localhost:10002/llm";

  connectedCallback() {
    super.connectedCallback();

    // Listen for streaming events from the router
    if (this.router) {
      this.router.addEventListener('streaming-event', (event: any) => {
        const streamingEvent = event.detail;
        this.processStreamingEvent(streamingEvent);
      });

      this.router.addEventListener('message-sent', (event: any) => {
        const sentEvent = event.detail;
        if (sentEvent.serverUrl === this.defaultServerUrl) {
          this.#startTime = sentEvent.timestamp;
          this.#elapsedTime = null;
        }
      });
    }
  }

  private processStreamingEvent(event: any) {
    // Only process events from this module's server URL
    if (event.serverUrl !== this.defaultServerUrl) return;

    // Process text messages for chat display
    if (event.kind === 'status-update') {
      const status = event.status;
      const isFinal = event.final;
      const state = status?.state;
      const hasMessage = status?.message?.parts?.length > 0;

      const serverState: Array<any> = hasMessage ? event.status.message.parts : [{ "text": "Server did not send any message parts" }];
      const serverMessage = serverState[0].text || "No text content"

      console.log("process status", status);
      console.log("process final message received", isFinal);
      console.log("process state", state);
      console.log("server message", serverState);
      console.log("End of message update")

      // Extract text parts
      if (hasMessage) {
        for (const part of status.message.parts) {
          if (part.kind === 'text') {
            this.response = isFinal ? serverMessage : "Working on response...";
            this.status = isFinal ? serverState[1].text : serverMessage;
            break; // Use the first text part
          }
        }
      }

      if (state === 'failed') {
        this.status = "Task failed - An error occurred";
      }

      // Calculate elapsed time when final response is received
      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime;
      }
    }
    else if (event.kind === 'task') {
      this.status = "Task management event received";
    }
    else if (event.kind === 'message') {
      this.status = "Direct message received";
    }
    else {
      this.status = `Event type: ${event.kind || 'unknown'}`;
    }
  }

  static styles = css`
    :host {
      border-radius: 1rem;
      padding: 0.5rem;
      color: white;
      display: flex;
      flex-direction: column;
      flex: 1;
    }



    .subtitle {
      font-size: 1rem;
      margin-bottom: 1.5rem;
      opacity: 0.9;
    }

    .response {
      flex: 1;
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 1.5rem;
      padding: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 0.5rem;
      overflow-y: auto;
    }

    .status {
      font-size: 0.875rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
    }

    .status p {
      margin: 0.25rem 0;
    }

    .status-text {
      white-space: pre-wrap;
    }

    .pending {
      width: 100%;
      min-height: 200px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
      gap: 16px;
    }

    .spinner {
      width: 48px;
      height: 48px;
      border: 4px solid rgba(255, 255, 255, 0.1);
      border-left-color: var(--p-60);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }

      to {
        opacity: 1;
      }
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
  `

  render() {
    return [
      this.#mainDynamicRegion(),
    ]
  }

  #mainDynamicRegion() {
    return html`
      <style>
        :host {
          background: ${this.color};
        }
      </style>
      <stat-bar
        .title=${this.title}
        .time=${this.#elapsedTime !== null ? `${(this.#elapsedTime / 1000).toFixed(2)}s` : '0.00s'}
        .tokens=${'569'}
        .configUrl=${'/llm_config'}
        .configType=${'llm'}
        .configData=${chatConfig}
      ></stat-bar>
      <div class="response">${unsafeHTML(marked(this.response || "Waiting for query...") as string)}</div>
      <div class="status">
        <p>Status:</p>
        <p class="status-text">${this.status}</p>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "chat-module": ChatModule
  }
}
