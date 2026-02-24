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
  accessor messages: Array<{role: 'user' | 'agent', content: string, timestamp: number}> = []

  @state()
  accessor status: Array<{timestamp: number, duration: number, message: string, type: string}> = [{timestamp: Date.now(), duration: 0, message: "Ready", type: "initial"}]

  @state()
  accessor suggestions = ""

  @state()
  accessor #pendingResponse = false

  @state()
  accessor #totalDuration: number = 0;

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
          this.#totalDuration = 0;
          // Add user message to conversation
          this.messages = [...this.messages, {
            role: 'user',
            content: sentEvent.message || 'User query',
            timestamp: Date.now()
          }];
          this.#pendingResponse = true;
          // Reset status with new query start
          this.status = [{timestamp: Date.now(), duration: 0, message: "Query sent", type: "sent"}];
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
            // Add agent response to conversation when final
            if (isFinal && this.#pendingResponse) {
              this.messages = [...this.messages, {
                role: 'agent',
                content: serverMessage,
                timestamp: Date.now()
              }];
              this.#pendingResponse = false;
              // Scroll to bottom after adding message
              this.updateComplete.then(() => this.#scrollToBottom());
            }
            
            // Get final state message (part 1) or current message
            const statusMessage = isFinal && serverState[1]?.text ? serverState[1].text : serverMessage;
            this.#addStatusWithDuration(statusMessage, event.kind);
            
            // Get suggestions (part 2) if available
            if (isFinal && serverState[2]?.text) {
              this.suggestions = serverState[2].text;
            }
            break; // Use the first text part
          }
        }
      }

      if (state === 'failed') {
        this.#addStatusWithDuration("Task failed - An error occurred", "error");
      }

      // Calculate elapsed time when final response is received
      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime;
      }
    }
    else if (event.kind === 'task') {
      this.#addStatusWithDuration("Task management event received", event.kind);
    }
    else if (event.kind === 'message') {
      this.#addStatusWithDuration("Direct message received", event.kind);
    }
    else {
      this.#addStatusWithDuration(`Event type: ${event.kind || 'unknown'}`, event.kind || 'unknown');
    }
  }

  // status calculated from previous steps
  #addStatusWithDuration(message: string, type: string) {
    const now = Date.now();
    const lastStatus = this.status[this.status.length - 1];
    const duration = lastStatus ? (now - lastStatus.timestamp) / 1000 : 0;
    
    this.status = [...this.status, {
      timestamp: now,
      duration: duration,
      message,
      type
    }];
    
    // Update total duration from start
    if (this.#startTime) {
      this.#totalDuration = (now - this.#startTime) / 1000;
    }
  }

  //Parse from a list into single suggestions
  #parseSuggestions(suggestionsText: string): string[] {
    // First, try to parse as JSON and extract suggested_questions
    try {
      const parsed = JSON.parse(suggestionsText);
      if (parsed && Array.isArray(parsed.suggested_questions)) {
        return parsed.suggested_questions;
      }
    } catch (e) {
      // Split by newlines
      let suggestions = suggestionsText
        .split(/\n/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
  
      // Split by comas
      if (suggestions.length === 1) {
        suggestions = suggestions[0]
          .split(/[,;]/)
          .map(s => s.trim())
          .filter(s => s.length > 0);
      }
  
      // try to reduce other symbols
      return suggestions.map(s => s.replace(/^(\d+[\.\)]\s*|[-•]\s*)/, '').trim());
    }
  }

  #scrollToBottom() {
    const chatContainer = this.shadowRoot?.querySelector('.chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
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
      flex: 1 1 auto;
      min-width: 0;
      overflow-y: auto;
    }



    .subtitle {
      font-size: 1rem;
      margin-bottom: 1.5rem;
      opacity: 0.9;
    }

    .chat-messages {
      flex: 1 1 auto;
      min-height: 100px;
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 0.5rem;
      padding: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 0.5rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .message {
      padding: 0.75rem 1rem;
      border-radius: 0.75rem;
      max-width: 85%;
    }

    .message.user {
      align-self: flex-end;
      background: rgba(59, 130, 246, 0.5);
      border-bottom-right-radius: 0.25rem;
    }

    .message.agent {
      align-self: flex-start;
      background: rgba(255, 255, 255, 0.15);
      border-bottom-left-radius: 0.25rem;
    }

    .message-role {
      font-size: 0.75rem;
      opacity: 0.7;
      margin-bottom: 0.25rem;
      text-transform: uppercase;
    }

    .message-content {
      word-wrap: break-word;
    }

    .message-content p {
      margin: 0 0 0.5rem 0;
    }

    .message-content p:last-child {
      margin-bottom: 0;
    }

    .pending-indicator {
      align-self: flex-start;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .typing-dots {
      display: flex;
      gap: 0.25rem;
    }

    .typing-dots span {
      width: 6px;
      height: 6px;
      background: white;
      border-radius: 50%;
      animation: bounce 1.4s ease-in-out infinite;
    }

    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }

    .empty-chat {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0.6;
      font-style: italic;
    }

    .status {
      flex-shrink: 0;
      font-size: 0.875rem;
      padding: 0.5rem;
      display: flex;
      flex-direction: column;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      min-height: 80px;
      max-height: 250px;
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
      display: flex;
      gap: 0.5rem;
    }

    .status-item:last-child {
      border-bottom: none;
    }

    .status-item .duration {
      font-weight: bold;
      color: white;
      min-width: 4rem;
      text-align: right;
    }

    .suggestions {
      flex-shrink: 0;
      font-size: 0.875rem;
      padding: 1rem;
      margin-bottom: 0.5rem;
      background: none;
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
        .time=${this.#totalDuration > 0 ? `${this.#totalDuration.toFixed(2)}s` : '0.00s'}
        .tokens=${'569'}
        .configUrl=${'/llm_config'}
        .configType=${'llm'}
        .configData=${chatConfig}
      ></stat-bar>
      <div class="chat-messages">
        ${this.messages.length === 0 ? html`
          <div class="empty-chat">Start a conversation by typing a message below...</div>
        ` : ''}
        ${repeat(
          this.messages,
          (msg) => msg.timestamp,
          (msg) => html`
            <div class="message ${msg.role}">
              <div class="message-role">${msg.role === 'user' ? 'You' : 'Assistant'}</div>
              <div class="message-content">${unsafeHTML(marked(msg.content) as string)}</div>
            </div>
          `
        )}
        ${this.#pendingResponse ? html`
          <div class="pending-indicator">
            <div class="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span>Thinking...</span>
          </div>
        ` : ''}
      </div>
      ${this.suggestions ? html`
        <div class="suggestions">
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
            <span class="duration">${item.duration.toFixed(2)}s</span> - ${item.message}
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
