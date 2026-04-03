const DEV_LOCAL_SERVER_ORIGIN = "http://localhost:10002";
const DEFAULT_APP_BASE_PATH = "/edge_aistack/";

function ensureLeadingSlash(value: string): string {
  return value.startsWith("/") ? value : `/${value}`;
}

function ensureTrailingSlash(value: string): string {
  return value.endsWith("/") ? value : `${value}/`;
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function normalizeAppBasePath(rawPath: string | undefined): string {
  const safePath = (rawPath || DEFAULT_APP_BASE_PATH).trim();
  const withLeadingSlash = ensureLeadingSlash(safePath || DEFAULT_APP_BASE_PATH);
  return ensureTrailingSlash(withLeadingSlash);
}

function buildProductionServerOrigin(): string {
  const appBasePath = normalizeAppBasePath(import.meta.env.VITE_APP_BASE_PATH as string | undefined);
  const basePathNoTrailingSlash = stripTrailingSlash(appBasePath);

  if (typeof window === "undefined") {
    return `${basePathNoTrailingSlash}/api`;
  }

  return `${window.location.origin}${basePathNoTrailingSlash}/api`;
}

function resolveDefaultServerOrigin(): string {
  const envOrigin = (import.meta.env.VITE_SERVER_ORIGIN as string | undefined)?.trim();
  if (envOrigin) {
    return stripTrailingSlash(envOrigin);
  }

  if (import.meta.env.DEV) {
    return DEV_LOCAL_SERVER_ORIGIN;
  }

  return stripTrailingSlash(buildProductionServerOrigin());
}

export const APP_BASE_PATH = normalizeAppBasePath(import.meta.env.VITE_APP_BASE_PATH as string | undefined);
export const DEFAULT_SERVER_ORIGIN = resolveDefaultServerOrigin();

export const SERVER_URLS = {
  agent: `${DEFAULT_SERVER_ORIGIN}/agent`,
  llm: `${DEFAULT_SERVER_ORIGIN}/llm`,
  traditional: `${DEFAULT_SERVER_ORIGIN}/traditional`,
  traditionalEnergy: `${DEFAULT_SERVER_ORIGIN}/traditional/energy`,
  traditionalTrends: `${DEFAULT_SERVER_ORIGIN}/traditional/trends`,
  traditionalTimeline: `${DEFAULT_SERVER_ORIGIN}/traditional/timeline`,
  traditionalIndustry: `${DEFAULT_SERVER_ORIGIN}/traditional/industry`,
};

export function buildServerUrl(path: string, origin: string = DEFAULT_SERVER_ORIGIN): string {
  const normalizedOrigin = stripTrailingSlash(origin);
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedOrigin}${normalizedPath}`;
}

export function getServerOrigin(serverUrl: string | undefined): string {
  if (!serverUrl) {
    return DEFAULT_SERVER_ORIGIN;
  }

  try {
    const parsed = new URL(serverUrl, typeof window !== "undefined" ? window.location.origin : "http://localhost");
    let pathname = stripTrailingSlash(parsed.pathname || "");

    const knownEndpointSuffixes = [
      "/agent",
      "/llm",
      "/traditional",
      "/traditional/energy",
      "/traditional/trends",
      "/traditional/timeline",
      "/traditional/industry",
    ];

    for (const suffix of knownEndpointSuffixes) {
      if (pathname.endsWith(suffix)) {
        pathname = pathname.slice(0, -suffix.length);
        break;
      }
    }

    return `${parsed.origin}${pathname}`;
  } catch {
    return DEFAULT_SERVER_ORIGIN;
  }
}
