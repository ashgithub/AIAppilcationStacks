export const DEFAULT_SERVER_ORIGIN = "http://localhost:10002";

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
  if (!path.startsWith("/")) {
    return `${origin}/${path}`;
  }
  return `${origin}${path}`;
}

export function getServerOrigin(serverUrl: string | undefined): string {
  if (!serverUrl) {
    return DEFAULT_SERVER_ORIGIN;
  }

  try {
    return new URL(serverUrl).origin;
  } catch {
    return DEFAULT_SERVER_ORIGIN;
  }
}
