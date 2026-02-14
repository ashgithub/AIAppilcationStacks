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
        margin-bottom: 20px;
        padding: 0 20px;
      }

      .bar-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        margin: 0 5px;
      }

      .bar {
        width: 100%;
        min-height: 10px;
        border-radius: 4px 4px 0 0;
        transition: height 0.3s ease;
        position: relative;
      }

      .bar-label {
        text-align: center;
        margin-top: 8px;
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
        flex-wrap: wrap;
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
    console.log('BarGraph render called with:', {
      dataPath: this.dataPath,
      labelPath: this.labelPath,
      orientation: this.orientation,
      barWidth: this.barWidth,
      gap: this.gap
    });

    let barData: BarData[] = [];

    // Resolve dataPath
    if (this.dataPath && typeof this.dataPath === 'string') {
      if (this.processor) {
        const rawData = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;
        let data: any = {};
        if (rawData instanceof Map) {
          // Handle resolved Map format from A2UI processor
          for (const [key, value] of rawData.entries()) {
            if (value instanceof Map) {
              // Nested Maps (categories, values, colors) are converted to arrays
              data[key] = Array.from(value.values());
            } else {
              data[key] = value;
            }
          }
        } else if (Array.isArray(rawData)) {
          // Fallback: Parse raw valueMap format: array of {key, valueString/valueNumber/...}
          for (const entry of rawData) {
            if (entry.key === 'categories' || entry.key === 'values' || entry.key === 'colors') {
              // Sub valueMap
              const subMap: any = {};
              if (entry.valueMap && Array.isArray(entry.valueMap)) {
                for (const subEntry of entry.valueMap) {
                  subMap[subEntry.key] = subEntry.valueString || subEntry.valueNumber || subEntry.valueBoolean || '';
                }
              }
              data[entry.key] = Object.values(subMap); // Convert to array
            } else {
              data[entry.key] = entry.valueString || entry.valueNumber || entry.valueBoolean || '';
            }
          }
        } else if (rawData && typeof rawData === 'object') {
          data = rawData;
        }
        const categories = data.categories;
        const values = data.values;
        const colors = data.colors || [];
        if (Array.isArray(categories) && Array.isArray(values)) {
          barData = categories.map((cat: any, i: number) => ({
            category: String(cat),
            value: typeof values[i] === 'number' ? values[i] : parseFloat(values[i]) || 0,
            color: Array.isArray(colors) && colors[i] ? String(colors[i]) : '#4CAF50'
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
        <div class="bar-container" style="gap: ${this.gap || 0}px;">
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