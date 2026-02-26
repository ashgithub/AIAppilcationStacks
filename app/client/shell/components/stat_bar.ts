import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import { AppConfigType, ConfigData } from "../configs/types.js";
import { designTokensCSS } from "../theme/design-tokens.js";

// Import the config canvas component
import "./config_canvas.js";

@customElement("stat-bar")
export class StatBar extends LitElement {
  @property({ type: String })
  accessor title = "";

  @property({ type: String })
  accessor time = "";

  @property({ type: String })
  accessor tokens = "";

  @property({ type: String })
  accessor configUrl = "";

  @property({ type: String })
  accessor configType: AppConfigType = 'agent';

  @property({ type: Object })
  accessor configData: ConfigData = {};

  static styles = css`
    ${designTokensCSS}

    :host {
      display: block;
      margin: var(--space-none);
    }

    .stat-bar {
      display: flex;
      flex-direction: row;
      gap: var(--space-xs);
      align-items: center;
    }

    .status-data{
      display: flex;
      flex-direction: row;
      gap: var(--space-xs);
      align-items: center;
    }

    .title {
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-semibold);
      margin: 0;
    }

    .time {
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      padding: var(--space-sm);
      background: var(--agent-bg);
      border-radius: var(--radius-sm);
      color: var(--text-primary);
    }

    .tokens {
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      padding: var(--space-sm);
      background: var(--agent-bg);
      border-radius: var(--radius-sm);
      color: var(--text-primary);
    }

    .config {
      font-size: var(--font-size-sm);
      padding: var(--space-none);
      background: var(--agent-bg);
      border-radius: var(--radius-sm);
    }
  `;

  render() {
    return html`
      <div class="stat-bar">
      <div class="title">${this.title}</div>
      <div class="status-data">
        ${this.time ? html`<div class="time">🕐 ${this.time}</div>` : ''}
        ${this.tokens ? html`<div class="tokens">🎟️ ${this.tokens} tokens</div>` : ''}
        ${this.configUrl ? html`<div class="config"><agent-config-canvas .serverURL=${this.configUrl} .configType=${this.configType} .configData=${this.configData}></agent-config-canvas></div>` : ''}
      </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "stat-bar": StatBar;
  }
}