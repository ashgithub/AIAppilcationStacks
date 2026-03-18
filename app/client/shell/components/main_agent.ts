import { provide } from "@lit/context";
import { consume } from "@lit/context";
import {
  LitElement,
  html,
  css,
  nothing,
  HTMLTemplateResult,
  unsafeCSS,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { theme as uiTheme } from "../theme/default-theme.js";
import { designTokensCSS, colors, radius, spacing } from "../theme/design-tokens.js";
import { A2UIRouter, routerContext } from "../services/a2ui-router.js";
import {
  SnackbarAction,
  SnackbarMessage,
  SnackbarUUID,
  SnackType,
} from "../types/types.js";
import { type Snackbar } from "../ui/snackbar.js";
import { repeat } from "lit/directives/repeat.js";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";

import "../ui/ui.js";
import "./config_canvas.js"
import "./stat_bar.js";
import "./status_drawer.js";

import { registerShellComponents } from "../ui/custom-components/register-components.js";
registerShellComponents();

import { AppConfig } from "../configs/types.js";
import { config as restaurantConfig } from "../configs/restaurant.js";
import { agentConfig } from "../configs/agent_config.js";

// #region Component
@customElement("dynamic-module")
export class DynamicModule extends LitElement {
  @provide({ context: UI.Context.themeContext })
  accessor theme: v0_8.Types.Theme = uiTheme;

  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @property({ type: String })
  accessor title = ""

  @property({ type: String })
  accessor subtitle = ""

  @property({ type: String })
  accessor color = "#334155"

  @property({ type: Object })
  accessor config: AppConfig = restaurantConfig;

  @state()
  accessor response = ""

  @state()
  accessor status: Array<{ timestamp: number, duration: number, message: string, type: string }> = [{ timestamp: Date.now(), duration: 0, message: "Ready", type: "initial" }]

  @state()
  accessor suggestions = ""

  @state()
  accessor tokenCount = ""

  @state()
  accessor sources: string[] = []

  @state()
  accessor #lastUserQuestion: string = "";

  @state()
  accessor #requesting = false;

  @state()
  accessor #error: string | null = null;

  @state()
  accessor #lastMessages: v0_8.Types.ServerToClientMessage[] = [];

  @state()
  accessor #processingSurfaces = false;

  @state()
  accessor #loadingTextIndex = 0;

  @state()
  accessor #startTime: number | null = null;

  @state()
  accessor #elapsedTime: number | null = null;

  @state()
  accessor #currentElapsedTime: number | null = null;

  @state()
  accessor #totalDuration: number = 0;

  // #region Internal Services
  #processor = v0_8.Data.createSignalA2uiMessageProcessor();
  #loadingInterval: number | undefined;
  #stopwatchInterval: number | undefined;
  #snackbar: Snackbar | undefined = undefined;
  #pendingSnackbarMessages: Array<{
    message: SnackbarMessage;
    replaceAll: boolean;
  }> = [];
  // #endregion Internal Services

  // #region Styles
  static styles = [
    unsafeCSS(v0_8.Styles.structuralStyles),
    css`
      ${designTokensCSS}

      * {
        box-sizing: border-box;
      }

      :host {
        --conversation-max-height: min(130vh, 1680px);
        display: flex;
        flex-direction: column;
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        margin: 0;
        padding: var(--space-sm);
        color: var(--text-primary);
        font-family: var(--font-family);
        border-radius: var(--radius-xl);
        background: var(--module-agent-bg);
      }

      .subtitle {
        font-size: var(--font-size-base);
        margin-bottom: var(--space-lg);
        opacity: 0.9;
      }

      .response {
        flex: 1 1 auto;
        min-height: 100px;
        max-height: var(--conversation-max-height);
        font-size: var(--font-size-base);
        line-height: 1.6;
        margin-bottom: var(--space-sm);
        padding: var(--space-md);
        background: rgba(0, 0, 0, 0.2);
        border-radius: var(--radius-md);
        overflow-y: auto;
        overflow-x: hidden;
      }
      
      .user-question {
        align-self: flex-end;
        background: var(--module-agent-active);
        border: 1px solid var(--agent-accent);
        border-bottom-right-radius: var(--radius-sm);
        padding: var(--space-sm) var(--space-md);
        margin-bottom: var(--space-sm);
        border-radius: var(--radius-lg);
      }

      .user-question-label {
        font-size: var(--font-size-xs);
        opacity: 0.7;
        text-transform: uppercase;
        margin-bottom: var(--space-xs);
      }

      .user-question-text {
        font-size: var(--font-size-base);
        line-height: 1.4;
      }

      .surfaces-container {
        display: flex;
        flex-direction: column;
        flex: 0 1 auto;
        min-height: 0;
        overflow: visible;
        max-height: none;
      }
        
      .surfaces {
        flex: 0 1 auto;
        width: 100%;
        max-width: 100svw;
        padding: var(--bb-grid-size-3);
        padding-bottom: 32px;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
        overflow-y: auto;
        overflow-x: hidden;
        max-height: var(--conversation-max-height);
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
        border-left-color: var(--agent-accent);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .error {
        flex-shrink: 0;
        color: var(--e-40);
        background-color: var(--e-95);
        border: 1px solid var(--e-80);
        padding: 16px;
        border-radius: 8px;
      }

      .title-section,
      .status-section {
        flex-shrink: 0;
        min-height: fit-content;
      }

      .suggestions {
      flex-shrink: 0;
      font-size: var(--font-size-sm);
      padding: var(--space-md);
      margin-bottom: var(--space-sm);
      background: none;
    }

    .suggestions-list {
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }

    .suggestion-item {
      padding: var(--space-sm) var(--space-md);
      background: var(--module-agent-active);
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: background var(--transition-normal), transform var(--transition-fast), border-color var(--transition-normal);
      border: 1px solid transparent;
    }

    .suggestion-item:hover {
      background: rgba(64, 196, 179, 0.25);
      border-color: var(--agent-accent);
      transform: translateX(4px);
    }

    .suggestion-item:active {
      transform: scale(0.98);
    }

    .sources-floating {
      flex-shrink: 0;
      margin: 0 var(--space-md) var(--space-sm);
      font-size: var(--font-size-xs);
      line-height: 1.5;
      color: var(--text-secondary);
      background: transparent;
      padding: 0.5rem;
    }

    .sources-floating strong {
      color: var(--text-primary);
      margin-right: var(--space-xs);
    }

    .source-link {
      color: var(--agent-accent);
      text-decoration: underline;
      text-underline-offset: 2px;
      word-break: break-word;
    }

    .source-link:hover {
      color: var(--text-primary);
    }

      .response-section {
        flex: 0 1 auto;
        overflow: visible;
        min-height: 0;
        max-height: none;
      }

      .pending {
        min-height: 200px;
        overflow: visible;
      }

      .surfaces-container {
        overflow: visible;
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
    `,
  ]
  // #endregion Styles

  // #region Lifecycle
  connectedCallback() {
    super.connectedCallback();

    if (this.config.theme) {
      this.theme = this.config.theme;
    }

    window.document.title = this.config.title;
    window.document.documentElement.style.setProperty(
      "--background",
      this.config.background
    );

    if (this.router) {
      this.router.addEventListener('streaming-event', (event: any) => {
        const streamingEvent = event.detail;
        this.updateStatusFromStreamingEvent(streamingEvent);
        this.processMessages(streamingEvent);
      });

      this.router.addEventListener('message-sent', (event: any) => {
        const sentEvent = event.detail;
        if (sentEvent.serverUrl === this.config.serverUrl) {
          this.#startTime = sentEvent.timestamp;
          this.#elapsedTime = null;
          this.#currentElapsedTime = 0;
          this.#totalDuration = 0;
          this.#requesting = true;
          this.#error = null;
          this.sources = [];
          this.#startLoadingAnimation();
          this.#lastUserQuestion = sentEvent.message || '';
          console.log("Query sent on agent")
          this.status = []
          this.#startStopwatch();
        }
      });
    }
  }
  // #endregion Lifecycle

  // #region Loading State
  #startLoadingAnimation() {
    if (
      Array.isArray(this.config.loadingText) &&
      this.config.loadingText.length > 1
    ) {
      this.#loadingTextIndex = 0;
      this.#loadingInterval = window.setInterval(() => {
        this.#loadingTextIndex =
          (this.#loadingTextIndex + 1) %
          (this.config.loadingText as string[]).length;
      }, 2000);
    }
  }

  #stopLoadingAnimation() {
    if (this.#loadingInterval) {
      clearInterval(this.#loadingInterval);
      this.#loadingInterval = undefined;
    }
  }

  #startStopwatch() {
    this.#stopStopwatch();
    this.#stopwatchInterval = window.setInterval(() => {
      if (this.#startTime && this.#elapsedTime === null) {
        this.#currentElapsedTime = Date.now() - this.#startTime;
        this.requestUpdate();
      }
    }, 100);
  }

  #stopStopwatch() {
    if (this.#stopwatchInterval) {
      clearInterval(this.#stopwatchInterval);
      this.#stopwatchInterval = undefined;
    }
    this.#currentElapsedTime = null;
  }
  // #endregion Loading State

  // #region Streaming - Parsing
  // TODO: move this mapping logic into a typed router helper.
  private updateStatusFromStreamingEvent(event: any) {
    if (event.serverUrl !== this.config.serverUrl) return;

    if (event.kind === 'status-update') {
      const status = event.status;
      const isFinal = event.final;
      const state = status?.state;
      const hasMessage = status?.message?.parts?.length > 0;

      const serverState: Array<any> = hasMessage ? event.status.message.parts : [{ "text": "Server did not send any message parts" }];
      const serverMessage = serverState[0].text || "No text content"

      console.log("server message", serverState);

      if (isFinal) {
        const textParts = serverState
          .filter((part: any) => part.kind === "text")
          .map((part: any) => part.text);
        const metadataTail = textParts.slice(-4);

        if (metadataTail[1]) {
          this.tokenCount = metadataTail[1];
        }

        if (metadataTail[2]) {
          this.suggestions = metadataTail[2];
        }

        this.sources = this.#parseSources(metadataTail[3] || "[]");
      }

      if (state == 'failed') {
        this.#addStatusWithDuration("Task failed - An error occurred", event.kind);
      } else {
        if (!isFinal) {
          this.#addStatusWithDuration(serverMessage, event.kind);
        }
      }

      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime;
        this.#stopStopwatch();
      }

      if (isFinal || state === 'failed') {
        this.#requesting = false;
        this.#stopLoadingAnimation();
      }
    }
    else if (event.kind === 'task') {
      console.log("Task management event received")
    }
    else if (event.kind === 'message') {
      this.#addStatusWithDuration("Direct message received", event.kind);
    }
    else {
      this.#addStatusWithDuration(`Event type: ${event.kind || 'unknown'}`, event.kind);
    }
  }
  // Compute step duration from the previous status timestamp.
  #addStatusWithDuration(message: string, type: string) {
    const now = Date.now();
    const lastStatus = this.status[this.status.length - 1];
    const duration = lastStatus ? (now - lastStatus.timestamp) / 1000 : 0;

    if (lastStatus && lastStatus.message === message && lastStatus.type === type) {
      return;
    }

    this.status = [...this.status, {
      timestamp: now,
      duration: duration,
      message,
      type
    }];

    if (this.#startTime) {
      this.#totalDuration = (now - this.#startTime) / 1000;
    }
  }

  // Accept JSON suggestions or plain text split by newline/comma.
  #parseSuggestions(suggestionsText: string): string[] {
    try {
      const parsed = JSON.parse(suggestionsText);
      if (parsed && Array.isArray(parsed.suggested_questions)) {
        return parsed.suggested_questions;
      }
    } catch {
      let suggestions = suggestionsText
        .split(/\n/)
        .map(s => s.trim())
        .filter(s => s.length > 0);

      if (suggestions.length === 1) {
        suggestions = suggestions[0]
          .split(/[,;]/)
          .map(s => s.trim())
          .filter(s => s.length > 0);
      }

      return suggestions.map(s => s.replace(/^(\d+[\.\)]\s*|[-Ã¢â‚¬Â¢]\s*)/, '').trim());
    }

    return [];
  }

  async #handleSuggestionClick(suggestion: string) {
    if (!this.router || !suggestion.trim()) return;

    console.log("Sending suggestion as query:", suggestion);
    try {
      this.suggestions = "";
      this.sources = [];
      this.router.sendTextMessage(this.config.serverUrl, suggestion.trim());
    } catch (error) {
      console.error("Failed to send suggestion:", error);
    }
  }

  private processMessages(event: any) {
    if (event.serverUrl !== this.config.serverUrl) return;

    if (event.kind === "status-update" && event.status?.message?.parts) {
      const newMessages: v0_8.Types.ServerToClientMessage[] = [];
      for (const part of event.status.message.parts) {
        if (part.kind === 'data') {
          const data = part.data;
          if (Array.isArray(data)) {
            newMessages.push(...data);
          } else {
            newMessages.push(data);
          }
        }
      }

      if (newMessages.length > 0) {
        this.#processingSurfaces = true;
        this.#startLoadingAnimation();
        this.#lastMessages = newMessages;
        this.#processor.clearSurfaces();
        this.#processor.processMessages(this.#lastMessages);
        this.#stopLoadingAnimation();
        this.#processingSurfaces = false;
      }
    }
  }
  // #endregion Streaming And Parsing

  // #region Notifications
  snackbar(
    message: string | HTMLTemplateResult,
    type: SnackType,
    actions: SnackbarAction[] = [],
    persistent = false,
    id = globalThis.crypto.randomUUID(),
    replaceAll = false
  ) {
    if (!this.#snackbar) {
      this.#pendingSnackbarMessages.push({
        message: {
          id,
          message,
          type,
          persistent,
          actions,
        },
        replaceAll,
      });
      return;
    }

    return this.#snackbar.show(
      {
        id,
        message,
        type,
        persistent,
        actions,
      },
      replaceAll
    );
  }

  unsnackbar(id?: SnackbarUUID) {
    if (!this.#snackbar) {
      return;
    }

    this.#snackbar.hide(id);
  }
  // #endregion Notifications

  // #region Render
  render() {
    return html`
      <stat-bar
        .title=${this.title}
        .time=${this.#totalDuration > 0 ? `${this.#totalDuration.toFixed(2)}s` : ((this.#currentElapsedTime !== null) ? `${(this.#currentElapsedTime / 1000).toFixed(2)}s` : '0.00s')}
        .tokens=${this.tokenCount ? `${this.tokenCount}`: '0'}
        .configUrl=${this.config.serverUrl + '/config'}
        .configType=${'agent'}
        .configData=${agentConfig}
      ></stat-bar>
      ${this.#lastUserQuestion ? html`
        <div class="user-question">
          <div class="user-question-label">You</div>
          <div class="user-question-text">${this.#lastUserQuestion}</div>
        </div>
      ` : ''}
      ${this.#maybeRenderError()}
      ${this.#maybeRenderData()}
      ${this.sources.length > 0 ? html`
        <div class="sources-floating">
          <strong>Sources:</strong>
          ${this.sources.map((source, index) => html`
            <a
              class="source-link"
              href=${this.#getSourceUrl(source)}
              target="_blank"
              rel="noopener noreferrer"
              title=${`Open source document: ${source}`}
            >${source}</a>${index < this.sources.length - 1 ? ", " : ""}
          `)}
        </div>
      ` : ''}
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
      ${this.#renderStatusWindow()}
    `;
  }



  #maybeRenderError() {
    if (!this.#error) return nothing;

    return html`<div class="error">${this.#error}</div>`;
  }

  #parseSources(sourcesText: string): string[] {
    if (!sourcesText || !sourcesText.trim()) {
      return [];
    }

    try {
      const parsed = JSON.parse(sourcesText);
      if (Array.isArray(parsed)) {
        return [...new Set(parsed.map((s) => String(s).trim()).filter((s) => s.length > 0))];
      }
      return [];
    } catch {
      return sourcesText
        .replace(/^\[|\]$/g, "")
        .split(",")
        .map((s) => s.replace(/^["'\s]+|["'\s]+$/g, "").trim())
        .filter((s) => s.length > 0);
    }
  }

  #getSourceUrl(source: string): string {
    const sourceFile = source.split(/[\\/]/).pop()?.trim() || source.trim();

    try {
      const serverBase = new URL(this.config.serverUrl || window.location.origin);
      return `${serverBase.origin}/rag_docs/${encodeURIComponent(sourceFile)}`;
    } catch {
      return `/rag_docs/${encodeURIComponent(sourceFile)}`;
    }
  }

  #getCurrentLoadingText(defaultText: string) {
    const latestStatusText = this.status[this.status.length - 1]?.message;
    if (typeof latestStatusText === "string" && latestStatusText.trim().length > 0) {
      return latestStatusText;
    }

    if (this.config.loadingText) {
      if (Array.isArray(this.config.loadingText)) {
        return this.config.loadingText[this.#loadingTextIndex];
      }
      return this.config.loadingText;
    }

    return defaultText;
  }

  #maybeRenderData() {
    if (this.#requesting) {
      const text = this.#getCurrentLoadingText("Awaiting an answer...");

      return html`
        <div class="pending">
          <div class="spinner"></div>
          <div class="loading-text">${text}</div>
        </div>
      `;
    }

    // Keep a loading state while a new surface tree is being applied.
    if (this.#processingSurfaces) {
      const text = this.#getCurrentLoadingText("Updating interface...");

      return html`
        <div class="surfaces-container">
          <div class="pending">
            <div class="spinner"></div>
            <div class="loading-text">${text}</div>
          </div>
        </div>
      `;
    }

    const surfaces = this.#processor.getSurfaces();
    if (surfaces.size === 0) {
      return html`<div class="response-section">
        <div class="response">Start a conversation by typing a message below...</div>
      </div>`;
    }

    return html`<div class="surfaces-container">
      <section class="surfaces">
        ${repeat(
      this.#processor.getSurfaces(),
      ([surfaceId]) => surfaceId,
      ([surfaceId, surface]) => {
        return html`<a2ui-surface
                @a2uiaction=${async (
          evt: v0_8.Events.StateEvent<"a2ui.action">
        ) => {
            const [target] = evt.composedPath();
            if (!(target instanceof HTMLElement)) {
              return;
            }

            const context: v0_8.Types.A2UIClientEventMessage["userAction"]["context"] =
              {};
            if (evt.detail.action.context) {
              const srcContext = evt.detail.action.context;
              for (const item of srcContext) {
                if (item.value.literalBoolean !== undefined) {
                  context[item.key] = item.value.literalBoolean;
                } else if (item.value.literalNumber !== undefined) {
                  context[item.key] = item.value.literalNumber;
                } else if (item.value.literalString !== undefined) {
                  context[item.key] = item.value.literalString;
                } else if (item.value.path) {
                  const path = this.#processor.resolvePath(
                    item.value.path,
                    evt.detail.dataContextPath
                  );
                  const value = this.#processor.getData(
                    evt.detail.sourceComponent,
                    path,
                    surfaceId
                  );
                  context[item.key] = value;
                }
              }
            }

            const message: v0_8.Types.A2UIClientEventMessage = {
              userAction: {
                name: evt.detail.action.name,
                surfaceId,
                sourceComponentId: target.id,
                timestamp: new Date().toISOString(),
                context,
              },
            };

            await this.#sendUserActionMessage(message);
          }}
                .surfaceId=${surfaceId}
                .surface=${surface}
                .processor=${this.#processor}
                .enableCustomElements=${true}
              ></a2-uisurface>`;
      }
    )}
      </section>
    </div>`;
  }

  #renderStatusWindow() {
    return html`<status-drawer .items=${this.status} accentColor="var(--agent-accent)"></status-drawer>`;
  }
  // #endregion Render

  // #region Actions
  async #sendUserActionMessage(message: v0_8.Types.A2UIClientEventMessage) {
    if (!this.router) return;
    try {
      await this.router.sendA2UIMessage(
        this.config.serverUrl || "http://localhost:10002",
        message
      );
    } catch (err) {
      this.#requesting = false;
      this.#stopLoadingAnimation();
      this.snackbar(err as string, SnackType.ERROR);
    }
  }
  // #endregion Actions
}
// #endregion Component

// #region Element Registration
declare global {
  interface HTMLElementTagNameMap {
    "dynamic-module": DynamicModule
  }
}
// #endregion Element Registration


