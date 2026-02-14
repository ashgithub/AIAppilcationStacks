import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"

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
    :host {
      display: block;
      width: 100%;
    }

    .input-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      align-items: center;
    }

    input {
      flex: 1;
      padding: 1rem 1.5rem;
      font-size: 1rem;
      border: none;
      border-radius: 2rem;
      background: #334155;
      color: white;
      outline: none;
      font-family: 'Inter', sans-serif;
      width: 100%;
    }

    input::placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

    button {
      width: 100%;
      height: 3.5rem;
      border-radius: 0.5rem;
      background: #334155;
      border: none;
      color: white;
      font-size: 1.25rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }

    button:hover {
      background: rgba(255, 255, 255, 0.5);
    }

    button:active {
      transform: scale(0.95);
    }

    .send-buttons{
      width: 100%;
      display:flex;
      flex-direction: row;
      gap: 0.5rem;
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
          <button @click=${this.handleSubmitLLM}>
            Message to chat application ▶
          </button>
          <button @click=${this.handleSubmitAgent}>
            Message to agent application ▶
          </button>
          <button @click=${this.handleSubmit}>
            Messages to both applications ▶
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
