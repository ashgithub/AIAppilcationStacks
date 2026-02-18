/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { Part, SendMessageSuccessResponse, Task } from "@a2a-js/sdk";
import { A2AClient } from "@a2a-js/sdk/client";
import { v0_8 } from "@a2ui/lit";
import { registerShellComponents } from "../ui/custom-components/register-components.js";
import { componentRegistry } from "@a2ui/lit/ui";

const A2UI_MIME_TYPE = "application/json+a2ui";

// Mock A2UI payload for testing client-side components
const getMockMessages = (): v0_8.Types.ServerToClientMessage[] => [
  // beginRendering
  {
    beginRendering: {
      surfaceId: "test-dashboard",
      root: "main-container",
      styles: {
        font: "Arial",
        primaryColor: "#007bff"
      }
    }
  },
  // surfaceUpdate with all three components
  {
    surfaceUpdate: {
      surfaceId: "test-dashboard",
      components: [
        {
          id: "main-container",
          component: {
            Column: {
              children: {
                explicitList: ["title", "kpi-row", "bar-chart", "line-chart", "outage-table", "map-component", "timeline-component"]
              }
            }
          }
        },
        {
          id: "title",
          component: {
            Text: {
              text: { literalString: "A2UI Components Test Dashboard" },
              usageHint: "h2"
            }
          }
        },
        // KPI cards arranged using native Row component with weight
        {
          id: "kpi-row",
          component: {
            Row: {
              children: {
                explicitList: ["kpi-1", "kpi-2", "kpi-3", "kpi-4"]
              },
              distribution: "spaceEvenly",
              alignment: "stretch"
            }
          }
        },
        {
          id: "kpi-1",
          weight: 1,
          component: {
            KpiCard: {
              dataPath: "/kpi/activeOutages"
            }
          }
        },
        {
          id: "kpi-2",
          weight: 1,
          component: {
            KpiCard: {
              dataPath: "/kpi/customersAffected"
            }
          }
        },
        {
          id: "kpi-3",
          weight: 1,
          component: {
            KpiCard: {
              dataPath: "/kpi/avgResolutionTime"
            }
          }
        },
        {
          id: "kpi-4",
          weight: 1,
          component: {
            KpiCard: {
              dataPath: "/kpi/systemUptime"
            }
          }
        },
        {
          id: "bar-chart",
          component: {
            BarGraph: {
              dataPath: "/chartData",
              labelPath: "/chartLabels"
            }
          }
        },
        {
          id: "line-chart",
          component: {
            LineGraph: {
              labelPath: "/lineLabels",
              seriesPath: "/lineSeries",
              showPoints: true,
              showArea: true,
              animated: true
            }
          }
        },
        {
          id: "map-component",
          component: {
            MapComponent: {
              dataPath: "/mapData",
              centerLat: 40.7128,
              centerLng: -74.0060,
              zoom: 10
            }
          }
        },
        {
          id: "timeline-component",
          component: {
            TimelineComponent: {
              dataPath: "/timelineData"
            }
          }
        },
        {
          id: "outage-table",
          component: {
            OutageTable: {
              dataPath: "/outageData",
              title: "Active Outages"
            }
          }
        }
      ]
    }
  },
  // dataModelUpdate with sample data
  {
    dataModelUpdate: {
      surfaceId: "test-dashboard",
      path: "/",
      contents: [
        // Individual KPI data objects for Row-based layout
        {
          key: "kpi",
          valueMap: [
            {
              key: "activeOutages",
              valueMap: [
                { key: "label", valueString: "Active Outages" },
                { key: "value", valueNumber: 3 },
                { key: "icon", valueString: "⚡" },
                { key: "change", valueNumber: -25 },
                { key: "changeLabel", valueString: "vs yesterday" },
                { key: "color", valueString: "coral" }
              ]
            },
            {
              key: "customersAffected",
              valueMap: [
                { key: "label", valueString: "Customers Affected" },
                { key: "value", valueNumber: 17550 },
                { key: "icon", valueString: "👥" },
                { key: "change", valueNumber: -12 },
                { key: "changeLabel", valueString: "vs yesterday" },
                { key: "color", valueString: "yellow" }
              ]
            },
            {
              key: "avgResolutionTime",
              valueMap: [
                { key: "label", valueString: "Avg Resolution Time" },
                { key: "value", valueNumber: 4.2 },
                { key: "unit", valueString: "hrs" },
                { key: "icon", valueString: "⏱" },
                { key: "change", valueNumber: 8 },
                { key: "changeLabel", valueString: "vs last week" },
                { key: "color", valueString: "teal" }
              ]
            },
            {
              key: "systemUptime",
              valueMap: [
                { key: "label", valueString: "System Uptime" },
                { key: "value", valueNumber: 99.7 },
                { key: "unit", valueString: "%" },
                { key: "icon", valueString: "✓" },
                { key: "change", valueNumber: 0.2 },
                { key: "changeLabel", valueString: "vs last month" },
                { key: "color", valueString: "cyan" }
              ]
            }
          ]
        },
        {
          key: "chartData",
          valueMap: [
            { key: "0", valueNumber: 150 },
            { key: "1", valueNumber: 200 },
            { key: "2", valueNumber: 100 },
            { key: "3", valueNumber: 300 }
          ]
        },
        {
          key: "chartLabels",
          valueMap: [
            { key: "0", valueString: "Q1" },
            { key: "1", valueString: "Q2" },
            { key: "2", valueString: "Q3" },
            { key: "3", valueString: "Q4" }
          ]
        },
        {
          key: "lineLabels",
          valueMap: [
            { key: "0", valueString: "Jan" },
            { key: "1", valueString: "Feb" },
            { key: "2", valueString: "Mar" },
            { key: "3", valueString: "Apr" },
            { key: "4", valueString: "May" },
            { key: "5", valueString: "Jun" }
          ]
        },
        {
          key: "lineSeries",
          valueMap: [
            {
              key: "0",
              valueMap: [
                { key: "name", valueString: "Revenue" },
                { key: "color", valueString: "#00D4FF" },
                {
                  key: "values",
                  valueMap: [
                    { key: "0", valueNumber: 45 },
                    { key: "1", valueNumber: 62 },
                    { key: "2", valueNumber: 58 },
                    { key: "3", valueNumber: 85 },
                    { key: "4", valueNumber: 78 },
                    { key: "5", valueNumber: 95 }
                  ]
                }
              ]
            },
            {
              key: "1",
              valueMap: [
                { key: "name", valueString: "Expenses" },
                { key: "color", valueString: "#FF6B6B" },
                {
                  key: "values",
                  valueMap: [
                    { key: "0", valueNumber: 30 },
                    { key: "1", valueNumber: 42 },
                    { key: "2", valueNumber: 35 },
                    { key: "3", valueNumber: 55 },
                    { key: "4", valueNumber: 48 },
                    { key: "5", valueNumber: 60 }
                  ]
                }
              ]
            },
            {
              key: "2",
              valueMap: [
                { key: "name", valueString: "Profit" },
                { key: "color", valueString: "#4ECDC4" },
                {
                  key: "values",
                  valueMap: [
                    { key: "0", valueNumber: 15 },
                    { key: "1", valueNumber: 20 },
                    { key: "2", valueNumber: 23 },
                    { key: "3", valueNumber: 30 },
                    { key: "4", valueNumber: 30 },
                    { key: "5", valueNumber: 35 }
                  ]
                }
              ]
            }
          ]
        },
        {
          key: "mapData",
          valueMap: [
            {
              key: "0",
              valueMap: [
                { key: "name", valueString: "New York" },
                { key: "latitude", valueNumber: 40.7128 },
                { key: "longitude", valueNumber: -74.0060 },
                { key: "description", valueString: "The Big Apple" }
              ]
            },
            {
              key: "1",
              valueMap: [
                { key: "name", valueString: "Boston" },
                { key: "latitude", valueNumber: 42.3601 },
                { key: "longitude", valueNumber: -71.0589 },
                { key: "description", valueString: "Historic city" }
              ]
            }
          ]
        },
        {
          key: "timelineData",
          valueMap: [
            {
              key: "0",
              valueMap: [
                { key: "date", valueString: "2023-01-15" },
                { key: "title", valueString: "Project Start" },
                { key: "description", valueString: "Initial project kickoff" },
                { key: "category", valueString: "Planning" }
              ]
            },
            {
              key: "1",
              valueMap: [
                { key: "date", valueString: "2023-06-01" },
                { key: "title", valueString: "First Release" },
                { key: "description", valueString: "Beta version released" },
                { key: "category", valueString: "Release" }
              ]
            }
          ]
        },
        {
          key: "outageData",
          valueMap: [
            {
              key: "0",
              valueMap: [
                { key: "id", valueString: "OUT-2026-0218" },
                { key: "location", valueString: "Downtown District" },
                { key: "status", valueString: "Active" },
                { key: "severity", valueString: "Critical" },
                { key: "startTime", valueString: "2026-02-18T08:30:00" },
                { key: "estimatedRestoration", valueString: "2026-02-18T14:00:00" },
                { key: "affectedCustomers", valueNumber: 12500 }
              ]
            },
            {
              key: "1",
              valueMap: [
                { key: "id", valueString: "OUT-2026-0217" },
                { key: "location", valueString: "Industrial Park" },
                { key: "status", valueString: "Investigating" },
                { key: "severity", valueString: "High" },
                { key: "startTime", valueString: "2026-02-17T22:15:00" },
                { key: "estimatedRestoration", valueString: "2026-02-18T10:00:00" },
                { key: "affectedCustomers", valueNumber: 4200 }
              ]
            },
            {
              key: "2",
              valueMap: [
                { key: "id", valueString: "OUT-2026-0215" },
                { key: "location", valueString: "Riverside Area" },
                { key: "status", valueString: "Scheduled" },
                { key: "severity", valueString: "Low" },
                { key: "startTime", valueString: "2026-02-20T06:00:00" },
                { key: "estimatedRestoration", valueString: "2026-02-20T12:00:00" },
                { key: "affectedCustomers", valueNumber: 850 }
              ]
            },
            {
              key: "3",
              valueMap: [
                { key: "id", valueString: "OUT-2026-0214" },
                { key: "location", valueString: "North Suburbs" },
                { key: "status", valueString: "Resolved" },
                { key: "severity", valueString: "Medium" },
                { key: "startTime", valueString: "2026-02-16T13:45:00" },
                { key: "estimatedRestoration", valueString: "2026-02-16T18:30:00" },
                { key: "affectedCustomers", valueNumber: 2100 }
              ]
            }
          ]
        }
      ]
    }
  }
];

