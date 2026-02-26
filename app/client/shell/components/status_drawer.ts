import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";
import { designTokensCSS } from "../theme/design-tokens.js";

export interface StatusItem {
  timestamp: number;
  duration: number;
  message: string;
  type: string;
}

@customElement("status-drawer")
export class StatusDrawer extends LitElement {
  @property({ type: Array })
  accessor items: StatusItem[] = [];

  @property({ type: String })
  accessor accentColor: string = "var(--agent-accent)";

  @state()
  accessor expanded = false;

  static styles = css`
    ${designTokensCSS}

    :host {
      display: block;
      margin-top: auto;
    }

    .drawer {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .drawer-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--space-sm) var(--space-md);
      cursor: pointer;
      user-select: none;
      transition: background 0.2s ease;
    }

    .drawer-header:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    .drawer-title {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--text-secondary);
    }

    .drawer-title .icon {
      font-size: var(--font-size-base);
    }

    .drawer-info {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .log-count {
      font-size: var(--font-size-xs);
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.1);
      padding: var(--space-xs) var(--space-sm);
      border-radius: var(--radius-sm);
    }

    .expand-icon {
      font-size: var(--font-size-sm);
      color: var(--text-secondary);
      transition: transform 0.3s ease;
    }

    .expand-icon.expanded {
      transform: rotate(180deg);
    }

    .drawer-content {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }

    .drawer-content.expanded {
      max-height: 200px;
      overflow-y: auto;
    }

    .status-list {
      padding: 0 var(--space-md) var(--space-md);
    }

    .status-item {
      padding: var(--space-xs) 0;
      border-bottom: 1px solid var(--border-subtle);
      font-size: var(--font-size-xs);
      line-height: 1.4;
      display: flex;
      gap: var(--space-sm);
      color: var(--text-secondary);
    }

    .status-item:last-child {
      border-bottom: none;
    }

    .status-item .duration {
      font-weight: var(--font-weight-bold);
      color: var(--text-primary);
      min-width: 3.5rem;
      text-align: right;
      flex-shrink: 0;
    }

    .status-item .message {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Latest status indicator when collapsed */
    .latest-status {
      font-size: var(--font-size-xs);
      color: var(--text-muted);
      max-width: 200px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `;

  private toggle() {
    this.expanded = !this.expanded;
  }

  render() {
    const latestStatus = this.items.length > 0 ? this.items[this.items.length - 1] : null;

    return html`
      <div class="drawer">
        <div class="drawer-header" @click=${this.toggle}>
          <div class="drawer-title">
            <span>Logs</span>
          </div>
          <div class="drawer-info">
            ${!this.expanded && latestStatus ? html`
              <span class="latest-status">${latestStatus.message}</span>
            ` : ''}
            <span class="log-count">${this.items.length} ${this.items.length === 1 ? 'entry' : 'entries'}</span>
            <span class="expand-icon ${this.expanded ? 'expanded' : ''}">▲</span>
          </div>
        </div>
        <div class="drawer-content ${this.expanded ? 'expanded' : ''}">
          <div class="status-list">
            ${repeat(
              this.items,
              (item) => item.timestamp,
              (item) => html`
                <div class="status-item">
                  <span class="duration">${item.duration.toFixed(2)}s</span>
                  <span class="message">${item.message}</span>
                </div>
              `
            )}
          </div>
        </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "status-drawer": StatusDrawer;
  }
}
