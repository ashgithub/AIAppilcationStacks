import { html, css } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { v0_8 } from "@a2ui/lit";
import { colors } from "../../theme/design-tokens.js";
import { ItemSelectEvent } from "./detail-modal.js";

interface BarData {
  category: string;
  value: number;
  color: string;
  percentage?: number;
  rank?: number;
  total?: number;
  details?: Record<string, any>;
}

const BAR_COLORS = [
  colors.oracle.primary,
  colors.oracle.secondary,
  colors.semantic.success,
  colors.oracle.accent,
  colors.semantic.warning,
  colors.chat.bgSecondary,
];

@customElement('bar-graph')
export class BarGraph extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor labelPath: any = "";
  @property({ attribute: false }) accessor detailsPath: any = "";
  @property({ attribute: false }) accessor title: string = "Data Comparison";
  @property({ attribute: false }) accessor orientation: string = 'vertical';
  @property({ attribute: false }) accessor barWidth: number = 0.2;
  @property({ attribute: false }) accessor gap: number = 0.1;
  @property({ attribute: false }) accessor interactive: boolean = true;
  @property({ attribute: false }) accessor colorful: boolean = true;
  @property({ attribute: false }) accessor action: v0_8.Types.Action | null = null;
  @property({ attribute: false }) accessor actionLabel: string = "";
  @property({ attribute: false }) accessor actionFallbackName: string = "highlight_data";

  @state() accessor hoveredBar: number | null = null;
  @state() accessor selectedBar: number | null = null;
  @state() accessor showDetails: boolean = false;
  @state() accessor selectedBarData: BarData | null = null;

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
        overflow: visible;
      }

      .bar-chart {
        width: 100%;
        font-family: var(--font-family);
        position: relative;
        isolation: isolate;
        overflow-x: auto;
        overflow-y: visible;
      }

      .chart-title {
        text-align: center;
        margin-bottom: 28px;
        font-size: 18px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        position: relative;
        z-index: 30;
      }

      .bar-container {
        display: flex;
        align-items: end;
        justify-content: space-around;
        height: 300px;
        margin-top: 64px;
        margin-bottom: 52px;
        padding: 28px 20px 0;
        position: relative;
        z-index: 1;
        overflow: visible;
      }

      .bar-item {
        flex: 1;
        min-width: 72px;
        position: relative;
        height: 100%;
        z-index: 1;
      }

      .bar {
        width: 100%;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        transition: height 0.3s ease;
        position: absolute;
        bottom: 0;
      }

      .bar-label {
        position: absolute;
        bottom: -40px;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        font-size: 12px;
        font-weight: var(--font-weight-medium);
        color: var(--text-secondary);
        width: 100%;
        max-width: 120px;
        line-height: 1.2;
        padding: 0 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: normal;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
      }

      .value-label {
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        font-weight: var(--font-weight-bold);
        color: var(--text-primary);
        white-space: nowrap;
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: var(--space-md);
        font-style: italic;
      }

      .legend {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 15px;
        margin-top: var(--space-md);
        overflow: visible;
      }

      .legend-item {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
        color: var(--text-secondary);
      }

      .legend-color {
        width: 12px;
        height: 12px;
        border-radius: var(--radius-sm);
      }

      /* Interactive styles */
      .bar-item.interactive {
        cursor: pointer;
      }

      .bar-item.interactive:hover .bar {
        filter: brightness(1.15);
        transform: scaleY(1.02);
        transform-origin: bottom;
      }

      .bar-item:hover,
      .bar-item.selected {
        z-index: 50;
      }

      .bar-item.interactive .bar {
        transition: all var(--transition-normal);
      }

      .bar-item.selected .bar {
        /* Selection indicated by opacity and details panel, no glow */
      }

      .bar-item.dimmed .bar {
        opacity: 0.4;
      }

      .value-label {
        opacity: 0;
        transition: opacity var(--transition-normal);
      }

      .bar-item:hover .value-label,
      .bar-item.selected .value-label {
        opacity: 1;
      }

      /* Prevent number label and tooltip from competing in the same space */
      .bar-item:hover .bar .value-label {
        opacity: 0;
      }

      /* Tooltip */
      .bar-tooltip {
        position: absolute;
        bottom: calc(100% - 4px);
        left: 50%;
        transform: translate(-50%, -8px);
        background: var(--surface-primary);
        background-image: none;
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
        border-radius: var(--radius-md);
        padding: var(--space-sm) var(--space-md);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        min-width: 120px;
        max-width: 200px;
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transition: opacity var(--transition-normal), visibility var(--transition-normal);
        text-align: left;
      }

      .bar-item:hover .bar-tooltip {
        opacity: 1;
        visibility: visible;
      }

      .tooltip-category {
        font-size: 12px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin-bottom: 4px;
      }

      .tooltip-value {
        font-size: 18px;
        font-weight: var(--font-weight-bold);
        color: var(--oracle-primary);
      }

      .tooltip-percent {
        font-size: 11px;
        color: var(--text-secondary);
        margin-top: 4px;
      }

      /* Legend interactivity */
      .legend-item.interactive {
        cursor: pointer;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        transition: all var(--transition-normal);
      }

      .legend-item.interactive:hover {
        background: var(--hover-overlay);
      }

      .legend-item.active {
        background: var(--surface-secondary);
        box-shadow: var(--shadow-sm);
      }

      .legend-item.dimmed {
        opacity: 0.4;
      }

      /* Details panel */
      .details-panel {
        background: var(--surface-secondary);
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-md);
        margin-top: var(--space-md);
        overflow: hidden;
        max-height: 0;
        opacity: 0;
        transition: all 0.3s ease;
      }

      .details-panel.open {
        max-height: 400px;
        opacity: 1;
      }

      .details-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--space-md);
        background: var(--surface-tertiary);
        border-bottom: 1px solid var(--border-primary);
      }

      .details-title {
        font-size: 16px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: var(--space-sm);
      }

      .details-color {
        width: 16px;
        height: 16px;
        border-radius: var(--radius-sm);
      }

      .details-close {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: var(--space-xs);
        border-radius: var(--radius-sm);
        font-size: 18px;
        transition: all var(--transition-normal);
      }

      .details-close:hover {
        background: var(--hover-overlay);
        color: var(--text-primary);
      }

      .details-actions {
        padding: 0 var(--space-md) var(--space-md);
      }

      .details-action-btn {
        width: 100%;
        padding: 8px 12px;
        font-size: 12px;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-primary);
        background: var(--surface-primary);
        color: var(--text-primary);
        cursor: pointer;
        transition: all var(--transition-normal);
      }

      .details-action-btn:hover {
        background: var(--oracle-primary);
        border-color: var(--oracle-primary);
        color: var(--surface-primary);
      }

      .details-body {
        padding: var(--space-md);
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: var(--space-md);
      }

      .detail-item {
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
      }

      .detail-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
      }

      .detail-value {
        font-size: 20px;
        font-weight: var(--font-weight-bold);
        color: var(--text-primary);
      }

      .detail-value.highlight {
        color: var(--oracle-primary);
      }

      .detail-value.small {
        font-size: 14px;
        font-weight: var(--font-weight-medium);
      }

      .detail-comparison {
        display: flex;
        align-items: center;
        gap: var(--space-xs);
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: var(--space-xs);
      }

      .comparison-bar {
        flex: 1;
        height: 4px;
        background: var(--border-primary);
        border-radius: 2px;
        overflow: hidden;
      }

      .comparison-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease;
      }
    `,
  ];

  render() {
    let barData: BarData[] = [];

    // Resolve dataPath and labelPath
    if (this.dataPath && typeof this.dataPath === 'string' && this.labelPath && typeof this.labelPath === 'string') {
      if (this.processor) {
        let values = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;
        let labels = this.processor.getData(this.component, this.labelPath, this.surfaceId ?? 'default') as any;

        // Convert valueMap format to arrays
        if (values instanceof Map) {
          values = Array.from(values.values());
        } else if (Array.isArray(values) && values[0] && typeof values[0] === 'object' && 'valueNumber' in values[0]) {
          // Handle array of {valueNumber: ...}
          values = values.map((item: any) => item.valueNumber || item.valueString || 0);
        }

        if (labels instanceof Map) {
          labels = Array.from(labels.values());
        } else if (Array.isArray(labels) && labels[0] && typeof labels[0] === 'object' && 'valueString' in labels[0]) {
          // Handle array of {valueString: ...}
          labels = labels.map((item: any) => item.valueString || item.valueNumber || '');
        }

        if (Array.isArray(values) && Array.isArray(labels) && values.length === labels.length) {
          // Parse optional details data
          let detailsData: any[] = [];
          if (this.detailsPath && typeof this.detailsPath === 'string') {
            let details = this.processor.getData(this.component, this.detailsPath, this.surfaceId ?? 'default') as any;
            
            // Helper to check if value is Map-like (works with SignalMap too)
            const isMapLike = (val: any): boolean => {
              return val && typeof val.get === 'function' && typeof val.values === 'function' && typeof val.forEach === 'function';
            };
            
            // Helper function to recursively convert Map-like objects to plain object
            const mapToObject = (mapOrValue: any): any => {
              if (isMapLike(mapOrValue)) {
                const obj: Record<string, any> = {};
                mapOrValue.forEach((value: any, key: string) => {
                  obj[key] = mapToObject(value);
                });
                return obj;
              }
              return mapOrValue;
            };

            // Convert top-level Map-like to array of values
            if (isMapLike(details)) {
              detailsData = Array.from(details.values()).map(mapToObject);
            } else if (Array.isArray(details)) {
              // Process each item - might be objects with valueMap arrays
              detailsData = details.map((item: any) => {
                if (item && typeof item === 'object') {
                  // Check if item has valueMap property (raw A2UI JSON format)
                  if ('valueMap' in item && Array.isArray(item.valueMap)) {
                    const obj: Record<string, any> = {};
                    item.valueMap.forEach((entry: any) => {
                      if (entry && entry.key) {
                        obj[entry.key] = entry.valueString ?? entry.valueNumber ?? entry.valueBoolean ?? null;
                      }
                    });
                    return obj;
                  }
                  // Check if item itself is Map-like
                  if (isMapLike(item)) {
                    return mapToObject(item);
                  }
                  // Already a proper object
                  return item;
                }
                return {};
              });
            }
          }

          const total = values.reduce((sum: number, v: any) => sum + (typeof v === 'number' ? v : parseFloat(v) || 0), 0);
          barData = labels.map((label: any, i: number) => {
            const value = typeof values[i] === 'number' ? values[i] : parseFloat(values[i]) || 0;
            return {
              category: String(label),
              value,
              color: this.colorful ? BAR_COLORS[i % BAR_COLORS.length] : colors.oracle.primary,
              percentage: total > 0 ? (value / total) * 100 : 0,
              rank: i + 1,
              total: values.length,
              details: detailsData[i] || undefined
            };
          });
        }
      }
    }

    const maxValue = barData.length > 0 ? Math.max(...barData.map(b => b.value)) : 0;
    const totalValue = barData.reduce((sum, b) => sum + b.value, 0);

    if (!barData || barData.length === 0) {
      return html`
        <div class="empty-state">
          No chart data available
        </div>
      `;
    }

    return html`
      <div class="bar-chart">
        <div class="chart-title">${this.title}</div>
        <div class="bar-container" style="gap: 10px;">
          ${barData.map((item, index) => this.renderBar(item, index, maxValue, totalValue))}
        </div>
        <div class="legend">
          ${barData.map((item, index) => this.renderLegendItem(item, index, totalValue))}
        </div>
        ${this.renderDetailsPanel(totalValue, maxValue)}
      </div>
    `;
  }

  private renderBar(item: BarData, index: number, maxValue: number, totalValue: number) {
    const heightPercent = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
    const percentage = totalValue > 0 ? ((item.value / totalValue) * 100).toFixed(1) : '0';
    const isHovered = this.hoveredBar === index;
    const isSelected = this.selectedBar === index;
    const isDimmed = this.hoveredBar !== null && this.hoveredBar !== index;

    return html`
      <div 
        class="bar-item ${this.interactive ? 'interactive' : ''} ${isSelected ? 'selected' : ''} ${isDimmed ? 'dimmed' : ''}"
        @mouseenter=${() => this.handleBarHover(index)}
        @mouseleave=${() => this.handleBarHover(null)}
        @click=${() => this.handleBarClick({...item, rank: index + 1, total: totalValue}, index, totalValue)}
      >
        <div class="bar" style="height: ${heightPercent}%; background-color: ${item.color};">
          <div class="value-label">${this.formatValue(item.value)}</div>
          ${this.interactive ? html`
            <div class="bar-tooltip">
              <div class="tooltip-category">${item.category}</div>
              <div class="tooltip-value">${this.formatValue(item.value)}</div>
              <div class="tooltip-percent">${percentage}% of total</div>
            </div>
          ` : ''}
        </div>
        <div class="bar-label">${item.category}</div>
      </div>
    `;
  }

  private renderLegendItem(item: BarData, index: number, totalValue: number) {
    const isActive = this.selectedBar === index;
    const isDimmed = this.hoveredBar !== null && this.hoveredBar !== index;

    return html`
      <div 
        class="legend-item ${this.interactive ? 'interactive' : ''} ${isActive ? 'active' : ''} ${isDimmed ? 'dimmed' : ''}"
        @click=${() => this.handleBarClick(item, index, totalValue)}
        @mouseenter=${() => this.handleBarHover(index)}
        @mouseleave=${() => this.handleBarHover(null)}
      >
        <div class="legend-color" style="background-color: ${item.color};"></div>
        <span>${item.category}</span>
      </div>
    `;
  }

  private renderDetailsPanel(totalValue: number, maxValue: number) {
    if (!this.selectedBarData) return html`<div class="details-panel"></div>`;
    
    const data = this.selectedBarData;
    const hasCustomDetails = data.details && Object.keys(data.details).length > 0;

    return html`
      <div class="details-panel ${this.showDetails ? 'open' : ''}">
        <div class="details-header">
          <div class="details-title">
            <div class="details-color" style="background-color: ${data.color};"></div>
            ${data.category}
          </div>
          <button class="details-close" @click=${this.closeDetails}>✕</button>
        </div>
        <div class="details-body">
          ${hasCustomDetails 
            ? this.renderCustomDetails(data.details!) 
            : this.renderDefaultDetails(data, totalValue, maxValue)
          }
        </div>
        <div class="details-actions">
          <button class="details-action-btn" @click=${(e: Event) => this.handleQueueAction(e)}>
            ${this.getActionLabel(data)}
          </button>
        </div>
      </div>
    `;
  }

  private renderCustomDetails(details: Record<string, any>) {
    // Format label: convert camelCase/snake_case to Title Case
    const formatLabel = (key: string) => {
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^./, s => s.toUpperCase())
        .trim();
    };

    return Object.entries(details).map(([key, value]) => html`
      <div class="detail-item">
        <span class="detail-label">${formatLabel(key)}</span>
        <span class="detail-value ${typeof value === 'number' ? 'highlight' : 'small'}">
          ${typeof value === 'number' ? this.formatValue(value) : String(value)}
        </span>
      </div>
    `);
  }

  private renderDefaultDetails(data: BarData, totalValue: number, maxValue: number) {
    const percentage = data.percentage ?? (totalValue > 0 ? (data.value / totalValue) * 100 : 0);
    const percentOfMax = maxValue > 0 ? (data.value / maxValue) * 100 : 0;

    return html`
      <div class="detail-item">
        <span class="detail-label">Value</span>
        <span class="detail-value highlight">${this.formatValue(data.value)}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">Share of Total</span>
        <span class="detail-value">${percentage.toFixed(1)}%</span>
        <div class="detail-comparison">
          <div class="comparison-bar">
            <div class="comparison-fill" style="width: ${percentage}%; background-color: ${data.color};"></div>
          </div>
        </div>
      </div>
      <div class="detail-item">
        <span class="detail-label">Rank</span>
        <span class="detail-value small">#${data.rank} of ${data.total}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">vs Maximum</span>
        <span class="detail-value small">${percentOfMax.toFixed(0)}%</span>
        <div class="detail-comparison">
          <div class="comparison-bar">
            <div class="comparison-fill" style="width: ${percentOfMax}%; background-color: var(--oracle-primary);"></div>
          </div>
        </div>
      </div>
    `;
  }

  private closeDetails() {
    this.showDetails = false;
    this.selectedBar = null;
    this.selectedBarData = null;
  }

  private handleBarHover(index: number | null) {
    if (this.interactive) {
      this.hoveredBar = index;
    }
  }

  private handleBarClick(item: BarData, index: number, totalValue?: number) {
    if (!this.interactive) return;
    
    // Toggle selection and show details
    if (this.selectedBar === index) {
      this.closeDetails();
    } else {
      this.selectedBar = index;
      this.selectedBarData = {
        ...item,
        percentage: totalValue && totalValue > 0 ? (item.value / totalValue) * 100 : item.percentage
      };
      this.showDetails = true;
    }

    // Dispatch event
    this.dispatchEvent(new ItemSelectEvent(item, index));
    this.dispatchEvent(new CustomEvent('bar-select', {
      bubbles: true,
      composed: true,
      detail: { bar: item, index }
    }));
  }

  private getValidatedActionName(): string {
    const fallback = (this.actionFallbackName || "highlight_data").trim();
    const candidate = (this.action?.name || fallback).trim();
    const safeActionNamePattern = /^[a-z][a-z0-9_]{1,63}$/;

    if (!safeActionNamePattern.test(candidate)) {
      console.warn(
        `[BarGraph] Invalid action name "${candidate}". Falling back to "${fallback}".`
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

  private getActionLabel(bar: BarData): string {
    const detailLabel = bar.details?.actionLabel ?? bar.details?.action_label;
    if (typeof detailLabel === "string" && detailLabel.trim()) {
      return detailLabel.trim();
    }

    const configuredLabel = this.actionLabel?.trim();
    if (configuredLabel && configuredLabel.toLowerCase() !== "view details") {
      return configuredLabel;
    }

    return this.humanizeActionName(this.getValidatedActionName());
  }

  private handleQueueAction(e: Event) {
    e.stopPropagation();
    if (!this.selectedBarData || this.selectedBar === null) return;

    const bar = this.selectedBarData;
    const actionContext: Record<string, unknown> = {
      barIndex: this.selectedBar,
      category: bar.category,
      value: bar.value,
      percentage: bar.percentage ?? 0,
      rank: bar.rank ?? 0,
      totalBars: bar.total ?? 0,
      ...(bar.details ?? {}),
    };

    const contextEntries: NonNullable<v0_8.Types.Action["context"]> =
      Object.entries(actionContext).map(([key, value]) => {
        if (typeof value === "boolean") {
          return { key, value: { literalBoolean: value } };
        }
        if (typeof value === "number") {
          return { key, value: { literalNumber: value } };
        }
        return { key, value: { literalString: String(value) } };
      });

    const resolvedAction: v0_8.Types.Action = {
      name: this.getValidatedActionName(),
      context: [...(this.action?.context ?? []), ...contextEntries],
    };

    const evt = new v0_8.Events.StateEvent<"a2ui.action">({
      eventType: "a2ui.action",
      action: resolvedAction,
      dataContextPath: this.dataContextPath,
      sourceComponentId: this.id || "bar-graph",
      sourceComponent: this.component,
    });

    this.dispatchEvent(evt);
  }

  private formatValue(value: number): string {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toLocaleString();
  }
}
