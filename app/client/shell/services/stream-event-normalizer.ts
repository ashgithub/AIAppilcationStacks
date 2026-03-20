import { v0_8 } from "@a2ui/lit";

type StreamPart = {
  kind?: string;
  text?: string;
  data?: unknown;
};

type RawStreamingEvent = {
  kind?: string;
  final?: boolean;
  status?: {
    state?: string;
    message?: {
      parts?: StreamPart[];
    };
  };
};

export interface NormalizedStreamingEvent {
  kind: string;
  isFinal: boolean;
  state: string | null;
  textParts: string[];
  uiMessages: v0_8.Types.ServerToClientMessage[];
  statusText: string;
  responseText: string;
  tokenCount: string;
  suggestionsRaw: string;
  suggestions: string[];
  sources: string[];
}

export function parseSuggestionsList(suggestionsText: string): string[] {
  if (!suggestionsText || !suggestionsText.trim()) {
    return [];
  }

  try {
    const parsed = JSON.parse(suggestionsText);
    if (parsed && Array.isArray(parsed.suggested_questions)) {
      return parsed.suggested_questions
        .map((s: unknown) => String(s).trim())
        .filter((s: string) => s.length > 0);
    }
  } catch {
    // Fall through to text parsing.
  }

  let suggestions = suggestionsText
    .split(/\n/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  if (suggestions.length === 1) {
    suggestions = suggestions[0]
      .split(/[,;]/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  return suggestions.map((s) => s.replace(/^(\d+[\.\)]\s*|[-•]\s*)/, "").trim());
}

export function parseSourcesList(sourcesText: string): string[] {
  if (!sourcesText || !sourcesText.trim()) {
    return [];
  }

  try {
    const parsed = JSON.parse(sourcesText);
    if (Array.isArray(parsed)) {
      return [...new Set(parsed.map((s) => String(s).trim()).filter((s) => s.length > 0))];
    }
  } catch {
    // Fall back to CSV-ish parsing.
  }

  return sourcesText
    .replace(/^\[|\]$/g, "")
    .split(",")
    .map((s) => s.replace(/^["'\s]+|["'\s]+$/g, "").trim())
    .filter((s) => s.length > 0);
}

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

function pickMetadataFromFinalTextParts(textParts: string[]) {
  let tokenCount = "";
  let suggestionsRaw = "";
  let sources: string[] = [];
  const used = new Set<number>();

  for (let i = textParts.length - 1; i >= 0; i -= 1) {
    const parsedSources = tryParseSourcesMetadata(textParts[i]);
    if (parsedSources.length > 0) {
      sources = parsedSources;
      used.add(i);
      break;
    }
  }

  for (let i = textParts.length - 1; i >= 0; i -= 1) {
    if (used.has(i)) {
      continue;
    }
    const parsedSuggestions = tryParseSuggestionsMetadata(textParts[i]);
    if (parsedSuggestions.length > 0) {
      suggestionsRaw = textParts[i];
      used.add(i);
      break;
    }
  }

  for (let i = textParts.length - 1; i >= 0; i -= 1) {
    if (used.has(i)) {
      continue;
    }
    const value = textParts[i]?.trim();
    if (/^-?\d+(\.\d+)?$/.test(value)) {
      tokenCount = value;
      used.add(i);
      break;
    }
  }

  let responseText = "";
  for (let i = 0; i < textParts.length; i += 1) {
    if (!used.has(i) && textParts[i].trim().length > 0) {
      responseText = textParts[i];
      break;
    }
  }

  if (!responseText && textParts.length > 0) {
    responseText = textParts[0];
  }

  return {
    tokenCount,
    suggestionsRaw,
    sources,
    responseText,
  };
}

function tryParseSuggestionsMetadata(value: string): string[] {
  try {
    const parsed = JSON.parse(value);
    if (parsed && Array.isArray(parsed.suggested_questions)) {
      return parsed.suggested_questions
        .map((s: unknown) => String(s).trim())
        .filter((s: string) => s.length > 0);
    }
  } catch {
    // Ignore. Metadata parser should remain strict.
  }
  return [];
}

function tryParseSourcesMetadata(value: string): string[] {
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.map((s) => String(s).trim()).filter((s) => s.length > 0);
    }
  } catch {
    // Ignore. Metadata parser should remain strict.
  }
  return [];
}

export function normalizeStreamingEvent(raw: unknown): NormalizedStreamingEvent {
  const event = (raw || {}) as RawStreamingEvent;
  const kind = event.kind || "unknown";
  const isFinal = Boolean(event.final);
  const state = event.status?.state || null;
  const parts = event.status?.message?.parts || [];

  const textParts: string[] = [];
  const uiMessages: v0_8.Types.ServerToClientMessage[] = [];

  for (const part of parts) {
    if (part.kind === "text" && typeof part.text === "string") {
      textParts.push(part.text);
      continue;
    }

    if (part.kind === "data") {
      if (Array.isArray(part.data)) {
        for (const item of part.data) {
          if (isServerToClientMessage(item)) {
            uiMessages.push(item);
          }
        }
      } else if (isServerToClientMessage(part.data)) {
        uiMessages.push(part.data);
      }
    }
  }

  let responseText = textParts[0] || "";
  let tokenCount = "";
  let suggestionsRaw = "";
  let sources: string[] = [];

  if (kind === "status-update" && isFinal) {
    const parsed = pickMetadataFromFinalTextParts(textParts);
    responseText = parsed.responseText;
    tokenCount = parsed.tokenCount;
    suggestionsRaw = parsed.suggestionsRaw;
    sources = parsed.sources;
  }

  const statusText = responseText || (textParts[0] || "No text content");

  return {
    kind,
    isFinal,
    state,
    textParts,
    uiMessages,
    statusText,
    responseText,
    tokenCount,
    suggestionsRaw,
    suggestions: parseSuggestionsList(suggestionsRaw),
    sources,
  };
}
