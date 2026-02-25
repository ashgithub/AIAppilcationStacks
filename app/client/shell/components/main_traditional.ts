import { LitElement, html, css } from "lit"
import { customElement, property } from "lit/decorators.js"
import { v0_8 } from "@a2ui/lit";
import "./stat_bar.js"
import { registerShellComponents } from "../ui/custom-components/register-components.js";
import { outageConfig } from "../configs/outage_config.js"
import { designTokensCSS, colors, radius } from "../theme/design-tokens.js"

registerShellComponents();

@customElement("static-module")
export class StaticModule extends LitElement {
  @property({ type: String }) accessor currentTab = 'summary';
  @property({ attribute: false }) accessor component: any = this;

  private processor = v0_8.Data.createSignalA2uiMessageProcessor();

  connectedCallback() {
    super.connectedCallback();
    this.initializeData();
  }

  private async initializeData() {
    try {
      const response = await fetch('http://localhost:10002/traditional');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const messages: v0_8.Types.ServerToClientMessage[] = await response.json();
      this.processor.processMessages(messages);
    } catch (error) {
      console.error('Failed to fetch outage data from server:', error);
      // Fallback to static data for demo
      this.initializeStaticData();
    }
  }

  private async fetchData(endpoint: string) {
    try {
      const response = await fetch(`http://localhost:10002${endpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const messages: v0_8.Types.ServerToClientMessage[] = await response.json();
      this.processor.processMessages(messages);
      this.requestUpdate();
    } catch (error) {
      console.error(`Failed to fetch data from ${endpoint}:`, error);
    }
  }

  private async loadEnergyTrends() {
    await this.fetchData('/traditional/trends');
  }

  private async loadTimeline() {
    await this.fetchData('/traditional/timeline');
  }

  private async loadIndustryData() {
    await this.fetchData('/traditional/industry');
  }

  private hasEnergyTrends(): boolean {
    return !!this.processor.getData(this.component, "/trends/energyTrend");
  }

  private hasTimeline(): boolean {
    return !!this.processor.getData(this.component, "/timeline/timelineEvents");
  }

  private hasIndustry(): boolean {
    return !!this.processor.getData(this.component, "/industry/industryTable");
  }

  private initializeStaticData() {
    // Create static outage data messages (fallback)
    const messages: v0_8.Types.ServerToClientMessage[] = [
      {
        dataModelUpdate: {
          surfaceId: 'default',
          path: '/',
          contents: [
            {
              key: 'outageSummary',
              valueMap: [
                { key: '0', valueNumber: 25 },
                { key: '1', valueNumber: 15 },
                { key: '2', valueNumber: 8 },
                { key: '3', valueNumber: 3 }
              ]
            },
            {
              key: 'outageSummaryLabels',
              valueMap: [
                { key: '0', valueString: 'Active' },
                { key: '1', valueString: 'Investigating' },
                { key: '2', valueString: 'Resolved' },
                { key: '3', valueString: 'Scheduled' }
              ]
            },
            {
              key: 'outageTable',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'id', valueString: 'OUT-001' },
                  { key: 'location', valueString: 'Downtown Grid' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'severity', valueString: 'High' },
                  { key: 'startTime', valueString: '2024-01-15T14:30:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-15T18:00:00Z' },
                  { key: 'affectedCustomers', valueNumber: 1250 }
                ]},
                { key: '1', valueMap: [
                  { key: 'id', valueString: 'OUT-002' },
                  { key: 'location', valueString: 'North Substation' },
                  { key: 'status', valueString: 'Investigating' },
                  { key: 'severity', valueString: 'Medium' },
                  { key: 'startTime', valueString: '2024-01-15T12:15:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-15T16:30:00Z' },
                  { key: 'affectedCustomers', valueNumber: 850 }
                ]},
                { key: '2', valueMap: [
                  { key: 'id', valueString: 'OUT-003' },
                  { key: 'location', valueString: 'East District' },
                  { key: 'status', valueString: 'Resolved' },
                  { key: 'severity', valueString: 'Low' },
                  { key: 'startTime', valueString: '2024-01-14T09:45:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-14T11:20:00Z' },
                  { key: 'affectedCustomers', valueNumber: 320 }
                ]}
              ]
            },
            {
              key: 'timelineEvents',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'date', valueString: '2024-01-15T14:30:00Z' },
                  { key: 'title', valueString: 'Power Outage Reported' },
                  { key: 'description', valueString: 'Downtown Grid experiencing widespread outage' }
                ]},
                { key: '1', valueMap: [
                  { key: 'date', valueString: '2024-01-15T12:15:00Z' },
                  { key: 'title', valueString: 'North Substation Issue' },
                  { key: 'description', valueString: 'Investigating potential equipment failure' }
                ]},
                { key: '2', valueMap: [
                  { key: 'date', valueString: '2024-01-14T09:45:00Z' },
                  { key: 'title', valueString: 'East District Restored' },
                  { key: 'description', valueString: 'Power fully restored to all affected areas' }
                ]}
              ]
            },
            {
              key: 'mapMarkers',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'name', valueString: 'Downtown Grid' },
                  { key: 'latitude', valueNumber: 40.7589 },
                  { key: 'longitude', valueNumber: -73.9851 },
                  { key: 'description', valueString: 'Active outage affecting 1250 customers' }
                ]},
                { key: '1', valueMap: [
                  { key: 'name', valueString: 'North Substation' },
                  { key: 'latitude', valueNumber: 40.7829 },
                  { key: 'longitude', valueNumber: -73.9654 },
                  { key: 'description', valueString: 'Under investigation' }
                ]},
                { key: '2', valueMap: [
                  { key: 'name', valueString: 'East District' },
                  { key: 'latitude', valueNumber: 40.7505 },
                  { key: 'longitude', valueNumber: -73.9934 },
                  { key: 'description', valueString: 'Restored - monitoring for issues' }
                ]}
              ]
            }
          ]
        }
      }
    ];

    this.processor.processMessages(messages);
  }
  static styles = css`
    ${designTokensCSS}

    :host {
      display: block;
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
      background: var(--module-traditional-bg);
      border-radius: var(--radius-xl);
      padding: var(--space-sm);
      color: var(--text-primary);
    }

    .tabs {
      display: flex;
      margin-bottom: var(--space-md);
      border-bottom: 1px solid var(--border-secondary);
    }

    .tab {
      padding: var(--space-sm) var(--space-md);
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      transition: all var(--transition-slow);
      border-bottom: 2px solid transparent;
    }

    .tab.active {
      color: var(--oracle-secondary);
      border-bottom-color: var(--oracle-secondary);
    }

    .tab:hover {
      color: var(--text-primary);
      background: var(--module-traditional-active);
    }

    .tab-content {
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
    }

    .chart-section {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
    }

    .table-section {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
      overflow-x: auto;
    }

    .timeline-section {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
    }

    .map-section {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
    }

    .map-description {
      font-size: var(--font-size-sm);
      line-height: var(--line-height-normal);
      color: var(--text-secondary);
    }

    .section-title {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-bold);
      margin-bottom: var(--space-md);
      color: var(--text-primary);
    }

    .action-buttons {
      display: flex;
      gap: var(--space-md);
      margin: var(--space-md) 0;
      justify-content: center;
      flex-wrap: wrap;
    }

    .action-btn {
      padding: var(--space-sm) var(--space-lg);
      border: none;
      border-radius: var(--radius-md);
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      transition: all var(--transition-slow);
      color: var(--neutral-white);
    }

    .energy-btn {
      background: var(--oracle-secondary);
    }

    .energy-btn:hover {
      background: #b8524a;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(209, 101, 86, 0.4);
    }

    .industry-btn {
      background: var(--oracle-primary);
      color: var(--neutral-900);
    }

    .industry-btn:hover {
      background: #6ab0f5;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(136, 194, 255, 0.4);
    }
  `

  render() {
    return html`
      <stat-bar .title=${"Outage Monitoring"} .time=${""} .tokens=${""} .configUrl=${"/outage_config"} .configType=${"traditional"} .configData=${outageConfig}></stat-bar>
      <div class="tabs">
        <button class="tab ${this.currentTab === 'summary' ? 'active' : ''}" @click=${() => this.switchTab('summary')}>
          Energy Summary
        </button>
        <button class="tab ${this.currentTab === 'details' ? 'active' : ''}" @click=${() => this.switchTab('details')}>
          Outages Details
        </button>
        <button class="tab ${this.currentTab === 'map' ? 'active' : ''}" @click=${() => this.switchTab('map')}>
          Outage Map
        </button>
      </div>
      <div class="tab-content">
        ${this.renderTabContent()}
      </div>
    `
  }

  private switchTab(tab: string) {
    this.currentTab = tab;
  }

  private renderTabContent() {
    switch (this.currentTab) {
      case 'summary':
        return this.renderSummaryTab();
      case 'details':
        return this.renderDetailsTab();
      case 'map':
        return this.renderMapTab();
      default:
        return this.renderSummaryTab();
    }
  }

  private renderSummaryTab() {
    return html`
      <div class="chart-section">
        <div class="section-title">Energy Consumption Overview</div>
        <kpi-card-group .dataPath=${"/energyKPIs"} .title=${"Energy Metrics"} .processor=${this.processor} .component=${this}></kpi-card-group>
      </div>
      <div class="chart-section">
        <div class="section-title">Energy Production Trends</div>
        <line-graph .seriesPath=${"/trends/energyTrend"} .labelPath=${"/trends/energyTrendLabels"} .title=${"Monthly Production by Source"} .processor=${this.processor} .component=${this}></line-graph>
        ${!this.hasEnergyTrends() ? html`<button @click=${this.loadEnergyTrends} class="action-btn energy-btn">Load Energy Trends</button>` : ''}
      </div>
    `;
  }

  private renderDetailsTab() {
    return html`
      <div class="table-section">
        <div class="section-title">Outage Details by Location</div>
        <outage-table .dataPath=${"/outageTable"} .title=${"Outage Details"} .processor=${this.processor} .component=${this}></outage-table>
      </div>
      <div class="timeline-section">
        <div class="section-title">Outage Timeline</div>
        <timeline-component .dataPath=${"/timeline/timelineEvents"} .processor=${this.processor} .component=${this}></timeline-component>
        ${!this.hasTimeline() ? html`<button @click=${this.loadTimeline} class="action-btn">Load Timeline</button>` : ''}
      </div>
      <div class="table-section">
        <div class="section-title">Industry Performance Metrics</div>
        <outage-table .dataPath=${"/industry/industryTable"} .title=${"Industry Data"} .processor=${this.processor} .component=${this}></outage-table>
        ${!this.hasIndustry() ? html`<button @click=${this.loadIndustryData} class="action-btn industry-btn">Load Industry Data</button>` : ''}
      </div>
    `;
  }

  private renderMapTab() {
    return html`
      <div class="map-section">
        <div class="section-title">Outage Locations</div>
        <map-component .dataPath=${"/mapMarkers"} .centerLat=${38} .centerLng=${-120} .zoom=${5} .processor=${this.processor} .component=${this}></map-component>
        <div class="map-description">
          <p>This map shows the current locations of reported power outages in the service area. Red markers indicate active outages, with popup details showing affected customers and status.</p>
          <p>Click on any marker to view more information about that specific outage location.</p>
        </div>
      </div>
    `;
  }


}

declare global {
  interface HTMLElementTagNameMap {
    "static-module": StaticModule
  }
}
