import { html, css, LitElement } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { designTokensCSS } from "../../theme/design-tokens.js";

// Reusable details viewer used by interactive components.
@customElement('detail-modal')
export class DetailModal extends LitElement {
  @property({ type: Boolean }) accessor open = false;
  @property({ type: String }) accessor title = "Details";
  @property({ type: String }) accessor position: 'modal' | 'panel' | 'inline' = 'modal';
  @property({ attribute: false }) accessor data: Record<string, any> = {};
  @property({ attribute: false }) accessor fields: Array<{key: string, label: string, type?: string}> = [];

  static styles = [
    designTokensCSS,
    css`
      :host {
        font-family: var(--font-family);
      }

      /* Modal overlay */
      .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        opacity: 0;
        visibility: hidden;
        transition: opacity var(--transition-normal), visibility var(--transition-normal);
      }

      .modal-overlay.open {
        opacity: 1;
        visibility: visible;
      }

      .modal-content {
        background: var(--surface-primary);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-glow);
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow: hidden;
        transform: scale(0.9) translateY(20px);
        transition: transform var(--transition-normal);
      }

      .modal-overlay.open .modal-content {
        transform: scale(1) translateY(0);
      }

      /* Inline panel variant */
      .inline-panel {
        background: var(--surface-secondary);
        border-radius: var(--radius-md);
        padding: var(--space-md);
        margin-top: var(--space-sm);
        border: 1px solid var(--border-primary);
        max-height: 0;
        overflow: hidden;
        opacity: 0;
        transition: max-height 0.3s ease, opacity 0.2s ease, padding 0.3s ease, margin 0.3s ease;
      }

      .inline-panel.open {
        max-height: 500px;
        opacity: 1;
        padding: var(--space-md);
        margin-top: var(--space-sm);
      }

      /* Side panel variant */
      .side-panel {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        width: 400px;
        max-width: 90vw;
        background: var(--surface-primary);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        transform: translateX(100%);
        transition: transform var(--transition-normal);
        overflow-y: auto;
      }

      .side-panel.open {
        transform: translateX(0);
      }

      .side-panel-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.3);
        z-index: 999;
        opacity: 0;
        visibility: hidden;
        transition: opacity var(--transition-normal), visibility var(--transition-normal);
      }

      .side-panel-overlay.open {
        opacity: 1;
        visibility: visible;
      }

      /* Header */
      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--space-md) var(--space-lg);
        border-bottom: 1px solid var(--border-primary);
        background: var(--surface-secondary);
      }

      .modal-title {
        font-size: 18px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin: 0;
      }

      .close-btn {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: var(--space-xs);
        border-radius: var(--radius-sm);
        font-size: 20px;
        line-height: 1;
        transition: all var(--transition-normal);
      }

      .close-btn:hover {
        background: var(--hover-overlay);
        color: var(--text-primary);
      }

      /* Body */
      .modal-body {
        padding: var(--space-lg);
        overflow-y: auto;
        max-height: 60vh;
      }

      .inline-panel .modal-body {
        padding: 0;
        max-height: none;
      }

      .detail-grid {
        display: grid;
        gap: var(--space-md);
      }

      .detail-item {
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
      }

      .detail-label {
        font-size: 11px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .detail-value {
        font-size: 14px;
        color: var(--text-primary);
        line-height: 1.5;
      }

      .detail-value.number {
        font-weight: var(--font-weight-semibold);
        color: var(--oracle-primary);
      }

      .detail-value.status {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: var(--radius-xl);
        font-size: 12px;
        font-weight: var(--font-weight-semibold);
        text-transform: uppercase;
        width: fit-content;
      }

      .detail-value.status.active {
        background: rgba(239, 68, 68, 0.15);
        color: var(--color-error);
      }

      .detail-value.status.resolved {
        background: rgba(16, 185, 129, 0.15);
        color: var(--color-success);
      }

      .detail-value.status.pending,
      .detail-value.status.investigating {
        background: rgba(245, 158, 11, 0.15);
        color: var(--color-warning);
      }

      /* Inline header */
      .inline-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--space-sm);
        padding-bottom: var(--space-sm);
        border-bottom: 1px solid var(--border-subtle);
      }

      .inline-title {
        font-size: 14px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
      }
    `,
  ];

  render() {
    if (this.position === 'modal') {
      return this.renderModal();
    } else if (this.position === 'panel') {
      return this.renderSidePanel();
    } else {
      return this.renderInlinePanel();
    }
  }

