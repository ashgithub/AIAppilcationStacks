import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import { AppConfigType, ConfigData } from "../configs/types.js";

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
    :host {
      display: block;
      margin: 0.5rem;
    }

    .stat-bar {
      display: flex;
      flex-direction: row;
      gap: 0.2rem;
      align-items: center;
    }

    .title {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }

    .time {
      font-size: 0.875rem;
      font-weight: 500;
      padding: 0.5rem;
      background: #1a2332;
      border-radius: 0.25rem;
      color: white;
    }

    .tokens {
      font-size: 0.875rem;
      font-weight: 500;
      padding: 0.5rem;
      background: #1a2332;
      border-radius: 0.25rem;
      color: white;
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