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
    message: v0_8.Types.A2UIClientEventMessage | string,
    sessionId?: string
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

    const finalClientMessage = {
      ...clientMessage,
      metadata: {
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
    });

    const messages: v0_8.Types.ServerToClientMessage[] = [];

    for await (const event of streamingResponse) {
      this.dispatchEvent(new CustomEvent('streaming-event', { detail: event }));

      if (event.kind === "status-update" && event.status?.message?.parts) {
        for (const part of event.status.message.parts) {
          if (part.kind === 'data') {
            const a2uiMessage = part.data as v0_8.Types.ServerToClientMessage;
            messages.push(a2uiMessage);
          }
        }
      }
    }
    return messages;
  }
}

registerShellComponents();
