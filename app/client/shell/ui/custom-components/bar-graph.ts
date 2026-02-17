import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";

interface BarData {
  category: string;
  value: number;
  color: string;
}

@customElement('bar-graph')
export class BarGraph extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor labelPath: any = "";
  @property({ attribute: false }) accessor orientation: string = 'vertical';
  @property({ attribute: false }) accessor barWidth: number = 0.2;
  @property({ attribute: false }) accessor gap: number = 0.1;

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
        overflow-x: auto;
      }

      .bar-chart {
        width: 100%;
        font-family: Arial, sans-serif;
      }

      .chart-title {
        text-align: center;
        margin-bottom: 20px;
        font-size: 18px;
        font-weight: 600;
        color: #333;
      }

      .bar-container {
        display: flex;
        align-items: end;
        justify-content: space-around;
        height: 300px;
        margin-bottom: 40px;
        padding: 0 20px;
      }

      .bar-item {
        flex: 1;
        position: relative;
        height: 100%;
      }

      .bar {
        width: 100%;
        border-radius: 4px 4px 0 0;
        transition: height 0.3s ease;
        position: absolute;
        bottom: 0;
      }

      .bar-label {
        position: absolute;
        bottom: -25px;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        font-size: 12px;
        font-weight: 500;
        color: #666;
        max-width: 80px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .value-label {
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        font-weight: 600;
        color: #333;
        background: rgba(255, 255, 255, 0.9);
        padding: 2px 4px;
        border-radius: 3px;
        white-space: nowrap;
      }

      .empty-state {
        text-align: center;
        color: #666;
        padding: 20px;
        font-style: italic;
      }

      .legend {
        display: flex;
        justify-content: center;
        flex-wrap: nowrap;
        gap: 15px;
        margin-top: 20px;
      }

      .legend-item {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
        color: #666;
      }

      .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
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
          barData = labels.map((label: any, i: number) => ({
            category: String(label),
            value: typeof values[i] === 'number' ? values[i] : parseFloat(values[i]) || 0,
            color: '#4CAF50' // Default color, could be extended to support custom colors
          }));
        }
      }
    }

    const maxValue = barData.length > 0 ? Math.max(...barData.map(b => b.value)) : 0;

    if (!barData || barData.length === 0) {
      return html`
        <div class="empty-state">
          No chart data available
        </div>
      `;
    }

    return html`
      <div class="bar-chart">
        <div class="chart-title">Data Comparison</div>
        <div class="bar-container" style="gap: 10px;">
          ${barData.map((item) => this.renderBar(item, maxValue))}
        </div>
        <div class="legend">
          ${barData.map(item => this.renderLegendItem(item))}
        </div>
      </div>
    `;
  }

  private renderBar(item: BarData, maxValue: number) {
    const heightPercent = maxValue > 0 ? (item.value / maxValue) * 100 : 0;

    return html`
      <div class="bar-item">
        <div class="bar" style="height: ${heightPercent}%; background-color: ${item.color};">
          <div class="value-label">${item.value}</div>
        </div>
        <div class="bar-label">${item.category}</div>
      </div>
    `;
  }

  private renderLegendItem(item: BarData) {
    return html`
      <div class="legend-item">
        <div class="legend-color" style="background-color: ${item.color};"></div>
        <span>${item.category}</span>
      </div>
    `;
  }
}