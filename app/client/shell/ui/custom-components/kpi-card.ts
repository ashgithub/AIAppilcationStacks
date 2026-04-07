import { html, css } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { colors } from "../../theme/design-tokens.js";
import { KpiClickEvent } from "./detail-modal.js";
import "./detail-modal.js";

interface KpiData {
  label: string;
  value: number | string;
  unit?: string;
  change?: number;
  changeLabel?: string;
  icon?: string;
  color?: string;
  details?: Record<string, any>;
}

const KPI_THEMES: Record<string, { primary: string; bg: string }> = {
  cyan: { primary: colors.oracle.primary, bg: `rgba(136, 194, 255, 0.1)` },
  coral: { primary: colors.oracle.secondary, bg: `rgba(209, 101, 86, 0.1)` },
  teal: { primary: colors.semantic.success, bg: `rgba(16, 185, 129, 0.1)` },
  yellow: { primary: colors.oracle.accent, bg: `rgba(240, 204, 113, 0.1)` },
  purple: { primary: colors.chat.bgSecondary, bg: `rgba(126, 138, 164, 0.1)` },
  green: { primary: colors.semantic.successDark, bg: `rgba(5, 150, 105, 0.1)` },
  pink: { primary: colors.semantic.error, bg: `rgba(239, 68, 68, 0.1)` },
  orange: { primary: colors.semantic.warning, bg: `rgba(245, 158, 11, 0.1)` },
};

