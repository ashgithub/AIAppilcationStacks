import { html, css } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { colors, designTokensCSS } from "../../theme/design-tokens.js";
import { ItemSelectEvent } from "./detail-modal.js";
import "./detail-modal.js";

interface TableColumn {
  header: string;
  field: string;
  type: string;
}
interface TableRecord {
  [key: string]: any;
}

@customElement('data-table')
export class Table extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor detailsPath: any = "";
  @property({ attribute: false }) accessor title: string = "Data Table";
  @property({ attribute: false }) accessor columns: TableColumn[] = [];
  @property({ attribute: false }) accessor showPagination: boolean = false;
  @property({ attribute: false }) accessor pageSize: number = 10;
  @property({ attribute: false }) accessor expandable: boolean = true;
  @property({ attribute: false }) accessor showDetailPanel: boolean = false;

  @state() accessor expandedRows: Set<number> = new Set();
  @state() accessor selectedRow: number | null = null;
  @state() accessor selectedRecord: TableRecord | null = null;
  @state() accessor selectedDetails: TableRecord | null = null;

  static styles = [
    ...Root.styles,
    designTokensCSS,
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

      .number-cell {
        font-weight: var(--font-weight-semibold);
        color: var(--oracle-primary);
        text-align: right;
      }

      .string-cell {
        color: var(--text-primary);
      }

      .date-cell {
        font-size: 12px;
        color: var(--text-secondary);
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

      /* Expandable row styles */
      tbody tr.clickable {
        cursor: pointer;
      }

      tbody tr.selected {
        background: var(--surface-elevated);
        border-left: 3px solid var(--oracle-primary);
      }

      tbody tr.expanded {
        background: var(--surface-secondary);
      }

      .expand-icon {
        width: 20px;
        text-align: center;
        color: var(--text-secondary);
        transition: transform var(--transition-normal);
        font-size: 12px;
      }

      .expand-icon.rotated {
        transform: rotate(90deg);
      }

      .expanded-content {
        background: var(--surface-secondary);
        border-top: 1px dashed var(--border-subtle);
      }

      .expanded-content td {
        padding: var(--space-md) var(--space-lg);
      }

      .expanded-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: var(--space-md);
      }

      .expanded-field {
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
      }

      .expanded-label {
        font-size: 10px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .expanded-value {
        font-size: 13px;
        color: var(--text-primary);
      }

      /* Detail panel styles */
      .table-with-panel {
        display: flex;
        gap: var(--space-md);
      }

      .table-main {
        flex: 1;
        min-width: 0;
      }

      .detail-panel {
        width: 320px;
        background: var(--surface-secondary);
        border-radius: var(--radius-md);
        padding: var(--space-md);
        position: sticky;
        top: 0;
        max-height: 400px;
        overflow-y: auto;
      }

      .detail-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--space-md);
        padding-bottom: var(--space-sm);
        border-bottom: 1px solid var(--border-primary);
      }

      .detail-panel-title {
        font-size: 14px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
      }

      .detail-panel-close {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 16px;
        padding: 4px;
        border-radius: var(--radius-sm);
      }

      .detail-panel-close:hover {
        background: var(--hover-overlay);
        color: var(--text-primary);
      }

      .detail-panel-empty {
        color: var(--text-secondary);
        font-style: italic;
        font-size: 13px;
        text-align: center;
        padding: var(--space-lg);
      }
    `,
  ];

  render() {
    const tableData = this.parseRecordsFromPath(this.dataPath);
    const detailData = this.parseRecordsFromPath(this.detailsPath);

    if (!this.columns || this.columns.length === 0) {
      return html`
        <div class="table-container">
          <div class="table-title">${this.title}</div>
          <div class="empty-state">No columns configured</div>
        </div>
      `;
    }

    if (tableData.length === 0) {
      return html`
        <div class="table-container">
          <div class="table-title">${this.title}</div>
          <div class="empty-state">No data available</div>
        </div>
      `;
    }

    // Render with or without detail panel
    if (this.showDetailPanel) {
      return html`
        <div class="table-container table-with-panel">
          <div class="table-main">
            <div class="table-title">${this.title}</div>
            ${this.renderTable(tableData, detailData)}
          </div>
          ${this.renderDetailPanel()}
        </div>
      `;
    }

    return html`
      <div class="table-container">
        <div class="table-title">${this.title}</div>
        ${this.renderTable(tableData, detailData)}
        <div class="table-footer">
          <span class="record-count">${tableData.length} record${tableData.length !== 1 ? 's' : ''} total</span>
        </div>
      </div>
    `;
  }

  private renderTable(tableData: TableRecord[], detailData: TableRecord[]) {
    return html`
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              ${this.expandable ? html`<th style="width: 30px;"></th>` : ''}
              ${this.columns.map(column => html`<th>${column.header}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${tableData.map((record, index) => this.renderRow(record, index, detailData[index]))}
          </tbody>
        </table>
      </div>
    `;
  }

  private renderDetailPanel() {
    const detailSource = this.getDetailSource(this.selectedRecord, this.selectedDetails);
    if (!detailSource) {
      return html`
        <div class="detail-panel">
          <div class="detail-panel-header">
            <span class="detail-panel-title">Details</span>
          </div>
          <div class="detail-panel-empty">Select a row to view details</div>
        </div>
      `;
    }

    return html`
      <div class="detail-panel">
        <div class="detail-panel-header">
          <span class="detail-panel-title">Record Details</span>
          <button class="detail-panel-close" @click=${this.clearSelection}>×</button>
        </div>
        <div class="expanded-grid">
          ${Object.entries(detailSource).map(([key, value]) => html`
            <div class="expanded-field">
              <span class="expanded-label">${this.formatFieldLabel(key)}</span>
              <span class="expanded-value">${this.formatFieldValue(key, value)}</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  private renderRow(record: TableRecord, index: number, details?: TableRecord) {
    const isExpanded = this.expandedRows.has(index);
    const isSelected = this.selectedRow === index;

    return html`
      <tr 
        class="${this.expandable ? 'clickable' : ''} ${isExpanded ? 'expanded' : ''} ${isSelected ? 'selected' : ''}"
        @click=${() => this.handleRowClick(record, index, details)}
      >
        ${this.expandable ? html`
          <td>
            <span class="expand-icon" @click=${(e: Event) => this.toggleExpand(e, index)}>${isExpanded ? '\u25BC' : '\u25B6'}</span>
          </td>
        ` : ''}
        ${this.columns.map(column => this.renderCell(record, column))}
      </tr>
      ${isExpanded ? this.renderExpandedContent(record, details) : ''}
    `;
  }

  private renderExpandedContent(record: TableRecord, details?: TableRecord) {
    if (details && Object.keys(details).length > 0) {
      return html`
        <tr class="expanded-content">
          <td colspan="${this.columns.length + (this.expandable ? 1 : 0)}">
            <div class="expanded-grid">
              ${Object.entries(details).map(([key, value]) => html`
                <div class="expanded-field">
                  <span class="expanded-label">${this.formatFieldLabel(key)}</span>
                  <span class="expanded-value">${this.formatFieldValue(key, value)}</span>
                </div>
              `)}
            </div>
          </td>
        </tr>
      `;
    }

    // Get all fields that are not in the main columns
    const displayedFields = new Set(this.columns.map(c => c.field));
    const extraFields = Object.entries(record).filter(([key]) => !displayedFields.has(key));

    // If no extra fields, show all fields with more detail
    const fieldsToShow = extraFields.length > 0 ? extraFields : Object.entries(record);

    return html`
      <tr class="expanded-content">
        <td colspan="${this.columns.length + (this.expandable ? 1 : 0)}">
          <div class="expanded-grid">
            ${fieldsToShow.map(([key, value]) => html`
              <div class="expanded-field">
                <span class="expanded-label">${this.formatFieldLabel(key)}</span>
                <span class="expanded-value">${this.formatFieldValue(key, value)}</span>
              </div>
            `)}
          </div>
        </td>
      </tr>
    `;
  }

  private handleRowClick(record: TableRecord, index: number, details?: TableRecord) {
    if (this.expandable) {
      this.toggleExpandedRow(index);
    }

    if (this.showDetailPanel) {
      this.selectedRow = index;
      this.selectedRecord = record;
      this.selectedDetails = details ?? null;
    }
    // Dispatch event for parent components
    this.dispatchEvent(new ItemSelectEvent(record, index));
  }

  private toggleExpand(e: Event, index: number) {
    e.stopPropagation();
    this.toggleExpandedRow(index);
  }

  private toggleExpandedRow(index: number) {
    if (this.expandedRows.has(index)) {
      this.expandedRows.delete(index);
    } else {
      this.expandedRows.add(index);
    }
    this.requestUpdate();
  }

  private clearSelection() {
    this.selectedRow = null;
    this.selectedRecord = null;
    this.selectedDetails = null;
  }

  private getDetailSource(record: TableRecord | null, details: TableRecord | null | undefined): TableRecord | null {
    if (details && Object.keys(details).length > 0) {
      return details;
    }
    return record;
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
    return mapOrValue;
  }

  private parseRecordItem(item: any): TableRecord {
    const record: TableRecord = {};

    if (!item || typeof item !== 'object') {
      return record;
    }

    if ('valueMap' in item && Array.isArray(item.valueMap)) {
      for (const kv of item.valueMap) {
        if (!kv || !kv.key) continue;
        if (kv.valueString !== undefined) {
          record[kv.key] = kv.valueString;
        } else if (kv.valueNumber !== undefined) {
          record[kv.key] = kv.valueNumber;
        } else if (kv.valueBoolean !== undefined) {
          record[kv.key] = kv.valueBoolean;
        }
      }
      return record;
    }

    if (this.isMapLike(item)) {
      return this.mapToObject(item);
    }

    Object.assign(record, item);
    return record;
  }

  private parseRecordsFromPath(path: any): TableRecord[] {
    if (!path || typeof path !== 'string' || !this.processor) return [];

    let rawData = this.processor.getData(this.component, path, this.surfaceId ?? 'default') as any;

    if (this.isMapLike(rawData)) {
      rawData = Array.from(rawData.values());
    }

    if (!Array.isArray(rawData)) return [];

    return rawData.map((item: any) => this.parseRecordItem(item));
  }

  private formatFieldLabel(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim();
  }

  private formatFieldValue(key: string, value: any): string {
    if (value === undefined || value === null) return '—';
    const keyLower = key.toLowerCase();
    if (keyLower.includes('date') || keyLower.includes('time')) {
      return this.formatDateTime(String(value));
    }
    if (typeof value === 'number') {
      return this.formatNumber(value);
    }
    return String(value);
  }

  private renderCell(record: TableRecord, column: TableColumn) {
    const value = record[column.field];
    let formattedValue = value;

    if (value === undefined || value === null) {
      formattedValue = '—';
    } else {
      switch (column.type) {
        case 'number':
          formattedValue = this.formatNumber(value);
          return html`<td class="number-cell">${formattedValue}</td>`;
        case 'date':
          formattedValue = this.formatDateTime(value);
          return html`<td class="time-cell"><span class="date">${formattedValue}</span></td>`;
        case 'status':
          return html`<td><span class="status-badge ${this.getStatusClass(value)}">${value}</span></td>`;
        case 'severity':
          return html`<td><span class="severity-badge ${this.getSeverityClass(value)}"><span class="severity-dot"></span>${value}</span></td>`;
        case 'string':
        default:
          return html`<td class="string-cell">${formattedValue}</td>`;
      }
    }

    return html`<td>${formattedValue}</td>`;
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

  private formatNumber(num: any): string {
    if (typeof num !== 'number') return String(num || '—');
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
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
}

