import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { designTokensCSS, buttonStyles } from "../theme/design-tokens.js"

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
    ${buttonStyles}

    :host {
      display: block;
      width: 100%;
    }

    .input-container {
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
      padding: var(--space-sm);
      background: var(--agent-bg-secondary);
      border-radius: var(--radius-md);
    }

    input {
      flex: 1;
      padding: var(--space-sm) var(--space-md);
      height: 36px;
      font-size: var(--font-size-sm);
      border: 1px solid var(--border-secondary);
      border-radius: var(--radius-sm);
      background: var(--agent-bg);
      color: var(--text-primary);
      outline: none;
      font-family: var(--font-family);
      transition: border-color var(--transition-normal);
    }

    input:focus {
      border-color: var(--oracle-primary);
    }

    input::placeholder {
      color: var(--text-muted);
    }

    .send-buttons {
      display: flex;
      gap: var(--space-xs);
      align-items: stretch;
    }

    .send-buttons .btn {
      flex: 1;
    }

    .send-buttons .btn-secondary {
      flex: 2;
    }

    /* Responsive: stack on small screens */
    @media (max-width: 600px) {
      .send-buttons {
        flex-direction: column;
      }
      
      .send-buttons .btn {
        flex: none;
      }
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
          placeholder="Show me latest outage zones..."
        />
        <div class="send-buttons">
          <button class="btn btn-outline-chat" @click=${this.handleSubmitLLM} title="Send to Chat Module">
            Send to Chat
          </button>
          <button class="btn btn-secondary" @click=${this.handleSubmit} title="Send to Both Modules">
            Send to Both
          </button>
          <button class="btn btn-outline-agent" @click=${this.handleSubmitAgent} title="Send to Agent Module">
            Send to Agent
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