// Individual KPI card component.
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
  @property({ attribute: false }) accessor clickable: boolean = true;
  @property({ attribute: false }) accessor details: Record<string, any> = {};

  @state() accessor showDetails = false;
  @state() accessor currentKpiData: KpiData | null = null;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        flex: 0 1 auto;
        min-width: 180px;
        max-width: 280px;
        box-sizing: border-box;
        padding: var(--space-xs);
      }

      .kpi-card {
        background: var(--module-agent-bg);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        padding: var(--space-lg);
        min-height: 140px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        transition: transform var(--transition-normal), box-shadow var(--transition-normal);
      }

      .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
      }

      .kpi-card.clickable {
        cursor: pointer;
      }

      .kpi-card.clickable:active {
        transform: translateY(0);
      }

      .kpi-card.compact {
        padding: var(--space-sm);
      }

      .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--space-sm);
      }

      .kpi-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }

      .kpi-card.compact .kpi-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        font-size: 16px;
      }

      .kpi-label {
        font-size: 13px;
        font-weight: var(--font-weight-medium);
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        flex: 1;
      }

      .kpi-card.compact .kpi-label {
        font-size: 11px;
      }

      .kpi-value-container {
        margin-bottom: var(--space-sm);
      }

      .kpi-value {
        font-size: 32px;
        font-weight: var(--font-weight-bold);
        color: var(--text-primary);
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
        font-weight: var(--font-weight-medium);
        color: var(--text-secondary);
      }

      .kpi-card.compact .kpi-unit {
        font-size: 14px;
      }

      .kpi-change {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: var(--font-weight-medium);
        margin-top: auto;
      }

      .kpi-card.compact .kpi-change {
        font-size: 11px;
      }

      .kpi-change-positive {
        color: var(--color-success);
      }

      .kpi-change-negative {
        color: var(--color-error);
      }

      .kpi-change-neutral {
        color: var(--text-secondary);
      }

      .kpi-change-icon {
        font-size: 10px;
      }

      .kpi-change-label {
        color: var(--text-secondary);
        font-weight: var(--font-weight-normal);
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: var(--space-lg);
        font-style: italic;
        font-size: 12px;
      }

      .click-hint {
        font-size: 10px;
        color: var(--text-muted);
        text-align: center;
        margin-top: var(--space-sm);
        opacity: 0;
        transition: opacity var(--transition-normal);
      }

      .kpi-card.clickable:hover .click-hint {
        opacity: 1;
      }
    `,
  ];

  render() {
    let kpiData: KpiData | null = null;

    if (this.dataPath && typeof this.dataPath === 'string' && this.processor) {
      const rawData = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;
      
      if (rawData) {
        kpiData = this.parseKpiData(rawData);
      }
    }
    
    if (!kpiData && (this.label || this.value)) {
      kpiData = {
        label: this.label,
        value: this.value,
        unit: this.unit,
        change: this.change ?? undefined,
        changeLabel: this.changeLabel,
        icon: this.icon,
        color: this.colorTheme,
        details: this.details
      };
    }

    if (!kpiData) {
      return html`<div class="empty-state">No KPI data</div>`;
    }

    this.currentKpiData = kpiData;
    const themeColors = KPI_THEMES[kpiData.color || this.colorTheme] || KPI_THEMES.cyan;
    const changeClass = this.getChangeClass(kpiData.change);

    return html`
      <div class="kpi-card ${this.compact ? 'compact' : ''} ${this.clickable ? 'clickable' : ''}" @click=${this.handleClick}>
        <div class="kpi-header">
          <span class="kpi-label">${this.toDisplayText(kpiData.label) || '--'}</span>
          ${kpiData.icon ? html`
            <div class="kpi-icon" style="background: ${themeColors.bg}; color: ${themeColors.primary};">
              ${this.getIconSymbol(String(kpiData.icon))}
            </div>
          ` : ''}
        </div>
        <div class="kpi-value-container">
          <div class="kpi-value" style="color: ${themeColors.primary};">
            ${this.formatValue(kpiData.value)}
            ${kpiData.unit ? html`<span class="kpi-unit">${this.toDisplayText(kpiData.unit)}</span>` : ''}
          </div>
        </div>
        ${kpiData.change !== undefined ? html`
          <div class="kpi-change ${changeClass}">
            <span class="kpi-change-icon">${this.getChangeIcon(kpiData.change)}</span>
            ${Math.abs(kpiData.change)}%
            ${kpiData.changeLabel ? html`<span class="kpi-change-label">${kpiData.changeLabel}</span>` : ''}
          </div>
        ` : ''}
        ${this.clickable ? html`<div class="click-hint">Click for details</div>` : ''}
      </div>
      <detail-modal
        .open=${this.showDetails}
        .title=${(this.toDisplayText(kpiData.label) || 'KPI') + ' Details'}
        .position=${'modal'}
        .data=${this.getDetailData(kpiData)}
        @close=${this.closeDetails}
      ></detail-modal>
    `;
  }

  private handleClick() {
    if (this.clickable && this.currentKpiData) {
      this.showDetails = true;
      this.dispatchEvent(new KpiClickEvent(this.currentKpiData));
    }
  }

  private closeDetails() {
    this.showDetails = false;
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
      const parts = Object.entries(normalized)
        .map(([k, v]) => {
          const text = this.toDisplayText(v);
          return text ? `${k}: ${text}` : '';
        })
        .filter((item) => item.length > 0);
      return parts.join(', ');
    }
    return String(normalized).trim();
  }

  private getDetailData(kpiData: KpiData): Record<string, any> {
    const data: Record<string, any> = {
      'Metric': this.toDisplayText(kpiData.label) || '--',
      'Current Value': `${this.formatValue(kpiData.value)}${kpiData.unit ? ' ' + this.toDisplayText(kpiData.unit) : ''}`,
    };

    if (kpiData.change !== undefined) {
      data['Change'] = `${kpiData.change > 0 ? '+' : ''}${kpiData.change}%`;
      if (kpiData.changeLabel) {
        data['Period'] = kpiData.changeLabel;
      }
    }

    if (kpiData.details) {
      Object.entries(kpiData.details).forEach(([key, value]) => {
        const text = this.toDisplayText(value);
        if (text) data[key] = text;
      });
    }

    return data;
  }

  private parseKpiData(rawData: any): KpiData | null {
    // Keep known KPI keys out of the derived `details` payload.
    const standardFields = new Set(['label', 'value', 'unit', 'change', 'changeLabel', 'icon', 'color', 'colorTheme', 'details']);

    if (rawData instanceof Map) {
      const details: Record<string, any> = {};
      rawData.forEach((value, key) => {
        if (!standardFields.has(key)) {
          details[key] = value;
        }
      });
      return {
        label: rawData.get('label') || '',
        value: rawData.get('value') || 0,
        unit: rawData.get('unit'),
        change: rawData.get('change'),
        changeLabel: rawData.get('changeLabel'),
        icon: rawData.get('icon'),
        color: rawData.get('color') || rawData.get('colorTheme'),
        details: Object.keys(details).length > 0 ? details : rawData.get('details')
      };
    } else if (rawData.valueMap) {
      const result: KpiData = { label: '', value: 0 };
      const details: Record<string, any> = {};
      for (const kv of rawData.valueMap) {
        if (kv.key === 'label') result.label = kv.valueString || '';
        else if (kv.key === 'value') result.value = kv.valueNumber ?? kv.valueString ?? 0;
        else if (kv.key === 'unit') result.unit = kv.valueString;
        else if (kv.key === 'change') result.change = kv.valueNumber;
        else if (kv.key === 'changeLabel') result.changeLabel = kv.valueString;
        else if (kv.key === 'icon') result.icon = kv.valueString;
        else if (kv.key === 'color' || kv.key === 'colorTheme') result.color = kv.valueString;
        else if (kv.key === 'details' && kv.valueMap) {
          for (const detailKv of kv.valueMap) {
            details[detailKv.key] = detailKv.valueString ?? detailKv.valueNumber ?? detailKv.valueBool;
          }
        } else if (!standardFields.has(kv.key)) {
          details[kv.key] = kv.valueString ?? kv.valueNumber ?? kv.valueBool;
        }
      }
      if (Object.keys(details).length > 0) {
        result.details = details;
      }
      return result;
    } else if (typeof rawData === 'object') {
      const details: Record<string, any> = {};
      for (const key of Object.keys(rawData)) {
        if (!standardFields.has(key)) {
          details[key] = rawData[key];
        }
      }
      return {
        label: rawData.label || '',
        value: rawData.value || 0,
        unit: rawData.unit,
        change: rawData.change,
        changeLabel: rawData.changeLabel,
        icon: rawData.icon,
        color: rawData.color || rawData.colorTheme,
        details: Object.keys(details).length > 0 ? details : rawData.details
      };
    }
    return null;
  }

  private formatValue(value: any): string {
    const normalized = this.mapToObject(value);
    if (normalized === undefined || normalized === null || normalized === '') return '--';
    if (typeof normalized === 'string') {
      const trimmed = normalized.trim();
      if (!trimmed) return '--';
      const numeric = Number(trimmed);
      if (!Number.isNaN(numeric) && Number.isFinite(numeric)) {
        return this.formatValue(numeric);
      }
      return trimmed;
    }
    if (typeof normalized === 'boolean') return String(normalized);
    if (typeof normalized === 'number') {
      if (normalized >= 1000000) {
        return (normalized / 1000000).toFixed(1) + 'M';
      } else if (normalized >= 1000) {
        return (normalized / 1000).toFixed(1) + 'K';
      }
      return normalized.toLocaleString();
    }
    return this.toDisplayText(normalized) || '--';
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

  private getIconSymbol(icon: string): string {
    const iconMap: Record<string, string> = {
      'bolt': '⚡',
      'lightning': '⚡',
      'electricity': '⚡',
      'power': '⚡',
      'energy': '⚡',
      'dollar': '💰',
      'money': '💰',
      'revenue': '💰',
      'cost': '💰',
      'users': '👥',
      'people': '👥',
      'customers': '👥',
      'percent': '📈',
      'percentage': '📈',
      'growth': '📈',
      'trend': '📈',
      'temperature': '🌡️',
      'temp': '🌡️',
      'heat': '🌡️',
      'clock': '🕐',
      'time': '🕐',
      'duration': '🕐',
      'speed': '💨',
      'velocity': '💨',
      'fast': '💨',
      'car': '🚗',
      'vehicle': '🚗',
      'transport': '🚗',
      'home': '🏠',
      'house': '🏠',
      'building': '🏢',
      'factory': '🏭',
      'industry': '🏭',
      'production': '🏭'
    };
    return iconMap[icon.toLowerCase()] || '📊';
  }
}

// Renders a collection of KPI cards from a bound data set.
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
        padding: var(--space-sm) var(--space-xs);
        box-sizing: border-box;
      }

      .kpi-group {
        font-family: var(--font-family);
      }

      .kpi-group-title {
        font-size: 20px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin-bottom: var(--space-md);
        letter-spacing: 0.5px;
      }

      .kpi-group-container {
        display: flex;
        gap: 2px;
        flex-wrap: wrap;
        padding: 2px;
      }

      .kpi-group-container > * {
        flex: 0 1 auto;
      }

      .empty-state {
        text-align: center;
        color: var(--text-muted);
        padding: 40px var(--space-lg);
        font-style: italic;
        background: var(--module-agent-bg);
        border-radius: var(--radius-lg);
      }
    `,
  ];

  render() {
    let kpiItems: KpiData[] = [];

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
              .details=${item.details || {}}
            ></kpi-card>
          `)}
        </div>
      </div>
    `;
  }

  private parseItem(item: any, idx: number): KpiData | null {
    // Keep known KPI keys out of the derived `details` payload.
    const standardFields = new Set(['label', 'value', 'unit', 'change', 'changeLabel', 'icon', 'color', 'colorTheme', 'details']);

    if (item instanceof Map) {
      const details: Record<string, any> = {};
      item.forEach((value, key) => {
        if (!standardFields.has(key)) {
          details[key] = value;
        }
      });
      return {
        label: item.get('label') || `KPI ${idx + 1}`,
        value: item.get('value') || 0,
        unit: item.get('unit'),
        change: item.get('change'),
        changeLabel: item.get('changeLabel'),
        icon: item.get('icon'),
        color: item.get('color') || item.get('colorTheme'),
        details: Object.keys(details).length > 0 ? details : item.get('details')
      };
    } else if (item.valueMap) {
      const result: KpiData = { label: `KPI ${idx + 1}`, value: 0 };
      const details: Record<string, any> = {};
      for (const kv of item.valueMap) {
        if (kv.key === 'label') result.label = kv.valueString || result.label;
        else if (kv.key === 'value') result.value = kv.valueNumber ?? kv.valueString ?? 0;
        else if (kv.key === 'unit') result.unit = kv.valueString;
        else if (kv.key === 'change') result.change = kv.valueNumber;
        else if (kv.key === 'changeLabel') result.changeLabel = kv.valueString;
        else if (kv.key === 'icon') result.icon = kv.valueString;
        else if (kv.key === 'color' || kv.key === 'colorTheme') result.color = kv.valueString;
        else if (kv.key === 'details' && kv.valueMap) {
          for (const detailKv of kv.valueMap) {
            details[detailKv.key] = detailKv.valueString ?? detailKv.valueNumber ?? detailKv.valueBool;
          }
        } else if (!standardFields.has(kv.key)) {
          details[kv.key] = kv.valueString ?? kv.valueNumber ?? kv.valueBool;
        }
      }
      if (Object.keys(details).length > 0) {
        result.details = details;
      }
      return result;
    } else if (typeof item === 'object') {
      const details: Record<string, any> = {};
      for (const key of Object.keys(item)) {
        if (!standardFields.has(key)) {
          details[key] = item[key];
        }
      }
      return {
        label: item.label || `KPI ${idx + 1}`,
        value: item.value || 0,
        unit: item.unit,
        change: item.change,
        changeLabel: item.changeLabel,
        icon: item.icon,
        color: item.color || item.colorTheme,
        details: Object.keys(details).length > 0 ? details : item.details
      };
    }
    return null;
  }
}
