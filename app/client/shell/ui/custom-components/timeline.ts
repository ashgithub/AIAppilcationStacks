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

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        background: #1a1a1a;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
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
        background: #444;
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
        border: 2px solid #1a1a1a;
        box-shadow: 0 0 0 2px #444;
      }

      .timeline-content {
        background: #2a2a2a;
        border-radius: 6px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
      }

      .timeline-date {
        font-size: 12px;
        color: #cccccc;
        margin-bottom: 4px;
        font-weight: 500;
      }

      .timeline-title {
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
      }

      .timeline-description {
        font-size: 14px;
        color: #cccccc;
        line-height: 1.4;
      }

      .timeline-category {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        margin-top: 8px;
        background: #333;
        color: #cccccc;
      }

      .empty-state {
        text-align: center;
        color: #cccccc;
        padding: 40px;
        font-style: italic;
      }

      .timeline-item.custom-color::before {
        background: var(--event-color, #4CAF50);
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
        ${events.map(event => this.renderTimelineItem(event))}
      </div>
    `;
  }

  private getEvents(): TimelineEvent[] {
    let events: TimelineEvent[] = [];

    if (this.dataPath && typeof this.dataPath === 'string') {
      if (this.processor) {
        let data = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;

        if (data instanceof Map) {
          data = Array.from(data.values());
        }

        if (Array.isArray(data)) {
          events = data.map((item: any) => {
            let eventData: any = {};

            if (item instanceof Map) {
              // Handle A2UI Map structure: Map('date' -> '2023-01-15', 'title' -> 'Project Start', ...)
              for (const [key, value] of item.entries()) {
                if (key === 'date') eventData.date = value;
                if (key === 'title') eventData.title = value;
                if (key === 'description') eventData.description = value;
                if (key === 'category') eventData.category = value;
              }
            } else if (typeof item === 'object' && item.valueMap && Array.isArray(item.valueMap)) {
              // Handle A2UI structure: {valueMap: [{key: 'date', valueString: ...}, ...]}
              item.valueMap.forEach((entry: any) => {
                if (entry.key === 'date' && entry.valueString) eventData.date = entry.valueString;
                if (entry.key === 'title' && entry.valueString) eventData.title = entry.valueString;
                if (entry.key === 'description' && entry.valueString) eventData.description = entry.valueString;
                if (entry.key === 'category' && entry.valueString) eventData.category = entry.valueString;
              });
            }

            if (eventData.date) {
              return {
                date: eventData.date,
                title: eventData.title || 'Event',
                description: eventData.description || '',
                category: eventData.category || 'Event',
                color: '#4CAF50'
              };
            }
            return null;
          }).filter(Boolean) as TimelineEvent[];
        }
      }
    }

    // Sort events by date
    events.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return events;
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