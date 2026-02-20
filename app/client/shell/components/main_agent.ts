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

// App elements.
import "../ui/ui.js";
import "./config_canvas.js"
import "./stat_bar.js";

// Register custom components
import { registerShellComponents } from "../ui/custom-components/register-components.js";
registerShellComponents();

// Configurations
import { AppConfig } from "../configs/types.js";
import { config as restaurantConfig } from "../configs/restaurant.js";
import { agentConfig } from "../configs/agent_config.js";

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
  accessor status: Array<{timestamp: string, message: string, type: string}> = [{timestamp: new Date().toISOString(), message: "Ready", type: "initial"}]

  @state()
  accessor #requesting = false;

  @state()
  accessor #error: string | null = null;

  @state()
  accessor #lastMessages: v0_8.Types.ServerToClientMessage[] = [];

  @state()
  accessor #loadingTextIndex = 0;

  @state()
  accessor #startTime: number | null = null;

  @state()
  accessor #elapsedTime: number | null = null;

  @state()
  accessor #currentElapsedTime: number | null = null;

  #processor = v0_8.Data.createSignalA2uiMessageProcessor();
  #loadingInterval: number | undefined;
  #stopwatchInterval: number | undefined;
  #snackbar: Snackbar | undefined = undefined;
  #pendingSnackbarMessages: Array<{
    message: SnackbarMessage;
    replaceAll: boolean;
  }> = [];

  static styles = [
    unsafeCSS(v0_8.Styles.structuralStyles),
    css`
      * {
        box-sizing: border-box;
      }

      :host {
        display: flex;
        flex-direction: column;
        flex: 1 1 0;
        min-width: 0;
        overflow: hidden;
        margin: 0;
        padding: 0.5rem;
        color: light-dark(var(--n-10), var(--n-90));
        font-family: var(--font-family);
        border-radius: 1rem;
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
        max-height: 300px;
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

      .surfaces-container {
        display: flex;
        flex-direction: column;
        height: 100%;
      }

      .surfaces {
        flex: 1;
        width: 100%;
        max-width: 100svw;
        padding: var(--bb-grid-size-3);
        padding-bottom: 32px;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
        overflow-y: auto;
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
      }

      .response-section {
        overflow: visible;
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

  connectedCallback() {
    super.connectedCallback();

    // Apply the theme directly, which will use the Lit context.
    if (this.config.theme) {
      this.theme = this.config.theme;
    }

    window.document.title = this.config.title;
    window.document.documentElement.style.setProperty(
      "--background",
      this.config.background
    );

    // Listen for streaming events from the router
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
          this.#startStopwatch();
        }
      });
    }
  }

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
    this.#stopStopwatch(); // Clear any existing timer
    this.#stopwatchInterval = window.setInterval(() => {
      if (this.#startTime && this.#elapsedTime === null) {
        this.#currentElapsedTime = Date.now() - this.#startTime;
        this.requestUpdate(); // Trigger re-render
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

  // TODO: this method should go on a separate router type, missing to update
  private updateStatusFromStreamingEvent(event: any) {
    // Only process events from this module's server URL
    if (event.serverUrl !== this.config.serverUrl) return;

    // status updates messages
    if (event.kind === 'status-update') {
      const status = event.status;
      const isFinal = event.final;
      const state = status?.state;
      const hasMessage = status?.message?.parts?.length > 0;

      // Actual part with status of server
      const serverState:Array<any> = hasMessage? event.status.message.parts : [{"text":"Server did not send any message parts"}];
      const serverMessage = serverState[0].text || "No text content"

      console.log("server message",serverState);

      if (state == 'failed'){
        this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Task failed - An error occurred", type: event.kind}]
      }else {
        this.status = [...this.status, {timestamp: new Date().toISOString(), message: serverMessage, type: event.kind}];
      }

      // Calculate elapsed time when final response is received
      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime;
        this.#stopStopwatch();
      }
    }
    else if (event.kind === 'task') {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Task management event received", type: event.kind}];
    }
    else if (event.kind === 'message') {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: "Direct message received", type: event.kind}];
    }
    else {
      this.status = [...this.status, {timestamp: new Date().toISOString(), message: `Event type: ${event.kind || 'unknown'}`, type: event.kind}];
    }
  }

  private processMessages(event: any) {
    // Only process events from this module's server URL
    if (event.serverUrl !== this.config.serverUrl) return;

    // Check if this event contains A2UI messages
    if (event.kind === "status-update" && event.status?.message?.parts) {
      const newMessages: v0_8.Types.ServerToClientMessage[] = [];
      for (const part of event.status.message.parts) {
        if (part.kind === 'data') {
          const data = part.data;
          if (Array.isArray(data)) {
            // Proper A2UI format: array of messages
            newMessages.push(...data);
          } else {
            // Single message format (temporary compatibility)
            newMessages.push(data);
          }
        }
      }
      // Replace with latest messages, not accumulate
      if (newMessages.length > 0) {
        this.#lastMessages = newMessages;
        this.#processor.clearSurfaces();
        this.#processor.processMessages(this.#lastMessages);
      }
    }
  }

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

  render() {
    return html`
      <style>
        :host {
          background: ${this.color};
        }
      </style>
      <stat-bar
        .title=${this.title}
        .time=${(this.#elapsedTime !== null || this.#currentElapsedTime !== null) ? `${((this.#elapsedTime || this.#currentElapsedTime || 0) / 1000).toFixed(2)}s` : '0.00s'}
        .tokens=${'12456'}
        .configUrl=${this.config.serverUrl + '/config'}
        .configType=${'agent'}
        .configData=${agentConfig}
      ></stat-bar>
      ${this.#maybeRenderError()}
      ${this.#maybeRenderData()}
      ${this.#renderStatusWindow()}
    `;
  }



  #maybeRenderError() {
    if (!this.#error) return nothing;

    return html`<div class="error">${this.#error}</div>`;
  }

  #maybeRenderData() {
    if (this.#requesting) {
      let text = "Awaiting an answer...";
      if (this.config.loadingText) {
        if (Array.isArray(this.config.loadingText)) {
          text = this.config.loadingText[this.#loadingTextIndex];
        } else {
          text = this.config.loadingText;
        }
      }

      return html`
        <div class="pending">
          <div class="spinner"></div>
          <div class="loading-text">${text}</div>
        </div>
      `;
    }

    // Render A2UI surfaces
    const surfaces = this.#processor.getSurfaces();
    if (surfaces.size === 0) {
      return html`<div class="response-section">
        <div class="response">Ready to process A2UI messages...</div>
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
                  if (item.value.literalBoolean) {
                    context[item.key] = item.value.literalBoolean;
                  } else if (item.value.literalNumber) {
                    context[item.key] = item.value.literalNumber;
                  } else if (item.value.literalString) {
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

              // Send action back via router
              if (this.router) {
                this.#requesting = true;
                this.#startLoadingAnimation();
                try {
                  await this.router.sendA2UIMessage(this.config.serverUrl || "http://localhost:10002", message);
                } catch (err) {
                  this.snackbar(err as string, SnackType.ERROR);
                } finally {
                  this.#requesting = false;
                  this.#stopLoadingAnimation();
                }
              }
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
    return html`<div class="status-section">
        <div class="status">
          ${repeat(
            this.status,
            (item) => item.timestamp,
            (item) => html`<div class="status-item">
              ${new Date(item.timestamp).toLocaleTimeString()} - ${item.message}
            </div>`
          )}
        </div>
      </div>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "dynamic-module": DynamicModule
  }
}
