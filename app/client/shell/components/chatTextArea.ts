import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { designTokensCSS } from "../theme/design-tokens.js"

@customElement("chat-input")
export class ChatInput extends LitElement {
  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @state()
  accessor #inputValue = ""

  // Default server URL for sending messages
  private llmDefaultServer = "http://localhost:10002/llm";
  private agentDefaultServer = "http://localhost:10002/agent";

  static styles = css`
    ${designTokensCSS}

    :host {
      display: block;
      width: 100%;
    }

    .input-container {
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
      align-items: center;
    }

    input {
      flex: 1;
      padding: var(--space-md) var(--space-lg);
      font-size: var(--font-size-base);
      border: none;
      border-radius: var(--radius-full);
      background: var(--agent-bg-secondary);
      color: var(--text-primary);
      outline: none;
      font-family: var(--font-family);
      width: 100%;
    }

    input::placeholder {
      color: var(--text-muted);
    }

    button {
      width: 100%;
      height: 3.5rem;
      border-radius: var(--radius-md);
      background: var(--agent-bg-secondary);
      border: none;
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-normal);
    }

    button:hover {
      transform: translateY(-2px);
    }

    button:active {
      transform: scale(0.98);
    }

    .btn-chat {
      background: var(--chat-bg);
      border: 1px solid var(--oracle-primary);
    }

    .btn-chat:hover {
      background: var(--chat-bg-secondary);
      box-shadow: 0 4px 12px rgba(136, 194, 255, 0.3);
    }

    .btn-agent {
      background: var(--agent-bg-secondary);
      border: 1px solid var(--oracle-accent);
    }

    .btn-agent:hover {
      background: var(--agent-border);
      box-shadow: 0 4px 12px rgba(240, 204, 113, 0.3);
    }

    .btn-both {
      background: var(--oracle-bg-dark);
      border: 1px solid var(--oracle-secondary);
    }

    .btn-both:hover {
      background: #3d4249;
      box-shadow: 0 4px 12px rgba(209, 101, 86, 0.3);
    }

    .send-buttons {
      width: 100%;
      display: flex;
      flex-direction: row;
      gap: var(--space-sm);
      align-items: center;
    }
  `

  private async handleSubmit() {
    if (this.#inputValue.trim() && this.router) {
      console.log("Sending message:", this.#inputValue)
      try {
        this.router.sendTextMessage(this.llmDefaultServer, this.#inputValue.trim());
        this.router.sendTextMessage(this.agentDefaultServer, this.#inputValue.trim());
        this.#inputValue = ""
      } catch (error) {
        console.error("Failed to send message:", error);
      }
    }
  }
  
  private async handleSubmitLLM() {
    if (this.#inputValue.trim() && this.router) {
      console.log("Sending message:", this.#inputValue)
      try {
        this.router.sendTextMessage(this.llmDefaultServer, this.#inputValue.trim());
        this.#inputValue = ""
      } catch (error) {
        console.error("Failed to send message:", error);
      }
    }
  }

  private async handleSubmitAgent() {
    if (this.#inputValue.trim() && this.router) {
      console.log("Sending message:", this.#inputValue)
      try {
        this.router.sendTextMessage(this.agentDefaultServer, this.#inputValue.trim());
        this.#inputValue = ""
      } catch (error) {
        console.error("Failed to send message:", error);
      }
    }
  }

  private handleKeyPress(e: KeyboardEvent) {
    if (e.key === "Enter") {
      this.handleSubmit()
    }
  }

  render() {
    return html`
      <div class="input-container">
        <input
          type="text"
          .value=${this.#inputValue}
          @input=${(e: Event) => (this.#inputValue = (e.target as HTMLInputElement).value)}
          @keypress=${this.handleKeyPress}
          placeholder="Top 5 Chinese restaurants in New York"
        />
        <div class="send-buttons">
          <button class="btn-chat" @click=${this.handleSubmitLLM}>
            Message to Chat ▶
          </button>
          <button class="btn-agent" @click=${this.handleSubmitAgent}>
            Message to Agent ▶
          </button>
          <button class="btn-both" @click=${this.handleSubmit}>
            Send to Both ▶
          </button>
        </div>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "chat-input": ChatInput
  }
}
