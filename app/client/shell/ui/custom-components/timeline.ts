import { html, css } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { v0_8 } from "@a2ui/lit";
import { colors } from "../../theme/design-tokens.js";
import { ItemSelectEvent } from "./detail-modal.js";

interface TimelineEvent {
  date: string;
  title: string;
  description?: string;
  category?: string;
  color?: string;
  details?: Record<string, any>;
}

@customElement('timeline-component')
export class TimelineComponent extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor detailsPath: any = "";
  @property({ attribute: false }) accessor expandable: boolean = true;
  @property({ attribute: false }) accessor compactPreview: boolean = true;
  @property({ attribute: false }) accessor action: v0_8.Types.Action | null = null;
  @property({ attribute: false }) accessor actionLabel: string = "";
  @property({ attribute: false }) accessor actionFallbackName: string = "queue_timeline_event";

  @state() accessor expandedItems: Set<number> = new Set();

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        background: var(--surface-primary);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        padding: var(--space-md);
        margin: var(--space-xs);
        overflow-y: auto;
        max-height: 600px;
      }

      .timeline {
        position: relative;
        padding-left: 30px;
      }

      .timeline::before {
        content: '';
        position: absolute;
        left: 15px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: var(--border-secondary);
      }

      .timeline-item {
        position: relative;
        margin-bottom: 30px;
        padding-left: 20px;
      }

      .timeline-item::before {
        content: '';
        position: absolute;
        left: -25px;
        top: 8px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--color-success);
        border: 2px solid var(--surface-primary);
        box-shadow: 0 0 0 2px var(--border-secondary);
      }

      .timeline-content {
        background: var(--surface-secondary);
        border-radius: var(--radius-sm);
        padding: var(--space-sm);
        box-shadow: var(--shadow-sm);
      }

      .timeline-date {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 4px;
        font-weight: var(--font-weight-medium);
      }

      .timeline-title {
        font-size: 16px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin-bottom: 4px;
      }

      .timeline-description {
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.4;
      }

      .timeline-category {
        display: inline-block;
        padding: 2px 8px;
        border-radius: var(--radius-xl);
        font-size: 11px;
        font-weight: var(--font-weight-medium);
        margin-top: 8px;
        background: var(--surface-primary);
        color: var(--text-secondary);
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: 40px;
        font-style: italic;
      }

      .timeline-item.custom-color::before {
        background: var(--event-color, var(--color-success));
      }

      /* Expandable styles */
      .timeline-content.expandable {
        cursor: pointer;
        transition: all var(--transition-normal);
      }

      .timeline-content.expandable:hover {
        background: var(--surface-elevated);
        transform: translateX(4px);
      }

      .timeline-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--space-sm);
      }

      .timeline-header-content {
        flex: 1;
        min-width: 0;
      }

      .expand-toggle {
        color: var(--text-secondary);
        font-size: 12px;
        padding: 4px;
        transition: transform var(--transition-normal);
        flex-shrink: 0;
      }

      .expand-toggle.expanded {
        transform: rotate(90deg);
      }

      .timeline-expanded-details {
        max-height: 0;
        overflow: hidden;
        opacity: 0;
        transition: max-height 0.3s ease, opacity 0.2s ease, margin 0.3s ease;
      }

      .timeline-expanded-details.open {
        max-height: none;
        overflow: visible;
        opacity: 1;
        margin-top: var(--space-sm);
        padding-top: var(--space-sm);
        border-top: 1px dashed var(--border-subtle);
      }

      .timeline-detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(180px, 100%), 1fr));
        gap: var(--space-sm);
      }

      .timeline-detail-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .timeline-detail-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        font-weight: var(--font-weight-semibold);
      }

      .timeline-detail-value {
        font-size: 13px;
        color: var(--text-primary);
        overflow-wrap: anywhere;
      }

      .timeline-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-sm);
        margin-top: var(--space-sm);
      }

      .timeline-action-btn {
        padding: 6px 12px;
        font-size: 11px;
        border-radius: var(--radius-sm);
        background: var(--surface-primary);
        border: 1px solid var(--border-primary);
        color: var(--text-secondary);
        cursor: pointer;
        transition: all var(--transition-normal);
        max-width: 100%;
        white-space: normal;
        overflow-wrap: anywhere;
      }

      .timeline-action-btn:hover {
        background: var(--oracle-primary);
        color: var(--surface-primary);
        border-color: var(--oracle-primary);
      }
    `,
  ];

  render() {
    const events = this.getEvents();

    if (events.length === 0) {
      return html`
        <div class="empty-state">
          No timeline data available
        </div>
      `;
    }

    return html`
      <div class="timeline">
        ${events.map((event, index) => this.renderTimelineItem(event, index))}
      </div>
    `;
  }

  private getEvents(): TimelineEvent[] {
    const events: TimelineEvent[] = [];
    const eventRecords = this.parseRecordsFromPath(this.dataPath);
    const detailRecords = this.parseRecordsFromPath(this.detailsPath);

    eventRecords.forEach((eventData, index) => {
      const dateText = this.toDisplayText(eventData.date);
      if (!dateText) return;

      const mainKeys = new Set(['date', 'title', 'description', 'category', 'color']);
      const fallbackDetails = Object.fromEntries(
        Object.entries(eventData).filter(([key]) => !mainKeys.has(key))
      );
      const details = detailRecords[index] && Object.keys(detailRecords[index]).length > 0
        ? detailRecords[index]
        : fallbackDetails;

      events.push({
        date: dateText,
        title: this.toDisplayText(eventData.title) || 'Event',
        description: this.toDisplayText(eventData.description),
        category: this.toDisplayText(eventData.category) || 'Event',
        color: this.toDisplayText(eventData.color) || colors.semantic.success,
        details: Object.keys(details).length > 0 ? details : undefined
      });
    });

    events.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return events;
  }

  private isMapLike(value: any): boolean {
    return !!value
      && typeof value.get === 'function'
      && typeof value.values === 'function'
      && typeof value.forEach === 'function';
  }

  private mapToObject(mapOrValue: any): any {
    if (this.isMapLike(mapOrValue)) {
      const obj: Record<string, any> = {};
      mapOrValue.forEach((value: any, key: string) => {
        obj[key] = this.mapToObject(value);
      });
      return obj;
    }
    if (Array.isArray(mapOrValue)) {
      return mapOrValue.map((entry) => this.mapToObject(entry));
    }
    if (mapOrValue && typeof mapOrValue === 'object') {
      const obj: Record<string, any> = {};
      Object.entries(mapOrValue).forEach(([key, value]) => {
        obj[key] = this.mapToObject(value);
      });
      return obj;
    }
    return mapOrValue;
  }

  private toDisplayText(value: any): string {
    const normalized = this.mapToObject(value);
    if (normalized === undefined || normalized === null) return '';
    if (typeof normalized === 'string') return normalized.trim();
    if (typeof normalized === 'number' || typeof normalized === 'boolean') return String(normalized);
    if (Array.isArray(normalized)) {
      return normalized
        .map((item) => this.toDisplayText(item))
        .filter((item) => item.length > 0)
        .join(', ');
    }
    if (typeof normalized === 'object') {
      const segments = Object.entries(normalized)
        .map(([k, v]) => {
          const text = this.toDisplayText(v);
          return text ? `${this.formatLabel(k)}: ${text}` : '';
        })
        .filter((item) => item.length > 0);
      return segments.join(', ');
    }
    return String(normalized).trim();
  }

  private parseRecordItem(item: any): Record<string, any> {
    const record: Record<string, any> = {};
    if (!item || typeof item !== 'object') return record;

    if ('valueMap' in item && Array.isArray(item.valueMap)) {
      for (const kv of item.valueMap) {
        if (!kv || !kv.key) continue;
        if (kv.valueString !== undefined) {
          record[kv.key] = kv.valueString;
        } else if (kv.valueNumber !== undefined) {
          record[kv.key] = kv.valueNumber;
        } else if (kv.valueBoolean !== undefined) {
          record[kv.key] = kv.valueBoolean;
        } else if (kv.valueMap !== undefined) {
          record[kv.key] = this.mapToObject(kv.valueMap);
        }
      }
      return record;
    }

    if (this.isMapLike(item)) {
      return this.mapToObject(item);
    }

    return { ...item };
  }

  private parseRecordsFromPath(path: any): Record<string, any>[] {
    if (!path || typeof path !== 'string' || !this.processor) return [];

    let data = this.processor.getData(this.component, path, this.surfaceId ?? 'default') as any;
    if (this.isMapLike(data)) {
      data = Array.from(data.values());
    }
    if (!Array.isArray(data)) return [];

    return data.map((item: any) => this.parseRecordItem(item));
  }

  private renderTimelineItem(event: TimelineEvent, index: number) {
    const formattedDate = this.formatDate(event.date);
    const isExpanded = this.expandedItems.has(index);
    const showInlineDescription = !this.expandable || !this.compactPreview;

    return html`
      <div class="timeline-item" style="--event-color: ${event.color}">
        <div 
          class="timeline-content ${this.expandable ? 'expandable' : ''}"
          @click=${() => this.toggleExpand(index, event)}
        >
          <div class="timeline-header">
            <div class="timeline-header-content">
              <div class="timeline-date">${formattedDate}</div>
              <div class="timeline-title">${event.title}</div>
            </div>
            ${this.expandable ? html`
              <span class="expand-toggle ${isExpanded ? 'expanded' : ''}">▶</span>
            ` : ''}
          </div>
          ${showInlineDescription && event.description ? html`<div class="timeline-description">${event.description}</div>` : ''}
          ${event.category ? html`<div class="timeline-category">${event.category}</div>` : ''}
          
          ${this.expandable ? html`
            <div class="timeline-expanded-details ${isExpanded ? 'open' : ''}">
              <div class="timeline-detail-grid">
                ${event.description ? html`
                  <div class="timeline-detail-item">
                    <span class="timeline-detail-label">Description</span>
                    <span class="timeline-detail-value">${event.description}</span>
                  </div>
                ` : ''}
                <div class="timeline-detail-item">
                  <span class="timeline-detail-label">Full Date</span>
                  <span class="timeline-detail-value">${this.formatFullDate(event.date)}</span>
                </div>
                <div class="timeline-detail-item">
                  <span class="timeline-detail-label">Category</span>
                  <span class="timeline-detail-value">${event.category || 'General'}</span>
                </div>
                ${event.details ? Object.entries(event.details).map(([key, value]) => html`
                  <div class="timeline-detail-item">
                    <span class="timeline-detail-label">${this.formatLabel(key)}</span>
                    <span class="timeline-detail-value">${this.toDisplayText(value) || '--'}</span>
                  </div>
                `) : ''}
              </div>
              <div class="timeline-actions">
                <button class="timeline-action-btn" @click=${(e: Event) => this.handleAction(e, event, index)}>
                  ${this.getActionLabel(event)}
                </button>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  private toggleExpand(index: number, event: TimelineEvent) {
    if (!this.expandable) return;
    
    if (this.expandedItems.has(index)) {
      this.expandedItems.delete(index);
    } else {
      this.expandedItems.add(index);
    }
    this.requestUpdate();
    
    // Dispatch selection event
    this.dispatchEvent(new ItemSelectEvent(event, index));
  }

  private getValidatedActionName(): string {
    const fallback = (this.actionFallbackName || "queue_timeline_event").trim();
    const candidate = (this.action?.name || fallback).trim();
    const safeActionNamePattern = /^[a-z][a-z0-9_]{1,63}$/;

    if (!safeActionNamePattern.test(candidate)) {
      console.warn(
        `[TimelineComponent] Invalid action name "${candidate}". Falling back to "${fallback}".`
      );
      return fallback;
    }

    return candidate;
  }

  private humanizeActionName(actionName: string): string {
    return actionName
      .replace(/[_-]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  private getActionLabel(event: TimelineEvent): string {
    const detailLabel = event.details?.actionLabel ?? event.details?.action_label;
    if (typeof detailLabel === "string" && detailLabel.trim()) {
      return detailLabel.trim();
    }

    const configuredLabel = this.actionLabel?.trim();
    if (configuredLabel && configuredLabel.toLowerCase() !== "view details") {
      return configuredLabel;
    }

    return this.humanizeActionName(this.getValidatedActionName());
  }

  private handleAction(e: Event, event: TimelineEvent, index: number) {
    e.stopPropagation();

    const actionContext: Record<string, unknown> = {
      timelineIndex: index,
      date: event.date,
      title: event.title,
      description: event.description ?? "",
      category: event.category ?? "",
      ...(event.details ?? {}),
    };

    const contextEntries: NonNullable<v0_8.Types.Action["context"]> =
      Object.entries(actionContext).map(([key, value]) => {
        if (typeof value === "boolean") {
          return { key, value: { literalBoolean: value } };
        }
        if (typeof value === "number") {
          return { key, value: { literalNumber: value } };
        }
        return { key, value: { literalString: this.toDisplayText(value) || "--" } };
      });

    const resolvedAction: v0_8.Types.Action = {
      name: this.getValidatedActionName(),
      context: [...(this.action?.context ?? []), ...contextEntries],
    };

    const evt = new v0_8.Events.StateEvent<"a2ui.action">({
      eventType: "a2ui.action",
      action: resolvedAction,
      dataContextPath: this.dataContextPath,
      sourceComponentId: this.id || "timeline-component",
      sourceComponent: this.component,
    });

    this.dispatchEvent(evt);

    // Backward compatibility for existing static module handlers.
    this.dispatchEvent(new CustomEvent('timeline-action', {
      bubbles: true,
      composed: true,
      detail: { action: resolvedAction.name, event }
    }));
  }

  private formatLabel(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim();
  }

  private formatFullDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return date.toLocaleString(undefined, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  }

  private formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return dateString;
      }

      const options: Intl.DateTimeFormatOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      };

      return date.toLocaleDateString(undefined, options);
    } catch {
      return dateString;
    }
  }
}
