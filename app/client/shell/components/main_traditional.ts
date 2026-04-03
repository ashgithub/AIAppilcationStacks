import { LitElement, html, css } from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { v0_8 } from "@a2ui/lit";
import { A2UIRouter, routerContext } from "../services/a2ui-router.js";
import { buildServerUrl } from "../services/server-endpoints.js";
import "./stat_bar.js"
import { registerShellComponents } from "../ui/custom-components/register-components.js";
import { outageConfig } from "../configs/outage_config.js"
import { designTokensCSS, buttonStyles, colors, radius } from "../theme/design-tokens.js"
import { ItemSelectEvent, KpiClickEvent } from "../ui/custom-components/detail-modal.js";

registerShellComponents();

// #region Component
@customElement("static-module")
export class StaticModule extends LitElement {
  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @property({ type: String }) accessor currentTab = 'summary';
  @property({ attribute: false }) accessor component: any = this;
  
  @state() accessor selectedItem: any = null;
  @state() accessor showNotification = false;
  @state() accessor notificationMessage = '';

  private processor = v0_8.Data.createSignalA2uiMessageProcessor();

  // #region Data Loading
  connectedCallback() {
    super.connectedCallback();
    this.initializeData();
  }

  private async initializeData() {
    try {
      const messages = this.router
        ? await this.router.fetchTraditionalMessages('/traditional')
        : await this.fetchDirect('/traditional');
      this.processor.processMessages(messages);
      this.requestUpdate();
    } catch (error) {
      console.error('Failed to fetch outage data from server:', error);
      // Fall back to local data if the server is unavailable.
      this.initializeStaticData();
    }
  }

  private async fetchData(endpoint: string) {
    try {
      const messages = this.router
        ? await this.router.fetchTraditionalMessages(endpoint)
        : await this.fetchDirect(endpoint);
      this.processor.processMessages(messages);
      this.requestUpdate();
    } catch (error) {
      console.error(`Failed to fetch data from ${endpoint}:`, error);
    }
  }

