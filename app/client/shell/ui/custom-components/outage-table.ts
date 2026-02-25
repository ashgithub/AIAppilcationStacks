import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { colors } from "../../theme/design-tokens.js";

interface OutageRecord {
  id: string;
  location: string;
  status: string;
  severity: string;
  startTime: string;
  estimatedRestoration: string;
  affectedCustomers: number;
}

@customElement('outage-table')
export class OutageTable extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor title: string = "Outage Information";
  @property({ attribute: false }) accessor showPagination: boolean = false;
  @property({ attribute: false }) accessor pageSize: number = 10;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        background: var(--module-agent-bg);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        padding: var(--space-xl);
        margin: var(--space-xs);
        overflow: hidden;
      }

      .table-container {
        width: 100%;
        font-family: var(--font-family);
      }

      .table-title {
        text-align: left;
        margin-bottom: var(--space-lg);
        font-size: 20px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        letter-spacing: 0.5px;
      }

      .table-wrapper {
        overflow-x: auto;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }

      thead {
        background: var(--surface-secondary);
      }

      th {
        padding: 14px var(--space-md);
        text-align: left;
        font-weight: var(--font-weight-semibold);
        color: var(--text-secondary);
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
        border-bottom: 1px solid var(--border-primary);
        white-space: nowrap;
      }

      td {
        padding: 14px var(--space-md);
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border-subtle);
        vertical-align: middle;
      }

      tbody tr {
        transition: background var(--transition-normal);
      }

      tbody tr:hover {
        background: var(--hover-overlay);
      }

      tbody tr:last-child td {
        border-bottom: none;
      }

      .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: var(--radius-xl);
        font-size: 11px;
        font-weight: var(--font-weight-semibold);
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }

      .status-active {
        background: rgba(239, 68, 68, 0.15);
        color: var(--color-error);
      }

      .status-investigating {
        background: rgba(245, 158, 11, 0.15);
        color: var(--color-warning);
      }

      .status-resolved {
        background: rgba(16, 185, 129, 0.15);
        color: var(--color-success);
      }

      .status-scheduled {
        background: rgba(136, 194, 255, 0.15);
        color: var(--oracle-primary);
      }

      .severity-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: var(--font-weight-medium);
      }

      .severity-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }

      .severity-critical .severity-dot {
        background: var(--color-error);
      }

      .severity-high .severity-dot {
        background: var(--color-error);
      }

      .severity-medium .severity-dot {
        background: var(--color-warning);
      }

      .severity-low .severity-dot {
        background: var(--color-success);
      }

      .customer-count {
        font-weight: var(--font-weight-semibold);
        color: var(--oracle-primary);
      }

      .outage-id {
        font-family: var(--font-family-mono);
        font-size: 12px;
        color: var(--text-secondary);
      }

      .time-cell {
        font-size: 12px;
        color: var(--text-secondary);
      }

      .time-cell .date {
        color: var(--text-primary);
        font-weight: var(--font-weight-medium);
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: 40px var(--space-lg);
        font-style: italic;
      }

      .table-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: var(--space-md);
        padding-top: var(--space-md);
        border-top: 1px solid var(--border-primary);
      }

      .record-count {
        font-size: 12px;
        color: var(--text-secondary);
      }

      .pagination {
        display: flex;
        gap: var(--space-sm);
      }

      .pagination button {
        background: var(--surface-secondary);
        border: 1px solid var(--border-primary);
        color: var(--text-secondary);
        padding: 6px 12px;
        border-radius: var(--radius-sm);
        font-size: 12px;
        cursor: pointer;
        transition: all var(--transition-normal);
      }

      .pagination button:hover {
        background: var(--surface-elevated);
      }

      .pagination button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
    `,
  ];

  render() {
    let outageData: OutageRecord[] = [];

    // Resolve dataPath
    if (this.dataPath && typeof this.dataPath === 'string' && this.processor) {
      let rawData = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;

      if (rawData instanceof Map) {
        rawData = Array.from(rawData.values());
      }

      if (Array.isArray(rawData)) {
        outageData = rawData.map((item: any) => {
          const record: OutageRecord = {
            id: '',
            location: '',
            status: '',
            severity: '',
            startTime: '',
            estimatedRestoration: '',
            affectedCustomers: 0
          };

          // Handle valueMap format
          if (item.valueMap) {
            for (const kv of item.valueMap) {
              if (kv.key === 'id') record.id = kv.valueString || '';
              if (kv.key === 'location') record.location = kv.valueString || '';
              if (kv.key === 'status') record.status = kv.valueString || '';
              if (kv.key === 'severity') record.severity = kv.valueString || '';
              if (kv.key === 'startTime') record.startTime = kv.valueString || '';
              if (kv.key === 'estimatedRestoration') record.estimatedRestoration = kv.valueString || '';
              if (kv.key === 'affectedCustomers') record.affectedCustomers = kv.valueNumber || 0;
            }
          } else if (item instanceof Map) {
            record.id = item.get('id') || '';
            record.location = item.get('location') || '';
            record.status = item.get('status') || '';
            record.severity = item.get('severity') || '';
            record.startTime = item.get('startTime') || '';
            record.estimatedRestoration = item.get('estimatedRestoration') || '';
            record.affectedCustomers = item.get('affectedCustomers') || 0;
          } else if (typeof item === 'object') {
            record.id = item.id || '';
            record.location = item.location || '';
            record.status = item.status || '';
            record.severity = item.severity || '';
            record.startTime = item.startTime || '';
            record.estimatedRestoration = item.estimatedRestoration || '';
            record.affectedCustomers = item.affectedCustomers || 0;
          }

          return record;
        });
      }
    }

    if (outageData.length === 0) {
      return html`
        <div class="table-container">
          <div class="table-title">${this.title}</div>
          <div class="empty-state">No outage data available</div>
        </div>
      `;
    }

    return html`
      <div class="table-container">
        <div class="table-title">${this.title}</div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Outage ID</th>
                <th>Location</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Start Time</th>
                <th>Est. Restoration</th>
                <th>Affected</th>
              </tr>
            </thead>
            <tbody>
              ${outageData.map(record => this.renderRow(record))}
            </tbody>
          </table>
        </div>
        <div class="table-footer">
          <span class="record-count">${outageData.length} outage${outageData.length !== 1 ? 's' : ''} total</span>
        </div>
      </div>
    `;
  }

  private renderRow(record: OutageRecord) {
    const statusClass = this.getStatusClass(record.status);
    const severityClass = this.getSeverityClass(record.severity);

    return html`
      <tr>
        <td><span class="outage-id">${record.id}</span></td>
        <td>${record.location}</td>
        <td>
          <span class="status-badge ${statusClass}">${record.status}</span>
        </td>
        <td>
          <span class="severity-badge ${severityClass}">
            <span class="severity-dot"></span>
            ${record.severity}
          </span>
        </td>
        <td class="time-cell">
          <span class="date">${this.formatDateTime(record.startTime)}</span>
        </td>
        <td class="time-cell">
          <span class="date">${this.formatDateTime(record.estimatedRestoration)}</span>
        </td>
        <td>
          <span class="customer-count">${this.formatNumber(record.affectedCustomers)}</span>
        </td>
      </tr>
    `;
  }

  private getStatusClass(status: string): string {
    const normalized = status.toLowerCase();
    if (normalized.includes('active') || normalized.includes('ongoing')) return 'status-active';
    if (normalized.includes('investigating') || normalized.includes('pending')) return 'status-investigating';
    if (normalized.includes('resolved') || normalized.includes('completed')) return 'status-resolved';
    if (normalized.includes('scheduled') || normalized.includes('planned')) return 'status-scheduled';
    return 'status-active';
  }

  private getSeverityClass(severity: string): string {
    const normalized = severity.toLowerCase();
    if (normalized.includes('critical')) return 'severity-critical';
    if (normalized.includes('high')) return 'severity-high';
    if (normalized.includes('medium') || normalized.includes('moderate')) return 'severity-medium';
    if (normalized.includes('low') || normalized.includes('minor')) return 'severity-low';
    return 'severity-medium';
  }

  private formatDateTime(dateStr: string): string {
    if (!dateStr) return '—';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  private formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
  }
}
