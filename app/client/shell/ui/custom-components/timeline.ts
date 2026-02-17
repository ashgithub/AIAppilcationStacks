import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";

interface TimelineEvent {
  date: string;
  title: string;
  description?: string;
  category?: string;
  color?: string;
}

@customElement('timeline-component')
export class TimelineComponent extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor eventsPath: any = ""; // Keep for backward compatibility
  @property({ attribute: false }) accessor dateFormat: string = 'MM/DD/YYYY';
  @property({ attribute: false }) accessor eventColor: string = '#FF5722';
  @property({ attribute: false }) accessor lineColor: string = '#007bff';
  @property({ attribute: false }) accessor title: string = "";

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        background: #f8f9fa;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        padding: 16px;
        margin: 8px;
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
        background: #ddd;
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
        background: #4CAF50;
        border: 2px solid #fff;
        box-shadow: 0 0 0 2px #ddd;
      }

      .timeline-content {
        background: #fff;
        border-radius: 6px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      }

      .timeline-date {
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;
        font-weight: 500;
      }

      .timeline-title {
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin-bottom: 4px;
      }

      .timeline-description {
        font-size: 14px;
        color: #666;
        line-height: 1.4;
      }

      .timeline-category {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        margin-top: 8px;
        background: #e9ecef;
        color: #495057;
      }

      .empty-state {
        text-align: center;
        color: #666;
        padding: 40px;
        font-style: italic;
      }

      .timeline-item.custom-color::before {
        background: var(--event-color, #4CAF50);
      }
    `,
  ];

  render() {
    let events: TimelineEvent[] = [];

    // Use dataPath if provided (server preference), otherwise eventsPath
    const dataSource = this.dataPath || this.eventsPath;

    // Resolve data source
    if (dataSource && typeof dataSource === 'string') {
      if (this.processor) {
        let data = this.processor.getData(this.component, dataSource, this.surfaceId ?? 'default') as any;

        if (data instanceof Map) {
          data = Array.from(data.values());
        }

        if (Array.isArray(data)) {
          events = data.map((item: any) => {
            if (typeof item === 'object') {
              // Handle server payload structure: {description, end, start, title}
              return {
                date: item.start || item.date || item.timestamp || '',
                title: item.title || 'Event',
                description: item.description || '',
                category: 'Outage', // Default category for outages
                color: this.eventColor || '#FF5722' // Use configured event color
              };
            }
            return null;
          }).filter(Boolean) as TimelineEvent[];
        }
      }
    }

    // Sort events by date
    events.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    if (!events || events.length === 0) {
      return html`
        <div class="empty-state">
          No timeline data available
        </div>
      `;
    }

    return html`
      <div class="timeline">
        ${events.map(event => this.renderTimelineItem(event))}
      </div>
    `;
  }

  updated(changedProperties: Map<string | number | symbol, unknown>) {
    super.updated(changedProperties);
    if (changedProperties.has('dataPath') || changedProperties.has('eventsPath') || changedProperties.has('eventColor')) {
      this.requestUpdate();
    }
  }

  private renderTimelineItem(event: TimelineEvent) {
    const formattedDate = this.formatDate(event.date);

    return html`
      <div class="timeline-item" style="--event-color: ${event.color}">
        <div class="timeline-content">
          <div class="timeline-date">${formattedDate}</div>
          <div class="timeline-title">${event.title}</div>
          ${event.description ? html`<div class="timeline-description">${event.description}</div>` : ''}
          ${event.category ? html`<div class="timeline-category">${event.category}</div>` : ''}
        </div>
      </div>
    `;
  }

  private formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return dateString; // Return as-is if invalid
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