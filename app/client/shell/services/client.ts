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
import { DEFAULT_SERVER_ORIGIN } from "./server-endpoints.js";

const A2UI_MIME_TYPE = "application/json+a2ui";
const A2UI_STANDARD_CATALOG_ID = "https://a2ui.org/specification/v0_8/standard_catalog_definition.json";

function isServerToClientMessage(value: unknown): value is v0_8.Types.ServerToClientMessage {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return Boolean(
    candidate.beginRendering ||
      candidate.surfaceUpdate ||
      candidate.dataModelUpdate ||
      candidate.deleteSurface
  );
}

function collectServerMessages(value: unknown, out: v0_8.Types.ServerToClientMessage[]): void {
  if (!value) return;

  if (Array.isArray(value)) {
    for (const item of value) {
      collectServerMessages(item, out);
    }
    return;
  }

  if (isServerToClientMessage(value)) {
    out.push(value);
    return;
  }

  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if ("data" in obj) collectServerMessages(obj.data, out);
    if ("root" in obj) collectServerMessages(obj.root, out);
    if ("part" in obj) collectServerMessages(obj.part, out);
    if ("payload" in obj) collectServerMessages(obj.payload, out);
  }
}

export class A2UIClient extends EventTarget {
  #serverUrl: string;
  #client: A2AClient | null = null;

  constructor(serverUrl: string = "") {
    super();
    this.#serverUrl = serverUrl;
  }

  #ready: Promise<void> = Promise.resolve();
  get ready() {
    return this.#ready;
  }

  async #getClient() {
    if (!this.#client) {
      const baseUrl = this.#serverUrl || DEFAULT_SERVER_ORIGIN;

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
    message: v0_8.Types.A2UIClientEventMessage | string,
    sessionId?: string,
    requestId?: string
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    const client = await this.#getClient();
    const catalog = componentRegistry.getInlineCatalog();

    let clientMessage: any;

    if (typeof message === 'string') {
      clientMessage = {
        request: message,
      };
    } else {
      clientMessage = message;
    }

    const supportedCatalogIds = new Set<string>([A2UI_STANDARD_CATALOG_ID]);
    const catalogId = (catalog as { catalogId?: string } | null | undefined)?.catalogId;
    if (catalogId) {
      supportedCatalogIds.add(catalogId);
    }

    const finalClientMessage = {
      ...clientMessage,
      metadata: {
        a2uiClientCapabilities: {
          supportedCatalogIds: Array.from(supportedCatalogIds),
          inlineCatalogs: [catalog],
        },
        // Backward compatibility for server handlers still reading metadata.inlineCatalogs directly.
        inlineCatalogs: [catalog],
        ...(sessionId && { sessionId }),
      },
    };

    const parts: Part[] = [{
      kind: "data",
      data: finalClientMessage as unknown as Record<string, unknown>,
      mimeType: A2UI_MIME_TYPE,
    } as Part];

    const finalMessage = {
      messageId: crypto.randomUUID(),
      role: "user" as const,
      parts: parts,
      kind: "message" as const,
    };

    const streamingResponse = client.sendMessageStream({
      message: finalMessage,
      configuration: {
        acceptedOutputModes: [
          "text",
          "text/plain",
          "text/event-stream",
          A2UI_MIME_TYPE,
        ],
      },
    });

    const messages: v0_8.Types.ServerToClientMessage[] = [];

    for await (const event of streamingResponse) {
      this.dispatchEvent(new CustomEvent('streaming-event', {
        detail: {
          ...event,
          clientRequestId: requestId
        }
      }));

      const statusParts = event.kind === "status-update" ? (event.status?.message?.parts || []) : [];
      const artifactParts = event.kind === "artifact-update" ? (event.artifact?.parts || []) : [];

      for (const part of [...statusParts, ...artifactParts]) {
        if (part.kind === "data") {
          collectServerMessages(part.data, messages);
          continue;
        }
        const root = (part as { root?: { kind?: string; data?: unknown } }).root;
        if (root?.kind === "data") {
          collectServerMessages(root.data, messages);
        }
      }
    }
    return messages;
  }
}

registerShellComponents();
