import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { provide } from "@lit/context"
import { a2uiRouter, routerContext } from "./services/a2ui-router.js"
import { designTokensCSS, buttonStyles, colors, radius, spacing } from "./theme/design-tokens.js"
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
    ${buttonStyles}

    :host {
      display: flex;
      flex-direction: column;
      width: 100%;
      min-height: 100vh;
      background: var(--agent-bg);
      font-family: var(--font-family);
      overflow-x: hidden;
      box-sizing: border-box;
    }

    .container {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      padding: var(--space-sm);
      gap: var(--space-sm);
      box-sizing: border-box;
    }

    @media (max-width: 1200px) {
      .container {
        padding: var(--space-xs);
      }

      .modules {
        gap: var(--space-md);
      }
    }

    @media (max-width: 768px) {
      .container {
        padding: 2px;
      }

      .modules {
        gap: var(--space-sm);
      }
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-normal);
      margin: 0;
      padding: 0;
    }

    .header h3 {
      color: var(--text-primary);
      margin: 0;
    }

    .oracle-text {
      color: var(--color-error);
      letter-spacing: 0.2em;
    }

    .controls {
      display: flex;
      gap: var(--space-md);
      align-items: center;
    }

    .control {
      display: flex;
      align-items: center;
      gap: var(--space-xs);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      cursor: pointer;
      user-select: none;
    }

    .control input {
      display: none;
    }

    .toggle-switch {
      position: relative;
      width: 36px;
      height: 20px;
      background: var(--neutral-600);
      border-radius: 10px;
      transition: background 0.2s ease;
    }

    .toggle-switch::after {
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      width: 16px;
      height: 16px;
      background: var(--neutral-white);
      border-radius: 50%;
      transition: transform 0.2s ease;
    }

    .control input:checked + .toggle-switch {
      background: var(--color-success);
    }

    .control input:checked + .toggle-switch::after {
      transform: translateX(16px);
    }

    .control:hover .toggle-switch {
      opacity: 0.9;
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
          <h3><span class="oracle-text">ORACLE</span> Innovation Lab</h3>
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
              <span class="toggle-switch"></span>
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
              <span class="toggle-switch"></span>
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
              <span class="toggle-switch"></span>
              Agent
            </label>
          </div>
          <div class="extra-data">
            <button class="btn btn-secondary">Feedback</button>
            <button class="btn btn-secondary">View Comparison</button>
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
