import { LitElement, html, css } from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { marked } from "marked"
import { unsafeHTML } from "lit/directives/unsafe-html.js"
import { repeat } from "lit/directives/repeat.js"
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
  accessor status: Array<{timestamp: string, message: string, type: string}> = [{timestamp: new Date().toISOString(), message: "Ready", type: "initial"}]

  @state()
  accessor suggestions = ""

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

      console.log("process state", state);
      console.log("server message", serverState);

      // Extract text parts
      if (hasMessage) {
        for (const part of status.message.parts) {
          if (part.kind === 'text') {
            this.response = isFinal ? serverMessage : "Working on response...";
            
            // Get final state message (part 1) or current message
            const statusMessage = isFinal && serverState[1]?.text ? serverState[1].text : serverMessage;
            this.status = [...this.status, {timestamp: new Date().toISOString(), message: statusMessage, type: event.kind}];
            
            // Get suggestions (part 2) if available
            if (isFinal && serverState[2]?.text) {
              this.suggestions = serverState[2].text;
            }
            break; // Use the first text part
          }
        }
      }

      if (state === 'failed') {
        this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Task failed - An error occurred", type: "error"}];
      }

      // Calculate elapsed time when final response is received
      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime;
      }
    }
    else if (event.kind === 'task') {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Task management event received", type: event.kind}];
    }
    else if (event.kind === 'message') {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Direct message received", type: event.kind}];
    }
    else {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: `Event type: ${event.kind || 'unknown'}`, type: event.kind || 'unknown'}];
    }
  }

  //Parse from a list into single suggestions
  #parseSuggestions(suggestionsText: string): string[] {
    // Split by newlines first
    let suggestions = suggestionsText
      .split(/\n/)
      .map(s => s.trim())
      .filter(s => s.length > 0);

    // If only one item, try splitting by commas or semicolons
    if (suggestions.length === 1) {
      suggestions = suggestions[0]
        .split(/[,;]/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
    }

    // remove the extra data
    return suggestions.map(s => s.replace(/^(\d+[\.\)]\s*|[-•]\s*)/, '').trim());
  }

  // this sends the message to the server
  async #handleSuggestionClick(suggestion: string) {
    if (!this.router || !suggestion.trim()) return;

    console.log("Sending suggestion as query:", suggestion);
    try {
      // Clear current suggestions when a new query is sent
      this.suggestions = "";
      this.router.sendTextMessage(this.defaultServerUrl, suggestion.trim());
    } catch (error) {
      console.error("Failed to send suggestion:", error);
    }
  }

  static styles = css`
    :host {
      border-radius: 1rem;
      padding: 0.5rem;
      color: white;
      display: flex;
      flex-direction: column;
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
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
      padding: 0.5rem;
      display: flex;
      flex-direction: column;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      max-height: 200px;
      overflow-y: auto;
    }

    .status p {
      margin: 0.25rem 0;
    }

    .status-item {
      padding: 0.25rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
      font-size: 0.8rem;
      line-height: 1.4;
    }

    .status-item:last-child {
      border-bottom: none;
    }

    .suggestions {
      font-size: 0.875rem;
      padding: 1rem;
      margin-bottom: 0.5rem;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 0.5rem;
      border-left: 3px solid var(--p-60, #7c3aed);
    }

    .suggestions-title {
      font-weight: bold;
      margin-bottom: 0.5rem;
      opacity: 0.9;
    }

    .suggestions-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .suggestion-item {
      padding: 0.5rem 0.75rem;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.375rem;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .suggestion-item:hover {
      background: rgba(255, 255, 255, 0.25);
      transform: translateX(4px);
    }

    .suggestion-item:active {
      transform: scale(0.98);
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
      ${this.suggestions ? html`
        <div class="suggestions">
          <div class="suggestions-title">Suggestions:</div>
          <div class="suggestions-list">
            ${this.#parseSuggestions(this.suggestions).map(suggestion => html`
              <div class="suggestion-item" @click=${() => this.#handleSuggestionClick(suggestion)}>
                ${suggestion}
              </div>
            `)}
          </div>
        </div>
      ` : ''}
      <div class="status">
        ${repeat(
          this.status,
          (item) => item.timestamp,
          (item) => html`<div class="status-item">
            ${new Date(item.timestamp).toLocaleTimeString()} - ${item.message}
          </div>`
        )}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "chat-module": ChatModule
  }
}
