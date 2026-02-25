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
      margin: var(--space-sm);
    }

    .stat-bar {
      display: flex;
      flex-direction: row;
      gap: var(--space-xs);
      align-items: center;
    }

    .title {
      font-size: var(--font-size-xl);
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
      /* Additional styling if needed */
    }
  `;

  render() {
    return html`
      <div class="stat-bar">
        ${this.time ? html`<div class="time">${this.time}</div>` : ''}
        ${this.tokens ? html`<div class="tokens">TC: ${this.tokens}</div>` : ''}
        ${this.configUrl ? html`<div class="config"><agent-config-canvas .serverURL=${this.configUrl} .configType=${this.configType} .configData=${this.configData}></agent-config-canvas></div>` : ''}
        <div class="title">${this.title}</div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "stat-bar": StatBar;
  }
}