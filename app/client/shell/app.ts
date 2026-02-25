import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { provide } from "@lit/context"
import { a2uiRouter, routerContext } from "./services/a2ui-router.js"
import { designTokensCSS, colors, radius, spacing } from "./theme/design-tokens.js"
import "./components/main_traditional"
import "./components/chatTextArea"
import "./components/main_agent"
import "./components/main_chat"

@customElement("app-container")
export class AppContainer extends LitElement {
  @provide({ context: routerContext })
  accessor router = a2uiRouter;

  @state()
  accessor showingTraditional = true;

  @state()
  accessor showingChat = true;

  @state()
  accessor showingAgent = true;

  static styles = css`
    ${designTokensCSS}

    :host {
      display: flex;
      flex-direction: column;
      width: 100%;
      min-height: 100vh;
      background: var(--agent-bg);
      font-family: var(--font-family);
    }

    .container {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      padding: var(--space-sm);
      gap: var(--space-sm);
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text-primary);
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-normal);
      margin-bottom: 0;
    }

    .controls {
      display: flex;
      gap: var(--space-md);
      align-items: center;
    }

    .control {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      color: var(--text-primary);
      font-size: var(--font-size-base);
    }

    .modules {
      display: flex;
      flex-wrap: nowrap;
      gap: var(--space-lg);
      flex: 1;
      width: 100%;
      min-height: 0;
    }

    .modules > * {
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
    }
  `

  render() {
    return html`
      <div class="container">
        <div class="header">
          A2UI
          <div class="controls">
    <label class="control">
      <input
        type="checkbox"
        .checked=${this.showingTraditional}
        @change=${(e: Event) => {
          this.showingTraditional = (e.target as HTMLInputElement).checked;
          if (this.showingTraditional) {
            this.router.resetSession("http://localhost:10002/traditional");
          }
        }}
      />
      Traditional
    </label>
    <label class="control">
      <input
        type="checkbox"
        .checked=${this.showingChat}
        @change=${(e: Event) => {
          this.showingChat = (e.target as HTMLInputElement).checked;
          if (this.showingChat) {
            this.router.resetSession("http://localhost:10002/llm");
          }
        }}
      />
      Chat
    </label>
    <label class="control">
      <input
        type="checkbox"
        .checked=${this.showingAgent}
        @change=${(e: Event) => {
          this.showingAgent = (e.target as HTMLInputElement).checked;
          if (this.showingAgent) {
            this.router.resetSession("http://localhost:10002");
          }
        }}
      />
      Agent
    </label>
          </div>
        </div>
        <div class="modules">
          ${this.showingTraditional ? html`<static-module></static-module>` : ''}
          ${this.showingChat ? html`<chat-module
            title="Chatbot LLM"
            subtitle="App using LLM to chat, chatbot-UI">
          </chat-module>` : ''}
          ${this.showingAgent ? html`
            <dynamic-module
              title="Dynamic agent"
              subtitle="App using agent cluster and A2UI events for dynamic UI">
            </dynamic-module>
            ` : ''}
        </div>
        <chat-input></chat-input>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "app-container": AppContainer
  }
}
