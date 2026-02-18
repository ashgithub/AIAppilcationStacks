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
                explicitList: ["title", "bar-chart", "map-component", "timeline-component"]
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
