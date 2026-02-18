import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";

interface KpiData {
  label: string;
  value: number | string;
  unit?: string;
  change?: number;
  changeLabel?: string;
  icon?: string;
  color?: string;
}

// Preset color themes for KPI cards
const KPI_THEMES: Record<string, { primary: string; bg: string }> = {
  cyan: { primary: '#00D4FF', bg: 'rgba(0, 212, 255, 0.1)' },
  coral: { primary: '#FF6B6B', bg: 'rgba(255, 107, 107, 0.1)' },
  teal: { primary: '#4ECDC4', bg: 'rgba(78, 205, 196, 0.1)' },
  yellow: { primary: '#FFE66D', bg: 'rgba(255, 230, 109, 0.1)' },
  purple: { primary: '#AA96DA', bg: 'rgba(170, 150, 218, 0.1)' },
  green: { primary: '#95E1D3', bg: 'rgba(149, 225, 211, 0.1)' },
  pink: { primary: '#FCBAD3', bg: 'rgba(252, 186, 211, 0.1)' },
  orange: { primary: '#F38181', bg: 'rgba(243, 129, 129, 0.1)' },
};

/**
 * Single KPI Card component
 * Can be used standalone or within a KpiCardGroup
 */
@customElement('kpi-card')
export class KpiCard extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor label: string = "";
  @property({ attribute: false }) accessor value: any = "";
  @property({ attribute: false }) accessor unit: string = "";
  @property({ attribute: false }) accessor change: number | null = null;
  @property({ attribute: false }) accessor changeLabel: string = "";
  @property({ attribute: false }) accessor icon: string = "";
  @property({ attribute: false }) accessor colorTheme: string = "cyan";
  @property({ attribute: false }) accessor compact: boolean = false;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        flex: 1;
        min-width: 180px;
      }

      .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        padding: 20px;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }

      .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5);
      }

      .kpi-card.compact {
        padding: 16px;
      }

      .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .kpi-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }

      .kpi-card.compact .kpi-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        font-size: 16px;
      }

      .kpi-label {
        font-size: 13px;
        font-weight: 500;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        flex: 1;
      }

      .kpi-card.compact .kpi-label {
        font-size: 11px;
      }

      .kpi-value-container {
        margin-bottom: 8px;
      }

      .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        display: flex;
        align-items: baseline;
        gap: 6px;
      }

      .kpi-card.compact .kpi-value {
        font-size: 26px;
      }

      .kpi-unit {
        font-size: 16px;
        font-weight: 500;
        color: #8892b0;
      }

      .kpi-card.compact .kpi-unit {
        font-size: 14px;
      }

      .kpi-change {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 500;
        margin-top: auto;
      }

      .kpi-card.compact .kpi-change {
        font-size: 11px;
      }

      .kpi-change-positive {
        color: #4ECDC4;
      }

      .kpi-change-negative {
        color: #FF6B6B;
      }

      .kpi-change-neutral {
        color: #8892b0;
      }

      .kpi-change-icon {
        font-size: 10px;
      }

      .kpi-change-label {
        color: #8892b0;
        font-weight: 400;
      }

      .empty-state {
        text-align: center;
        color: #8892b0;
        padding: 20px;
        font-style: italic;
        font-size: 12px;
      }
    `,
  ];

  render() {
    let kpiData: KpiData | null = null;

    // If dataPath is provided, fetch data from processor
    if (this.dataPath && typeof this.dataPath === 'string' && this.processor) {
      const rawData = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;
      
      if (rawData) {
        kpiData = this.parseKpiData(rawData);
      }
    }
    
    // Otherwise, use direct properties
    if (!kpiData && (this.label || this.value)) {
      kpiData = {
        label: this.label,
        value: this.value,
        unit: this.unit,
        change: this.change ?? undefined,
        changeLabel: this.changeLabel,
        icon: this.icon,
        color: this.colorTheme
      };
    }

    if (!kpiData) {
      return html`<div class="empty-state">No KPI data</div>`;
    }

    const themeColors = KPI_THEMES[kpiData.color || this.colorTheme] || KPI_THEMES.cyan;
    const changeClass = this.getChangeClass(kpiData.change);

    return html`
      <div class="kpi-card ${this.compact ? 'compact' : ''}">
        <div class="kpi-header">
          <span class="kpi-label">${kpiData.label}</span>
          ${kpiData.icon ? html`
            <div class="kpi-icon" style="background: ${themeColors.bg}; color: ${themeColors.primary};">
              ${kpiData.icon}
            </div>
          ` : ''}
        </div>
        <div class="kpi-value-container">
          <div class="kpi-value" style="color: ${themeColors.primary};">
            ${this.formatValue(kpiData.value)}
            ${kpiData.unit ? html`<span class="kpi-unit">${kpiData.unit}</span>` : ''}
          </div>
        </div>
        ${kpiData.change !== undefined ? html`
          <div class="kpi-change ${changeClass}">
            <span class="kpi-change-icon">${this.getChangeIcon(kpiData.change)}</span>
            ${Math.abs(kpiData.change)}%
            ${kpiData.changeLabel ? html`<span class="kpi-change-label">${kpiData.changeLabel}</span>` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }

  private parseKpiData(rawData: any): KpiData | null {
    if (rawData instanceof Map) {
      return {
        label: rawData.get('label') || '',
        value: rawData.get('value') || 0,
        unit: rawData.get('unit'),
        change: rawData.get('change'),
        changeLabel: rawData.get('changeLabel'),
        icon: rawData.get('icon'),
        color: rawData.get('color')
      };
    } else if (rawData.valueMap) {
      const result: KpiData = { label: '', value: 0 };
      for (const kv of rawData.valueMap) {
        if (kv.key === 'label') result.label = kv.valueString || '';
        if (kv.key === 'value') result.value = kv.valueNumber ?? kv.valueString ?? 0;
        if (kv.key === 'unit') result.unit = kv.valueString;
        if (kv.key === 'change') result.change = kv.valueNumber;
        if (kv.key === 'changeLabel') result.changeLabel = kv.valueString;
        if (kv.key === 'icon') result.icon = kv.valueString;
        if (kv.key === 'color') result.color = kv.valueString;
      }
      return result;
    } else if (typeof rawData === 'object') {
      return {
        label: rawData.label || '',
        value: rawData.value || 0,
        unit: rawData.unit,
        change: rawData.change,
        changeLabel: rawData.changeLabel,
        icon: rawData.icon,
        color: rawData.color
      };
    }
    return null;
  }

  private formatValue(value: number | string): string {
    if (typeof value === 'number') {
      if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
      } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
      }
      return value.toLocaleString();
    }
    return String(value);
  }

  private getChangeClass(change?: number): string {
    if (change === undefined) return '';
    if (change > 0) return 'kpi-change-positive';
    if (change < 0) return 'kpi-change-negative';
    return 'kpi-change-neutral';
  }

  private getChangeIcon(change?: number): string {
    if (change === undefined) return '';
    if (change > 0) return '▲';
    if (change < 0) return '▼';
    return '●';
  }
}

/**
 * KPI Card Group - renders multiple KPI cards in a flexible row
 * Use native A2UI Row/Column components for more complex layouts
 */
@customElement('kpi-card-group')
export class KpiCardGroup extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor title: string = "";
  @property({ attribute: false }) accessor compact: boolean = false;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        margin: 8px;
      }

      .kpi-group {
        font-family: 'Segoe UI', Arial, sans-serif;
      }

      .kpi-group-title {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 16px;
        letter-spacing: 0.5px;
      }

      .kpi-group-container {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
      }

      .kpi-group-container > * {
        flex: 1 1 200px;
        min-width: 180px;
      }

      .empty-state {
        text-align: center;
        color: #8892b0;
        padding: 40px 20px;
        font-style: italic;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
      }
    `,
  ];

  render() {
    let kpiItems: KpiData[] = [];

    // Resolve dataPath
    if (this.dataPath && typeof this.dataPath === 'string' && this.processor) {
      let rawData = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;

      if (rawData instanceof Map) {
        rawData = Array.from(rawData.values());
      }

      if (Array.isArray(rawData)) {
        kpiItems = rawData.map((item: any, idx: number) => this.parseItem(item, idx)).filter(Boolean) as KpiData[];
      }
    }

    if (kpiItems.length === 0) {
      return html`
        <div class="kpi-group">
          ${this.title ? html`<div class="kpi-group-title">${this.title}</div>` : ''}
          <div class="empty-state">No KPI data available</div>
        </div>
      `;
    }

    const colors = ['cyan', 'coral', 'teal', 'yellow', 'purple', 'green', 'pink', 'orange'];

    return html`
      <div class="kpi-group">
        ${this.title ? html`<div class="kpi-group-title">${this.title}</div>` : ''}
        <div class="kpi-group-container">
          ${kpiItems.map((item, idx) => html`
            <kpi-card
              .label=${item.label}
              .value=${item.value}
              .unit=${item.unit || ''}
              .change=${item.change ?? null}
              .changeLabel=${item.changeLabel || ''}
              .icon=${item.icon || ''}
              .colorTheme=${item.color || colors[idx % colors.length]}
              .compact=${this.compact}
            ></kpi-card>
          `)}
        </div>
      </div>
    `;
  }

  private parseItem(item: any, idx: number): KpiData | null {
    if (item instanceof Map) {
      return {
        label: item.get('label') || `KPI ${idx + 1}`,
        value: item.get('value') || 0,
        unit: item.get('unit'),
        change: item.get('change'),
        changeLabel: item.get('changeLabel'),
        icon: item.get('icon'),
        color: item.get('color')
      };
    } else if (item.valueMap) {
      const result: KpiData = { label: `KPI ${idx + 1}`, value: 0 };
      for (const kv of item.valueMap) {
        if (kv.key === 'label') result.label = kv.valueString || result.label;
        if (kv.key === 'value') result.value = kv.valueNumber ?? kv.valueString ?? 0;
        if (kv.key === 'unit') result.unit = kv.valueString;
        if (kv.key === 'change') result.change = kv.valueNumber;
        if (kv.key === 'changeLabel') result.changeLabel = kv.valueString;
        if (kv.key === 'icon') result.icon = kv.valueString;
        if (kv.key === 'color') result.color = kv.valueString;
      }
      return result;
    } else if (typeof item === 'object') {
      return {
        label: item.label || `KPI ${idx + 1}`,
        value: item.value || 0,
        unit: item.unit,
        change: item.change,
        changeLabel: item.changeLabel,
        icon: item.icon,
        color: item.color
      };
    }
    return null;
  }
}