  private async fetchDirect(endpoint: string): Promise<v0_8.Types.ServerToClientMessage[]> {
    const response = await fetch(buildServerUrl(endpoint));
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
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
  // #endregion Data Loading

  // #region Static Fallback Data
  private initializeStaticData() {
    // Static fallback data for offline testing.
    const messages: v0_8.Types.ServerToClientMessage[] = [
      {
        dataModelUpdate: {
          surfaceId: 'default',
          path: '/',
          contents: [
            // KPI data
            {
              key: 'energyKPIs',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'label', valueString: 'Total Production' },
                  { key: 'value', valueNumber: 2847 },
                  { key: 'unit', valueString: 'GWh' },
                  { key: 'change', valueNumber: 12.5 },
                  { key: 'changeLabel', valueString: 'vs last month' },
                  { key: 'icon', valueString: '⚡' },
                  { key: 'colorTheme', valueString: 'cyan' },
                  { key: 'trend', valueString: 'rising steadily over Q4' },
                  { key: 'forecast', valueString: '3100 GWh expected next month' },
                  { key: 'breakdown', valueString: 'Solar: 45%, Wind: 30%, Hydro: 25%' }
                ]},
                { key: '1', valueMap: [
                  { key: 'label', valueString: 'Active Outages' },
                  { key: 'value', valueNumber: 25 },
                  { key: 'unit', valueString: '' },
                  { key: 'change', valueNumber: -8 },
                  { key: 'changeLabel', valueString: 'vs yesterday' },
                  { key: 'icon', valueString: '🔌' },
                  { key: 'colorTheme', valueString: 'coral' },
                  { key: 'trend', valueString: 'decreasing after storm recovery' },
                  { key: 'breakdown', valueString: 'High: 5, Medium: 12, Low: 8' }
                ]},
                { key: '2', valueMap: [
                  { key: 'label', valueString: 'Customers Affected' },
                  { key: 'value', valueNumber: 15420 },
                  { key: 'unit', valueString: '' },
                  { key: 'change', valueNumber: -22 },
                  { key: 'changeLabel', valueString: 'vs peak' },
                  { key: 'icon', valueString: '👥' },
                  { key: 'colorTheme', valueString: 'teal' },
                  { key: 'trend', valueString: 'restoration in progress' },
                  { key: 'affectedDistricts', valueString: 'Downtown, North, East District' }
                ]},
                { key: '3', valueMap: [
                  { key: 'label', valueString: 'Grid Efficiency' },
                  { key: 'value', valueNumber: 94.2 },
                  { key: 'unit', valueString: '%' },
                  { key: 'change', valueNumber: 1.8 },
                  { key: 'changeLabel', valueString: 'vs baseline' },
                  { key: 'icon', valueString: '📊' },
                  { key: 'colorTheme', valueString: 'green' },
                  { key: 'trend', valueString: 'above target of 92%' },
                  { key: 'factors', valueString: 'Smart grid upgrades, load balancing improvements' }
                ]}
              ]
            },
            // Outage summary data
            {
              key: 'outageSummary',
              valueMap: [
                { key: '0', valueNumber: 25 },
                { key: '1', valueNumber: 15 },
                { key: '2', valueNumber: 42 },
                { key: '3', valueNumber: 8 },
                { key: '4', valueNumber: 12 }
              ]
            },
            {
              key: 'outageSummaryLabels',
              valueMap: [
                { key: '0', valueString: 'Active' },
                { key: '1', valueString: 'Investigating' },
                { key: '2', valueString: 'Resolved' },
                { key: '3', valueString: 'Scheduled' },
                { key: '4', valueString: 'Monitoring' }
              ]
            },
            // Per-bar details
            {
              key: 'outageSummaryDetails',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'status', valueString: 'Active' },
                  { key: 'customersAffected', valueNumber: 1870 },
                  { key: 'severityBreakdown', valueString: 'High: 5, Medium: 12, Low: 8' },
                  { key: 'topAreas', valueString: 'Downtown, West Residential' },
                  { key: 'mainCauses', valueString: 'Transformer failure, Cable fault' },
                  { key: 'priority', valueString: 'Immediate response required' }
                ]},
                { key: '1', valueMap: [
                  { key: 'status', valueString: 'Investigating' },
                  { key: 'customersAffected', valueNumber: 850 },
                  { key: 'severityBreakdown', valueString: 'High: 2, Medium: 8, Low: 5' },
                  { key: 'topAreas', valueString: 'North Substation' },
                  { key: 'mainCauses', valueString: 'Equipment malfunction' },
                  { key: 'estimatedResolution', valueString: 'Under assessment' }
                ]},
                { key: '2', valueMap: [
                  { key: 'status', valueString: 'Resolved' },
                  { key: 'customersRestored', valueNumber: 5420 },
                  { key: 'resolutionRate', valueString: '100% service restored' },
                  { key: 'topAreas', valueString: 'East District, South Grid' },
                  { key: 'mainCauses', valueString: 'Tree contact, Minor faults' },
                  { key: 'avgResolutionTime', valueString: '2.5 hours' }
                ]},
                { key: '3', valueMap: [
                  { key: 'status', valueString: 'Scheduled' },
                  { key: 'plannedCustomers', valueNumber: 45 },
                  { key: 'scheduledWindow', valueString: 'Next 48 hours' },
                  { key: 'topAreas', valueString: 'Industrial Park' },
                  { key: 'maintenanceType', valueString: 'Preventive maintenance' },
                  { key: 'notificationSent', valueString: 'Yes - 72hrs advance' }
                ]},
                { key: '4', valueMap: [
                  { key: 'status', valueString: 'Monitoring' },
                  { key: 'customersWatched', valueNumber: 1200 },
                  { key: 'monitoringLevel', valueString: 'Standard observation' },
                  { key: 'topAreas', valueString: 'Central Grid, Harbor District' },
                  { key: 'lastChecked', valueString: '5 minutes ago' },
                  { key: 'alertThreshold', valueString: 'Auto-escalate if no improvement' }
                ]}
              ]
            },
            // Outage table
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
                  { key: 'affectedCustomers', valueNumber: 1250 },
                  { key: 'cause', valueString: 'Transformer failure due to storm damage' },
                  { key: 'crewAssigned', valueString: 'Team Alpha - 5 technicians' },
                  { key: 'priority', valueString: 'Critical - Hospital in area' },
                  { key: 'notes', valueString: 'Emergency backup generators activated at local hospital. Replacement transformer en route.' }
                ]},
                { key: '1', valueMap: [
                  { key: 'id', valueString: 'OUT-002' },
                  { key: 'location', valueString: 'North Substation' },
                  { key: 'status', valueString: 'Investigating' },
                  { key: 'severity', valueString: 'Medium' },
                  { key: 'startTime', valueString: '2024-01-15T12:15:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-15T16:30:00Z' },
                  { key: 'affectedCustomers', valueNumber: 850 },
                  { key: 'cause', valueString: 'Suspected equipment malfunction' },
                  { key: 'crewAssigned', valueString: 'Team Beta - 3 technicians' },
                  { key: 'priority', valueString: 'Standard residential area' },
                  { key: 'notes', valueString: 'Diagnostic team analyzing sensor data. May require equipment replacement.' }
                ]},
                { key: '2', valueMap: [
                  { key: 'id', valueString: 'OUT-003' },
                  { key: 'location', valueString: 'East District' },
                  { key: 'status', valueString: 'Resolved' },
                  { key: 'severity', valueString: 'Low' },
                  { key: 'startTime', valueString: '2024-01-14T09:45:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-14T11:20:00Z' },
                  { key: 'affectedCustomers', valueNumber: 320 },
                  { key: 'cause', valueString: 'Tree branch contact with power line' },
                  { key: 'crewAssigned', valueString: 'Team Charlie - 2 technicians' },
                  { key: 'priority', valueString: 'Standard' },
                  { key: 'notes', valueString: 'Branch removed, line inspected, all systems nominal.' }
                ]},
                { key: '3', valueMap: [
                  { key: 'id', valueString: 'OUT-004' },
                  { key: 'location', valueString: 'Industrial Park' },
                  { key: 'status', valueString: 'Scheduled' },
                  { key: 'severity', valueString: 'Low' },
                  { key: 'startTime', valueString: '2024-01-16T02:00:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-16T06:00:00Z' },
                  { key: 'affectedCustomers', valueNumber: 45 },
                  { key: 'cause', valueString: 'Planned maintenance - transformer upgrade' },
                  { key: 'crewAssigned', valueString: 'Team Delta - 4 technicians' },
                  { key: 'priority', valueString: 'Off-peak scheduled maintenance' },
                  { key: 'notes', valueString: 'All affected businesses notified 48 hours in advance.' }
                ]},
                { key: '4', valueMap: [
                  { key: 'id', valueString: 'OUT-005' },
                  { key: 'location', valueString: 'West Residential' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'severity', valueString: 'Medium' },
                  { key: 'startTime', valueString: '2024-01-15T15:45:00Z' },
                  { key: 'estimatedRestoration', valueString: '2024-01-15T19:30:00Z' },
                  { key: 'affectedCustomers', valueNumber: 620 },
                  { key: 'cause', valueString: 'Underground cable fault' },
                  { key: 'crewAssigned', valueString: 'Team Echo - 6 technicians' },
                  { key: 'priority', valueString: 'Elevated - Multiple senior facilities' },
                  { key: 'notes', valueString: 'Cable locator equipment deployed. Excavation may be required.' }
                ]}
              ]
            },
            // Timeline events
            {
              key: 'timelineEvents',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'date', valueString: '2024-01-15T15:45:00Z' },
                  { key: 'title', valueString: 'West Residential Outage' },
                  { key: 'description', valueString: 'Underground cable fault detected in West Residential area' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'affectedCustomers', valueNumber: 620 },
                  { key: 'location', valueString: 'West Residential District' },
                  { key: 'assignedCrew', valueString: 'Team Echo' },
                  { key: 'estimatedDuration', valueString: '4 hours' }
                ]},
                { key: '1', valueMap: [
                  { key: 'date', valueString: '2024-01-15T14:30:00Z' },
                  { key: 'title', valueString: 'Downtown Grid Emergency' },
                  { key: 'description', valueString: 'Major transformer failure affecting downtown business district' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'affectedCustomers', valueNumber: 1250 },
                  { key: 'location', valueString: 'Downtown Grid - Sectors A-C' },
                  { key: 'assignedCrew', valueString: 'Team Alpha' },
                  { key: 'estimatedDuration', valueString: '3.5 hours' }
                ]},
                { key: '2', valueMap: [
                  { key: 'date', valueString: '2024-01-15T12:15:00Z' },
                  { key: 'title', valueString: 'North Substation Investigation' },
                  { key: 'description', valueString: 'Anomalous readings detected, investigation underway' },
                  { key: 'status', valueString: 'Investigating' },
                  { key: 'affectedCustomers', valueNumber: 850 },
                  { key: 'location', valueString: 'North Substation Area' },
                  { key: 'assignedCrew', valueString: 'Team Beta' },
                  { key: 'estimatedDuration', valueString: '4.5 hours' }
                ]},
                { key: '3', valueMap: [
                  { key: 'date', valueString: '2024-01-14T11:20:00Z' },
                  { key: 'title', valueString: 'East District Restored' },
                  { key: 'description', valueString: 'Power fully restored after tree branch removal' },
                  { key: 'status', valueString: 'Resolved' },
                  { key: 'affectedCustomers', valueNumber: 320 },
                  { key: 'location', valueString: 'East District' },
                  { key: 'assignedCrew', valueString: 'Team Charlie' },
                  { key: 'resolutionTime', valueString: '1.5 hours' }
                ]},
                { key: '4', valueMap: [
                  { key: 'date', valueString: '2024-01-14T08:00:00Z' },
                  { key: 'title', valueString: 'Morning Grid Check Complete' },
                  { key: 'description', valueString: 'Daily automated grid inspection completed successfully' },
                  { key: 'status', valueString: 'Completed' },
                  { key: 'location', valueString: 'All Sectors' },
                  { key: 'notes', valueString: '3 minor anomalies flagged for review' }
                ]}
              ]
            },
            // Map markers
            {
              key: 'mapMarkers',
              valueMap: [
                { key: '0', valueMap: [
                  { key: 'name', valueString: 'Downtown Grid' },
                  { key: 'latitude', valueNumber: 40.7589 },
                  { key: 'longitude', valueNumber: -73.9851 },
                  { key: 'description', valueString: 'Active outage - Transformer failure' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'severity', valueString: 'High' },
                  { key: 'affectedCustomers', valueNumber: 1250 },
                  { key: 'crew', valueString: 'Team Alpha on site' }
                ]},
                { key: '1', valueMap: [
                  { key: 'name', valueString: 'North Substation' },
                  { key: 'latitude', valueNumber: 40.7829 },
                  { key: 'longitude', valueNumber: -73.9654 },
                  { key: 'description', valueString: 'Under investigation - Equipment check' },
                  { key: 'status', valueString: 'Investigating' },
                  { key: 'severity', valueString: 'Medium' },
                  { key: 'affectedCustomers', valueNumber: 850 },
                  { key: 'crew', valueString: 'Team Beta investigating' }
                ]},
                { key: '2', valueMap: [
                  { key: 'name', valueString: 'East District' },
                  { key: 'latitude', valueNumber: 40.7505 },
                  { key: 'longitude', valueNumber: -73.9934 },
                  { key: 'description', valueString: 'Restored - Active monitoring' },
                  { key: 'status', valueString: 'Resolved' },
                  { key: 'severity', valueString: 'Low' },
                  { key: 'affectedCustomers', valueNumber: 0 },
                  { key: 'crew', valueString: 'Monitoring remotely' }
                ]},
                { key: '3', valueMap: [
                  { key: 'name', valueString: 'West Residential' },
                  { key: 'latitude', valueNumber: 40.7420 },
                  { key: 'longitude', valueNumber: -74.0080 },
                  { key: 'description', valueString: 'Active outage - Underground cable fault' },
                  { key: 'status', valueString: 'Active' },
                  { key: 'severity', valueString: 'Medium' },
                  { key: 'affectedCustomers', valueNumber: 620 },
                  { key: 'crew', valueString: 'Team Echo deploying equipment' }
                ]},
                { key: '4', valueMap: [
                  { key: 'name', valueString: 'Industrial Park' },
                  { key: 'latitude', valueNumber: 40.7680 },
                  { key: 'longitude', valueNumber: -73.9500 },
                  { key: 'description', valueString: 'Scheduled maintenance tonight' },
                  { key: 'status', valueString: 'Scheduled' },
                  { key: 'severity', valueString: 'Low' },
                  { key: 'affectedCustomers', valueNumber: 45 },
                  { key: 'crew', valueString: 'Team Delta scheduled 2am' }
                ]}
              ]
            },
            // Energy trends
            {
              key: 'trends',
              valueMap: [
                { key: 'energyTrend', valueMap: [
                  { key: '0', valueMap: [
                    { key: 'name', valueString: 'Solar' },
                    { key: 'color', valueString: '#FFB547' },
                    { key: 'values', valueMap: [
                      { key: '0', valueNumber: 450 },
                      { key: '1', valueNumber: 520 },
                      { key: '2', valueNumber: 680 },
                      { key: '3', valueNumber: 890 },
                      { key: '4', valueNumber: 1050 },
                      { key: '5', valueNumber: 1180 },
                      { key: '6', valueNumber: 1250 },
                      { key: '7', valueNumber: 1100 },
                      { key: '8', valueNumber: 920 },
                      { key: '9', valueNumber: 680 },
                      { key: '10', valueNumber: 520 },
                      { key: '11', valueNumber: 480 }
                    ]}
                  ]},
                  { key: '1', valueMap: [
                    { key: 'name', valueString: 'Wind' },
                    { key: 'color', valueString: '#4ECDC4' },
                    { key: 'values', valueMap: [
                      { key: '0', valueNumber: 650 },
                      { key: '1', valueNumber: 580 },
                      { key: '2', valueNumber: 720 },
                      { key: '3', valueNumber: 540 },
                      { key: '4', valueNumber: 680 },
                      { key: '5', valueNumber: 750 },
                      { key: '6', valueNumber: 820 },
                      { key: '7', valueNumber: 900 },
                      { key: '8', valueNumber: 780 },
                      { key: '9', valueNumber: 850 },
                      { key: '10', valueNumber: 720 },
                      { key: '11', valueNumber: 690 }
                    ]}
                  ]},
                  { key: '2', valueMap: [
                    { key: 'name', valueString: 'Hydro' },
                    { key: 'color', valueString: '#45B7D1' },
                    { key: 'values', valueMap: [
                      { key: '0', valueNumber: 320 },
                      { key: '1', valueNumber: 340 },
                      { key: '2', valueNumber: 380 },
                      { key: '3', valueNumber: 420 },
                      { key: '4', valueNumber: 480 },
                      { key: '5', valueNumber: 520 },
                      { key: '6', valueNumber: 490 },
                      { key: '7', valueNumber: 450 },
                      { key: '8', valueNumber: 400 },
                      { key: '9', valueNumber: 360 },
                      { key: '10', valueNumber: 340 },
                      { key: '11', valueNumber: 330 }
                    ]}
                  ]}
                ]},
                { key: 'energyTrendLabels', valueMap: [
                  { key: '0', valueString: 'Jan' },
                  { key: '1', valueString: 'Feb' },
                  { key: '2', valueString: 'Mar' },
                  { key: '3', valueString: 'Apr' },
                  { key: '4', valueString: 'May' },
                  { key: '5', valueString: 'Jun' },
                  { key: '6', valueString: 'Jul' },
                  { key: '7', valueString: 'Aug' },
                  { key: '8', valueString: 'Sep' },
                  { key: '9', valueString: 'Oct' },
                  { key: '10', valueString: 'Nov' },
                  { key: '11', valueString: 'Dec' }
                ]},
                { key: 'energyTrendDetails', valueMap: [
                  { key: '0', valueMap: [{ key: 'period', valueString: 'January' }, { key: 'trend', valueString: 'Winter baseline output' }, { key: 'forecast', valueString: 'Expected increase next month' }]},
                  { key: '1', valueMap: [{ key: 'period', valueString: 'February' }, { key: 'trend', valueString: 'Seasonal ramp-up' }, { key: 'forecast', valueString: 'Continued growth expected' }]},
                  { key: '2', valueMap: [{ key: 'period', valueString: 'March' }, { key: 'trend', valueString: 'Strong spring growth' }, { key: 'forecast', valueString: 'Above-average production likely' }]},
                  { key: '3', valueMap: [{ key: 'period', valueString: 'April' }, { key: 'trend', valueString: 'Rapid acceleration' }, { key: 'forecast', valueString: 'Near-summer peak expected' }]},
                  { key: '4', valueMap: [{ key: 'period', valueString: 'May' }, { key: 'trend', valueString: 'High output period' }, { key: 'forecast', valueString: 'Stable high generation' }]},
                  { key: '5', valueMap: [{ key: 'period', valueString: 'June' }, { key: 'trend', valueString: 'Summer peak onset' }, { key: 'forecast', valueString: 'Potential monthly maximum' }]},
                  { key: '6', valueMap: [{ key: 'period', valueString: 'July' }, { key: 'trend', valueString: 'Sustained peak' }, { key: 'forecast', valueString: 'Slight taper expected' }]},
                  { key: '7', valueMap: [{ key: 'period', valueString: 'August' }, { key: 'trend', valueString: 'Post-peak normalization' }, { key: 'forecast', valueString: 'Gradual decline expected' }]},
                  { key: '8', valueMap: [{ key: 'period', valueString: 'September' }, { key: 'trend', valueString: 'Early autumn decline' }, { key: 'forecast', valueString: 'Further reduction likely' }]},
                  { key: '9', valueMap: [{ key: 'period', valueString: 'October' }, { key: 'trend', valueString: 'Autumn stabilization' }, { key: 'forecast', valueString: 'Low volatility expected' }]},
                  { key: '10', valueMap: [{ key: 'period', valueString: 'November' }, { key: 'trend', valueString: 'Pre-winter reduction' }, { key: 'forecast', valueString: 'Seasonal low approaching' }]},
                  { key: '11', valueMap: [{ key: 'period', valueString: 'December' }, { key: 'trend', valueString: 'Winter trough' }, { key: 'forecast', valueString: 'Recovery expected in Q1' }]}
                ]}
              ]
            },
            // Timeline
            {
              key: 'timeline',
              valueMap: [
                { key: 'timelineEvents', valueMap: [
                  { key: '0', valueMap: [
                    { key: 'date', valueString: '2024-01-15T15:45:00Z' },
                    { key: 'title', valueString: 'West Residential Outage Reported' },
                    { key: 'description', valueString: 'Underground cable fault detected in residential area' },
                    { key: 'status', valueString: 'Active' },
                    { key: 'affectedArea', valueString: 'West Residential - Blocks 12-18' },
                    { key: 'assignedTeam', valueString: 'Team Echo (6 technicians)' }
                  ]},
                  { key: '1', valueMap: [
                    { key: 'date', valueString: '2024-01-15T14:30:00Z' },
                    { key: 'title', valueString: 'Downtown Grid Emergency Response' },
                    { key: 'description', valueString: 'Major transformer failure affecting business district' },
                    { key: 'status', valueString: 'Active' },
                    { key: 'affectedArea', valueString: 'Downtown Sectors A, B, C' },
                    { key: 'assignedTeam', valueString: 'Team Alpha (5 technicians)' }
                  ]},
                  { key: '2', valueMap: [
                    { key: 'date', valueString: '2024-01-15T12:15:00Z' },
                    { key: 'title', valueString: 'North Substation Alert Triggered' },
                    { key: 'description', valueString: 'Automated monitoring detected anomalous readings' },
                    { key: 'status', valueString: 'Investigating' },
                    { key: 'affectedArea', valueString: 'North Substation perimeter' },
                    { key: 'assignedTeam', valueString: 'Team Beta (3 technicians)' }
                  ]},
                  { key: '3', valueMap: [
                    { key: 'date', valueString: '2024-01-14T11:20:00Z' },
                    { key: 'title', valueString: 'East District Power Restoration Complete' },
                    { key: 'description', valueString: 'All affected customers restored after tree branch removal' },
                    { key: 'status', valueString: 'Resolved' },
                    { key: 'resolution', valueString: 'Tree branch cleared, line inspected and tested' },
                    { key: 'duration', valueString: '1 hour 35 minutes' }
                  ]}
                ]},
                { key: 'timelineEventDetails', valueMap: [
                  { key: '0', valueMap: [{ key: 'status', valueString: 'Active' }, { key: 'affectedArea', valueString: 'West Residential - Blocks 12-18' }, { key: 'assignedTeam', valueString: 'Team Echo (6 technicians)' }]},
                  { key: '1', valueMap: [{ key: 'status', valueString: 'Active' }, { key: 'affectedArea', valueString: 'Downtown Sectors A, B, C' }, { key: 'assignedTeam', valueString: 'Team Alpha (5 technicians)' }]},
                  { key: '2', valueMap: [{ key: 'status', valueString: 'Investigating' }, { key: 'affectedArea', valueString: 'North Substation perimeter' }, { key: 'assignedTeam', valueString: 'Team Beta (3 technicians)' }]},
                  { key: '3', valueMap: [{ key: 'status', valueString: 'Resolved' }, { key: 'resolution', valueString: 'Tree branch cleared, line inspected and tested' }, { key: 'duration', valueString: '1 hour 35 minutes' }]}
                ]}
              ]
            },
            // Industry metrics
            {
              key: 'industry',
              valueMap: [
                { key: 'industryTable', valueMap: [
                  { key: '0', valueMap: [
                    { key: 'name', valueString: 'Solar Manufacturing' },
                    { key: 'productionIndex', valueNumber: 127.5 },
                    { key: 'employment', valueNumber: 4520 },
                    { key: 'growthRate', valueNumber: 15.2 },
                    { key: 'outputValue', valueNumber: 2.8 },
                    { key: 'efficiencyScore', valueNumber: 94.2 }
                  ]},
                  { key: '1', valueMap: [
                    { key: 'name', valueString: 'Wind Turbine Production' },
                    { key: 'productionIndex', valueNumber: 118.3 },
                    { key: 'employment', valueNumber: 3280 },
                    { key: 'growthRate', valueNumber: 12.8 },
                    { key: 'outputValue', valueNumber: 1.9 },
                    { key: 'efficiencyScore', valueNumber: 91.5 }
                  ]},
                  { key: '2', valueMap: [
                    { key: 'name', valueString: 'Battery Storage' },
                    { key: 'productionIndex', valueNumber: 145.2 },
                    { key: 'employment', valueNumber: 2890 },
                    { key: 'growthRate', valueNumber: 28.5 },
                    { key: 'outputValue', valueNumber: 3.2 },
                    { key: 'efficiencyScore', valueNumber: 88.7 }
                  ]},
                  { key: '3', valueMap: [
                    { key: 'name', valueString: 'Grid Infrastructure' },
                    { key: 'productionIndex', valueNumber: 105.8 },
                    { key: 'employment', valueNumber: 8920 },
                    { key: 'growthRate', valueNumber: 5.2 },
                    { key: 'outputValue', valueNumber: 4.1 },
                    { key: 'efficiencyScore', valueNumber: 96.3 }
                  ]},
                  { key: '4', valueMap: [
                    { key: 'name', valueString: 'EV Charging Networks' },
                    { key: 'productionIndex', valueNumber: 182.4 },
                    { key: 'employment', valueNumber: 1560 },
                    { key: 'growthRate', valueNumber: 42.1 },
                    { key: 'outputValue', valueNumber: 1.2 },
                    { key: 'efficiencyScore', valueNumber: 85.9 }
                  ]}
                ]}
              ]
            }
          ]
        }
      }
    ];

    this.processor.processMessages(messages);
  }
  // #endregion Static Fallback Data

  // #region Styles
  static styles = css`
    ${designTokensCSS}
    ${buttonStyles}

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
      gap: var(--space-xs);
      margin-bottom: var(--space-md);
      border-bottom: 1px solid var(--border-secondary);
    }

    .tabs .btn-tab.active {
      color: var(--color-error);
      border-bottom-color: var(--color-error);
    }

    .tabs .btn-tab:hover {
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
      gap: var(--space-sm);
      margin: var(--space-md) 0;
      justify-content: center;
      flex-wrap: wrap;
    }

    .notification {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--surface-tertiary);
      color: var(--text-primary);
      padding: var(--space-md) var(--space-lg);
      border-radius: var(--radius-md);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      z-index: 1000;
      animation: slideIn 0.3s ease-out;
      border-left: 4px solid var(--color-primary);
    }

    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    .notification-close {
      margin-left: var(--space-md);
      cursor: pointer;
      opacity: 0.7;
    }

    .notification-close:hover {
      opacity: 1;
    }

    .bar-chart-section {
      background: var(--surface-secondary);
      border-radius: var(--radius-md);
      padding: var(--space-md);
    }
  `
  // #endregion Styles

  // #region Render
  render() {
    return html`
      <stat-bar .title=${"Traditional app"} .time=${""} .tokens=${""} .configUrl=${buildServerUrl("/outage_config")} .configType=${"traditional"} .configData=${outageConfig}></stat-bar>
      <div class="tabs">
        <button class="btn btn-tab ${this.currentTab === 'summary' ? 'active' : ''}" @click=${() => this.switchTab('summary')}>
          Energy Summary
        </button>
        <button class="btn btn-tab ${this.currentTab === 'details' ? 'active' : ''}" @click=${() => this.switchTab('details')}>
          Outages Details
        </button>
        <button class="btn btn-tab ${this.currentTab === 'map' ? 'active' : ''}" @click=${() => this.switchTab('map')}>
          Outage Map
        </button>
      </div>
      <div class="tab-content">
        ${this.renderTabContent()}
      </div>
      ${this.renderNotification()}
    `
  }
  // #endregion Render

  // #region Notifications
  private renderNotification() {
    if (!this.showNotification) return null;
    return html`
      <div class="notification">
        ${this.notificationMessage}
        <span class="notification-close" @click=${this.closeNotification}>✕</span>
      </div>
    `;
  }

  private showNotify(message: string) {
    this.notificationMessage = message;
    this.showNotification = true;
    setTimeout(() => {
      this.showNotification = false;
    }, 4000);
  }

  private closeNotification() {
    this.showNotification = false;
  }
  // #endregion Notifications

  // #region Interaction Handlers
  // Interaction handlers
  private handleItemSelect(e: CustomEvent) {
    const detail = e.detail;
    this.selectedItem = detail.item;
    this.showNotify(`Selected: ${detail.item?.id || detail.item?.label || 'item'}`);
  }

  private handleKpiClick(e: CustomEvent) {
    const detail = e.detail;
    this.showNotify(`KPI clicked: ${detail.label} = ${detail.value}`);
  }

  private handleBarSelect(e: CustomEvent) {
    const { label, value, percentage } = e.detail;
    this.showNotify(`Bar selected: ${label} - ${value} (${percentage}%)`);
  }

  private handlePointSelect(e: CustomEvent) {
    const { series, index, value, label } = e.detail;
    this.showNotify(`Point selected: ${series} at ${label} = ${value}`);
  }

  private handleMarkerSelect(e: CustomEvent) {
    const marker = e.detail.marker;
    this.showNotify(`Marker: ${marker.name} - ${marker.status || 'View details'}`);
  }

  private handleTimelineAction(e: CustomEvent) {
    const { action, item } = e.detail;
    this.showNotify(`${action} action on: ${item.title}`);
  }
  // #endregion Interaction Handlers

  // #region Tab Rendering
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
        <kpi-card-group 
          .dataPath=${"/energyKPIs"} 
          .title=${"Energy Metrics"} 
          .processor=${this.processor} 
          .component=${this}
          clickable
          @kpi-click=${this.handleKpiClick}
        ></kpi-card-group>
      </div>
      <div class="bar-chart-section">
        <div class="section-title">Outage Status Distribution</div>
        <bar-graph
          .dataPath=${"/outageSummary"}
          .labelPath=${"/outageSummaryLabels"}
          .detailsPath=${"/outageSummaryDetails"}
          .title=${"Outages by Status"}
          .processor=${this.processor}
          .component=${this}
          interactive
          colorful
          @bar-select=${this.handleBarSelect}
        ></bar-graph>
      </div>
      <div class="chart-section">
        <div class="section-title">Energy Production Trends</div>
        <line-graph 
          .seriesPath=${"/trends/energyTrend"} 
          .labelPath=${"/trends/energyTrendLabels"} 
          .detailsPath=${"/trends/energyTrendDetails"}
          .title=${"Monthly Production by Source"} 
          .processor=${this.processor} 
          .component=${this}
          interactive
          showPoints
          @point-select=${this.handlePointSelect}
        ></line-graph>
        ${!this.hasEnergyTrends() ? html`<button @click=${this.loadEnergyTrends} class="btn btn-outline-traditional">Load Energy Trends</button>` : ''}
      </div>
    `;
  }

  private renderDetailsTab() {
    return html`
      <div class="table-section">
        <div class="section-title">Outage Details by Location</div>
        <data-table
          .dataPath=${"/outageTable"}
          .detailsPath=${"/outageTableDetails"}
          .title=${"Outage Details"}
          .columns=${[
            {header: "Outage ID", field: "id", type: "string"},
            {header: "Location", field: "location", type: "string"},
            {header: "Status", field: "status", type: "status"},
            {header: "Severity", field: "severity", type: "severity"},
            {header: "Start Time", field: "startTime", type: "date"},
            {header: "Est. Restoration", field: "estimatedRestoration", type: "date"},
            {header: "Affected", field: "affectedCustomers", type: "number"}
          ]}
          .processor=${this.processor}
          .component=${this}
          expandable
          showDetailPanel
          @item-select=${this.handleItemSelect}
        ></data-table>
      </div>
      <div class="timeline-section">
        <div class="section-title">Outage Timeline</div>
        <timeline-component 
          .dataPath=${"/timeline/timelineEvents"} 
          .detailsPath=${"/timeline/timelineEventDetails"}
          .processor=${this.processor} 
          .component=${this}
          expandable
          @timeline-action=${this.handleTimelineAction}
        ></timeline-component>
        ${!this.hasTimeline() ? html`<button @click=${this.loadTimeline} class="btn btn-outline-traditional">Load Timeline</button>` : ''}
      </div>
      <div class="table-section">
        <div class="section-title">Industry Performance Metrics</div>
        <data-table
          .dataPath=${"/industry/industryTable"}
          .detailsPath=${"/industry/industryTableDetails"}
          .title=${"Industry Data"}
          .columns=${[
            {header: "Industry", field: "name", type: "string"},
            {header: "Production Index", field: "productionIndex", type: "number"},
            {header: "Employment", field: "employment", type: "number"},
            {header: "Growth Rate", field: "growthRate", type: "number"},
            {header: "Output Value", field: "outputValue", type: "number"},
            {header: "Efficiency Score", field: "efficiencyScore", type: "number"}
          ]}
          .processor=${this.processor}
          .component=${this}
          expandable
        ></data-table>
        ${!this.hasIndustry() ? html`<button @click=${this.loadIndustryData} class="btn btn-outline-traditional">Load Industry Data</button>` : ''}
      </div>
    `;
  }

  private renderMapTab() {
    return html`
      <div class="map-section">
        <div class="section-title">Outage Locations</div>
        <map-component 
          .dataPath=${"/mapMarkers"} 
          .centerLat=${40.76} 
          .centerLng=${-73.98} 
          .zoom=${12} 
          .processor=${this.processor} 
          .component=${this}
          interactive
          showInfoPanel
          @marker-select=${this.handleMarkerSelect}
        ></map-component>
        <div class="map-description">
          <p>This map shows the current locations of reported power outages in the service area. Click markers for details or use the info panel to navigate between locations.</p>
          <p>Colors indicate severity: <strong style="color: #FF6B6B;">Red = High</strong>, <strong style="color: #FFB347;">Orange = Medium</strong>, <strong style="color: #4ECDC4;">Green = Resolved</strong></p>
        </div>
      </div>
    `;
  }
  // #endregion Tab Rendering


}
// #endregion Component

// #region Element Registration
declare global {
  interface HTMLElementTagNameMap {
    "static-module": StaticModule
  }
}
// #endregion Element Registration
