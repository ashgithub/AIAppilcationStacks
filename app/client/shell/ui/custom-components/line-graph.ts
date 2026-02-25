import { html, css, svg } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { colors } from "../../theme/design-tokens.js";

interface SeriesData {
  name: string;
  values: number[];
  color: string;
}

interface ChartPoint {
  x: number;
  y: number;
  value: number;
  label: string;
}

const SERIES_COLORS = [
  colors.oracle.primary,
  colors.oracle.secondary,
  colors.semantic.success, 
  colors.oracle.accent, 
  colors.chat.bgSecondary,    
  colors.semantic.warning,    
  colors.chat.bg,             
  colors.semantic.error,     
];

@customElement('line-graph')
export class LineGraph extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor labelPath: any = "";
  @property({ attribute: false }) accessor seriesPath: any = "";
  @property({ attribute: false }) accessor title: string = "Trend Analysis";
  @property({ attribute: false }) accessor showPoints: boolean = true;
  @property({ attribute: false }) accessor showArea: boolean = false;
  @property({ attribute: false }) accessor strokeWidth: number = 2;
  @property({ attribute: false }) accessor animated: boolean = true;

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

      .line-chart {
        width: 100%;
        font-family: var(--font-family);
      }

      .chart-title {
        text-align: center;
        margin-bottom: var(--space-xl);
        font-size: 20px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        letter-spacing: 0.5px;
      }

      .chart-wrapper {
        display: flex;
        align-items: flex-start;
      }

      .y-axis-labels {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 260px;
        padding-right: 10px;
        padding-top: 5px;
        padding-bottom: 5px;
      }

      .y-label {
        font-size: 11px;
        color: var(--text-secondary);
        text-align: right;
        min-width: 35px;
      }

      .chart-area {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .chart-container {
        position: relative;
        width: 100%;
        height: 260px;
        border-left: 1px solid var(--border-primary);
        border-bottom: 1px solid var(--border-primary);
      }

      .chart-svg {
        width: 100%;
        height: 100%;
        overflow: visible;
      }

      .grid-line {
        stroke: var(--border-secondary);
        stroke-width: 1;
        stroke-dasharray: 3, 6;
      }

      .data-line {
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
      }

      .data-line.animated {
        stroke-dasharray: 2000;
        stroke-dashoffset: 2000;
        animation: drawLine 1.5s ease-out forwards;
      }

      @keyframes drawLine {
        to {
          stroke-dashoffset: 0;
        }
      }

      .data-area {
        opacity: 0.15;
      }

      .data-area.animated {
        opacity: 0;
        animation: fadeInArea 0.8s ease-out 1s forwards;
      }

      @keyframes fadeInArea {
        to {
          opacity: 0.15;
        }
      }

      .data-point {
        cursor: pointer;
        transition: transform var(--transition-normal);
      }

      .data-point:hover {
        transform: scale(1.5);
      }

      .data-point.animated {
        opacity: 0;
        animation: fadeInPoint 0.3s ease-out forwards;
      }

      @keyframes fadeInPoint {
        to {
          opacity: 1;
        }
      }

      .x-axis-labels {
        display: flex;
        justify-content: space-between;
        padding-top: var(--space-sm);
        padding-left: 0;
        padding-right: 0;
      }

      .x-label {
        font-size: 11px;
        color: var(--text-secondary);
        text-align: center;
        flex: 1;
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: 40px var(--space-lg);
        font-style: italic;
      }

      .legend {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: var(--space-lg);
        margin-top: var(--space-xl);
        padding-top: var(--space-md);
        border-top: 1px solid var(--border-primary);
      }

      .legend-item {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        font-size: 13px;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 6px 12px;
        border-radius: var(--radius-xl);
        background: var(--surface-secondary);
        transition: all var(--transition-normal);
      }

      .legend-item:hover {
        background: var(--surface-elevated);
        transform: translateY(-2px);
      }

      .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
      }

      .legend-line {
        width: 24px;
        height: 3px;
        border-radius: var(--radius-sm);
      }
    `,
  ];

  render() {
    let series: SeriesData[] = [];
    let labels: string[] = [];

    // Resolve dataPath, labelPath, and seriesPath
    if (this.processor) {
      // Get labels
      if (this.labelPath && typeof this.labelPath === 'string') {
        let rawLabels = this.processor.getData(this.component, this.labelPath, this.surfaceId ?? 'default') as any;
        if (rawLabels instanceof Map) {
          labels = Array.from(rawLabels.values()).map(String);
        } else if (Array.isArray(rawLabels)) {
          labels = rawLabels.map((item: any) => {
            if (typeof item === 'object' && 'valueString' in item) return item.valueString;
            if (typeof item === 'object' && 'valueNumber' in item) return String(item.valueNumber);
            return String(item);
          });
        }
      }

      // Get series data - expects array of {name, values, color?}
      if (this.seriesPath && typeof this.seriesPath === 'string') {
        let rawSeries = this.processor.getData(this.component, this.seriesPath, this.surfaceId ?? 'default') as any;
        
        if (rawSeries instanceof Map) {
          rawSeries = Array.from(rawSeries.values());
        }

        if (Array.isArray(rawSeries)) {
          series = rawSeries.map((s: any, idx: number) => {
            let name = 'Series ' + (idx + 1);
            let values: number[] = [];
            let color = SERIES_COLORS[idx % SERIES_COLORS.length];

            if (s instanceof Map) {
              name = s.get('name') || name;
              color = s.get('color') || color;
              const vals = s.get('values');
              if (vals instanceof Map) {
                values = Array.from(vals.values()).map((v: any) => {
                  if (typeof v === 'object' && 'valueNumber' in v) return v.valueNumber;
                  return typeof v === 'number' ? v : parseFloat(v) || 0;
                });
              } else if (Array.isArray(vals)) {
                values = vals.map((v: any) => {
                  if (typeof v === 'object' && 'valueNumber' in v) return v.valueNumber;
                  return typeof v === 'number' ? v : parseFloat(v) || 0;
                });
              }
            } else if (typeof s === 'object') {
              name = s.name || s.valueString || name;
              color = s.color || color;
              
              // Handle nested valueMap structure
              if (Array.isArray(s)) {
                for (const kv of s) {
                  if (kv.key === 'name') name = kv.valueString || name;
                  if (kv.key === 'color') color = kv.valueString || color;
                  if (kv.key === 'values' && kv.valueMap) {
                    values = kv.valueMap.map((v: any) => v.valueNumber || 0);
                  }
                }
              } else if (s.valueMap) {
                for (const kv of s.valueMap) {
                  if (kv.key === 'name') name = kv.valueString || name;
                  if (kv.key === 'color') color = kv.valueString || color;
                  if (kv.key === 'values' && kv.valueMap) {
                    values = kv.valueMap.map((v: any) => v.valueNumber || 0);
                  }
                }
              } else {
                // Direct object with values array
                const vals = s.values;
                if (Array.isArray(vals)) {
                  values = vals.map((v: any) => {
                    if (typeof v === 'object' && 'valueNumber' in v) return v.valueNumber;
                    return typeof v === 'number' ? v : parseFloat(v) || 0;
                  });
                }
              }
            }

            return { name, values, color };
          });
        }
      } else if (this.dataPath && typeof this.dataPath === 'string') {
        // Fallback: single series from dataPath for backward compatibility
        let values = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;
        
        if (values instanceof Map) {
          values = Array.from(values.values());
        }
        
        if (Array.isArray(values)) {
          const numericValues = values.map((v: any) => {
            if (typeof v === 'object' && 'valueNumber' in v) return v.valueNumber;
            return typeof v === 'number' ? v : parseFloat(v) || 0;
          });
          series = [{ name: 'Data', values: numericValues, color: SERIES_COLORS[0] }];
        }
      }
    }

    if (series.length === 0 || labels.length === 0) {
      return html`
        <div class="empty-state">
          No chart data available
        </div>
      `;
    }

    // Calculate min/max across all series
    const allValues = series.flatMap(s => s.values);
    const maxValue = Math.max(...allValues);
    const minValue = Math.min(0, Math.min(...allValues)); // Always include 0
    const valueRange = maxValue - minValue || 1;

    // Add 10% padding to max
    const paddedMax = maxValue + valueRange * 0.1;
    const paddedRange = paddedMax - minValue;

    // Chart dimensions
    const chartWidth = 100; // percentage
    const chartHeight = 100; // percentage

    // Calculate points for each series
    const seriesPoints = series.map(s => {
      return s.values.map((value, i) => {
        const x = labels.length > 1 ? (i / (labels.length - 1)) * chartWidth : chartWidth / 2;
        const y = chartHeight - ((value - minValue) / paddedRange) * chartHeight;
        return { x, y, value, label: labels[i] || '' };
      });
    });

    // Y-axis labels (5 divisions)
    const yLabels = Array.from({ length: 5 }, (_, i) => {
      const value = minValue + (paddedRange * (4 - i) / 4);
      return Math.round(value * 10) / 10;
    });

    return html`
      <div class="line-chart">
        <div class="chart-title">${this.title}</div>
        <div class="chart-wrapper">
          <div class="y-axis-labels">
            ${yLabels.map(v => html`<span class="y-label">${this.formatValue(v)}</span>`)}
          </div>
          <div class="chart-area">
            <div class="chart-container">
              <svg class="chart-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <!-- Grid lines -->
                ${[0, 25, 50, 75, 100].map(y => svg`
                  <line class="grid-line" x1="0" y1="${y}" x2="100" y2="${y}" vector-effect="non-scaling-stroke" />
                `)}
                
                <!-- Render each series -->
                ${series.map((s, seriesIdx) => this.renderSeries(s, seriesPoints[seriesIdx], chartHeight, minValue, paddedRange, seriesIdx))}
              </svg>
            </div>
            <div class="x-axis-labels">
              ${labels.map(l => html`<span class="x-label">${l}</span>`)}
            </div>
          </div>
        </div>
        
        <div class="legend">
          ${series.map(s => html`
            <div class="legend-item">
              <div class="legend-dot" style="background-color: ${s.color}; color: ${s.color};"></div>
              <span>${s.name}</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }

  private formatValue(value: number): string {
    if (Math.abs(value) >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (Math.abs(value) >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toFixed(0);
  }

  private renderSeries(series: SeriesData, points: ChartPoint[], chartHeight: number, _minValue: number, _range: number, seriesIdx: number) {
    if (points.length === 0) return '';

    const linePath = this.createSmoothPath(points);
    
    // Create area path
    const areaPath = `${linePath} L ${points[points.length - 1].x} ${chartHeight} L ${points[0].x} ${chartHeight} Z`;

    return svg`
      <!-- Area fill (if enabled) -->
      ${this.showArea ? svg`
        <path 
          class="data-area ${this.animated ? 'animated' : ''}" 
          d="${areaPath}" 
          fill="${series.color}"
          vector-effect="non-scaling-stroke"
        />
      ` : ''}
      
      <!-- Line -->
      <path 
        class="data-line ${this.animated ? 'animated' : ''}" 
        d="${linePath}" 
        stroke="${series.color}" 
        stroke-width="${this.strokeWidth}"
        vector-effect="non-scaling-stroke"
        style="animation-delay: ${seriesIdx * 0.2}s; color: ${series.color};"
      />
      
      <!-- Data points -->
      ${this.showPoints ? points.map((p, i) => svg`
        <circle 
          class="data-point ${this.animated ? 'animated' : ''}" 
          cx="${p.x}" 
          cy="${p.y}" 
          r="0.8"
          fill="${series.color}"
          stroke="#1a1a2e"
          stroke-width="0.3"
          vector-effect="non-scaling-stroke"
          style="animation-delay: ${seriesIdx * 0.2 + 1 + i * 0.1}s; color: ${series.color};"
        >
          <title>${series.name}: ${p.label} = ${p.value}</title>
        </circle>
      `) : ''}
    `;
  }

  private createSmoothPath(points: ChartPoint[]): string {
    if (points.length < 2) {
      return points.length === 1 ? `M ${points[0].x} ${points[0].y}` : '';
    }

    // Use simple line segments for cleaner look
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  }
}
