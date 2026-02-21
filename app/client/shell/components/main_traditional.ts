import { LitElement, html, css } from "lit"
import { customElement, property } from "lit/decorators.js"
import { v0_8 } from "@a2ui/lit";
import "./stat_bar.js"
import { registerShellComponents } from "../ui/custom-components/register-components.js";
import { outageConfig } from "../configs/outage_config.js"

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
    :host {
      display: block;
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
      background: linear-gradient(135deg, #308792 0%, #0b788b 100%);
      border-radius: 1rem;
      padding: 0.5rem;
      color: white;
    }

    .tabs {
      display: flex;
      margin-bottom: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }

    .tab {
      padding: 0.75rem 1rem;
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.7);
      font-size: 1rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      border-bottom: 2px solid transparent;
    }

    .tab.active {
      color: white;
      border-bottom-color: white;
    }

    .tab:hover {
      color: white;
      background: rgba(255, 255, 255, 0.1);
    }

    .tab-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .chart-section {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 1rem;
    }

    .table-section {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 1rem;
      overflow-x: auto;
    }

    .timeline-section {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 1rem;
    }

    .map-section {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .map-description {
      font-size: 0.9rem;
      line-height: 1.5;
      color: rgba(255, 255, 255, 0.9);
    }

    .section-title {
      font-size: 1.2rem;
      font-weight: bold;
      margin-bottom: 1rem;
      color: white;
    }

    .action-buttons {
      display: flex;
      gap: 1rem;
      margin: 1rem 0;
      justify-content: center;
      flex-wrap: wrap;
    }

    .action-btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 0.5rem;
      font-size: 1rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s;
      color: white;
    }

    .energy-btn {
      background: #4CAF50;
    }

    .energy-btn:hover {
      background: #45a049;
      transform: translateY(-1px);
    }

    .industry-btn {
      background: #2196F3;
    }

    .industry-btn:hover {
      background: #1976D2;
      transform: translateY(-1px);
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
