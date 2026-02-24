import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { provide } from "@lit/context"
import { a2uiRouter, routerContext } from "./services/a2ui-router.js"
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
    :host {
      display: flex;
      flex-direction: column;
      width: 100%;
      min-height: 100vh;
      background: #1a2332;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .container {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      padding: 0.5rem;
      gap: 0.5rem;
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: white;
      font-size: 1rem;
      font-weight: 300;
      margin-bottom: 0rem;
    }

    .controls {
      display: flex;
      gap: 1rem;
      align-items: center;
    }

    .control {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: white;
      font-size: 1rem;
    }

    .modules {
      display: flex;
      flex-wrap: nowrap;
      gap: 1.5rem;
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
                @change=${(e: Event) => this.showingTraditional = (e.target as HTMLInputElement).checked}
              />
              Traditional
            </label>
            <label class="control">
              <input
                type="checkbox"
                .checked=${this.showingChat}
                @change=${(e: Event) => this.showingChat = (e.target as HTMLInputElement).checked}
              />
              Chat
            </label>
            <label class="control">
              <input
                type="checkbox"
                .checked=${this.showingAgent}
                @change=${(e: Event) => this.showingAgent = (e.target as HTMLInputElement).checked}
              />
              Agent
            </label>
          </div>
        </div>
        <div class="modules">
          ${this.showingTraditional ? html`<static-module></static-module>` : ''}
          ${this.showingChat ? html`<chat-module
            title="Chatbot LLM"
            subtitle="App using LLM to chat, chatbot-UI"
            color="#717af8">
          </chat-module>` : ''}
          ${this.showingAgent ? html`
            <dynamic-module
              title="Dynamic agent"
              subtitle="App using agent cluster and A2UI events for dynamic UI"
              color="#3c5d8b">
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
