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

import { config } from "dotenv";
import { UserConfig } from "vite";
import * as Middleware from "./middleware";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function normalizeAppBasePath(rawPath: string | undefined): string {
  const safePath = (rawPath || "/edge_aistack/").trim();
  const withLeadingSlash = safePath.startsWith("/") ? safePath : `/${safePath}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash : `${withLeadingSlash}/`;
}

export default async ({ command }: { command: string }) => {
  config();

  const entry: Record<string, string> = {
    shell: resolve(__dirname, "index.html"),
  };
  const appBasePath = normalizeAppBasePath(process.env.VITE_APP_BASE_PATH);
  const plugins = command === "serve" ? [Middleware.A2AMiddleware.plugin()] : [];

  return {
    base: appBasePath,
    plugins,
    build: {
      rollupOptions: {
        input: entry,
      },
      target: "esnext",
      outDir: "dist_web",
      emptyOutDir: true,
    },
    define: {},
    resolve: {
      dedupe: ["lit"],
    },
  } satisfies UserConfig;
};