export class A2UIClient extends EventTarget {
  #serverUrl: string;
  #client: A2AClient | null = null;
  #mockMode: boolean = false;

  constructor(serverUrl: string = "", mockMode: boolean = false) {
    super();
    this.#serverUrl = serverUrl;
    this.#mockMode = mockMode;
  }

  #ready: Promise<void> = Promise.resolve();
  get ready() {
    return this.#ready;
  }

  async #getClient() {
    if (!this.#client) {
      // Default to localhost:10002 if no URL provided (fallback for restaurant app default)
      const baseUrl = this.#serverUrl || "http://localhost:10002";

      this.#client = await A2AClient.fromCardUrl(
        `${baseUrl}/.well-known/agent-card.json`,
        {
          fetchImpl: async (url, init) => {
            const headers = new Headers(init?.headers);
            headers.set("X-A2A-Extensions", "https://a2ui.org/a2a-extension/a2ui/v0.8");
            return fetch(url, { ...init, headers });
          }
        }
      );
    }
    return this.#client;
  }

  async send(
    message: v0_8.Types.A2UIClientEventMessage | string
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    // If in mock mode (serverUrl is "mock" or mockMode is set), return mock messages instead of calling server
    const messages = getMockMessages();
    console.log(message)

    // Simulate streaming events for mock mode - send all messages in one status-update event
    setTimeout(() => {
      this.dispatchEvent(new CustomEvent('streaming-event', {
        detail: {
          kind: 'status-update',
          serverUrl: this.#serverUrl,
          status: {
            message: {
              parts: messages.map(msg => ({
                kind: 'data',
                data: msg
              }))
            }
          },
          final: true
        }
      }));
    }, 500); // Small delay to simulate network

    return messages;
    // const client = await this.#getClient();
    // const catalog = componentRegistry.getInlineCatalog();

    // // Create ClientToServerMessage with inline catalog
    // let clientMessage: any;

    // if (typeof message === 'string') {
    //   // For string messages, wrap as request
    //   clientMessage = {
    //     request: message,
    //   };
    // } else {
    //   // For A2UIClientEventMessage objects, use as-is
    //   clientMessage = message;
    // }

    // // Add inline catalog metadata
    // const finalClientMessage = {
    //   ...clientMessage,
    //   metadata: {
    //     inlineCatalogs: [catalog],
    //   },
    // };

    // // Create part with the ClientToServerMessage
    // const parts: Part[] = [{
    //   kind: "data",
    //   data: finalClientMessage as unknown as Record<string, unknown>,
    //   mimeType: A2UI_MIME_TYPE,
    // } as Part];

    // // Create A2A message
    // const finalMessage = {
    //   messageId: crypto.randomUUID(),
    //   role: "user" as const,
    //   parts: parts,
    //   kind: "message" as const,
    // };

    // // Opens Streaming SSE connection
    // const streamingResponse = client.sendMessageStream({
    //   message: finalMessage,
    // });

    // const messages: v0_8.Types.ServerToClientMessage[] = [];

    // // Process streaming events
    // for await (const event of streamingResponse) {

    //   // Dispatch event for UI status updates
    //   this.dispatchEvent(new CustomEvent('streaming-event', { detail: event }));

    //   // Check if this event contains task status with message parts
    //   // Only add the A2UI messages to render, probably will require handling LLM text responses.
    //   if (event.kind === "status-update" && event.status?.message?.parts) {
    //     for (const part of event.status.message.parts) {
    //       if (part.kind === 'data') {
    //         const a2uiMessage = part.data as v0_8.Types.ServerToClientMessage;
    //         messages.push(a2uiMessage);
    //       }
    //     }
    //   }
    // }
    // return messages;
  }
}

registerShellComponents();