  private renderModal() {
    return html`
      <div class="modal-overlay ${this.open ? 'open' : ''}" @click=${this.handleOverlayClick}>
        <div class="modal-content" @click=${(e: Event) => e.stopPropagation()}>
          <div class="modal-header">
            <h3 class="modal-title">${this.title}</h3>
            <button class="close-btn" @click=${this.close} aria-label="Close">×</button>
          </div>
          <div class="modal-body">
            ${this.renderContent()}
          </div>
        </div>
      </div>
    `;
  }

  private renderSidePanel() {
    return html`
      <div class="side-panel-overlay ${this.open ? 'open' : ''}" @click=${this.close}></div>
      <div class="side-panel ${this.open ? 'open' : ''}">
        <div class="modal-header">
          <h3 class="modal-title">${this.title}</h3>
          <button class="close-btn" @click=${this.close} aria-label="Close">×</button>
        </div>
        <div class="modal-body">
          ${this.renderContent()}
        </div>
      </div>
    `;
  }

  private renderInlinePanel() {
    return html`
      <div class="inline-panel ${this.open ? 'open' : ''}">
        <div class="inline-header">
          <span class="inline-title">${this.title}</span>
          <button class="close-btn" @click=${this.close} aria-label="Close">×</button>
        </div>
        <div class="modal-body">
          ${this.renderContent()}
        </div>
      </div>
    `;
  }

  private renderContent() {
    if (this.fields.length > 0) {
      return html`
        <div class="detail-grid">
          ${this.fields.map(field => this.renderField(field))}
        </div>
      `;
    }

    const entries = Object.entries(this.data);
    if (entries.length === 0) {
      return html`<p style="color: var(--text-secondary); font-style: italic;">No details available</p>`;
    }

    return html`
      <div class="detail-grid">
        ${entries.map(([key, value]) => html`
          <div class="detail-item">
            <span class="detail-label">${this.formatLabel(key)}</span>
            <span class="detail-value">${this.formatValue(value, this.inferType(key, value))}</span>
          </div>
        `)}
      </div>
    `;
  }

  private renderField(field: {key: string, label: string, type?: string}) {
    const value = this.data[field.key];
    if (value === undefined || value === null) return '';

    return html`
      <div class="detail-item">
        <span class="detail-label">${field.label}</span>
        <span class="detail-value ${field.type || ''} ${this.getStatusClass(value)}">${this.formatValue(value, field.type)}</span>
      </div>
    `;
  }

  private formatLabel(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim();
  }

  private formatValue(value: any, type?: string): string {
    if (value === undefined || value === null) return '—';

    switch (type) {
      case 'number':
        if (typeof value === 'number') {
          if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
          if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
          return value.toLocaleString();
        }
        return String(value);
      case 'date':
        try {
          const date = new Date(value);
          return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        } catch {
          return String(value);
        }
      case 'status':
        return String(value);
      default:
        return String(value);
    }
  }

  private inferType(key: string, value: any): string {
    const keyLower = key.toLowerCase();
    if (keyLower.includes('date') || keyLower.includes('time')) return 'date';
    if (keyLower.includes('status')) return 'status';
    if (typeof value === 'number') return 'number';
    return 'string';
  }

  private getStatusClass(value: any): string {
    if (typeof value !== 'string') return '';
    const valueLower = value.toLowerCase();
    if (valueLower.includes('active') || valueLower.includes('ongoing')) return 'active';
    if (valueLower.includes('resolved') || valueLower.includes('completed')) return 'resolved';
    if (valueLower.includes('pending') || valueLower.includes('investigating')) return 'pending';
    return '';
  }

  private handleOverlayClick(e: Event) {
    if ((e.target as HTMLElement).classList.contains('modal-overlay')) {
      this.close();
    }
  }

  close() {
    this.open = false;
    this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
  }
}

export class ItemSelectEvent extends Event {
  static eventName = 'item-select';

  constructor(
    public readonly item: any,
    public readonly index: number
  ) {
    super(ItemSelectEvent.eventName, { bubbles: true, composed: true });
  }
}

export class KpiClickEvent extends Event {
  static eventName = 'kpi-click';

  constructor(
    public readonly kpiData: any
  ) {
    super(KpiClickEvent.eventName, { bubbles: true, composed: true });
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'detail-modal': DetailModal;
  }
}
