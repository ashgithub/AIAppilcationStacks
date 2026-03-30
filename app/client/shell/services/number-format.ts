const COMPACT_TOKEN_FORMATTER = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2,
});

function parseNumericInput(value: string | number): number | null {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  const normalized = value.replace(/,/g, "").trim();
  if (!normalized) {
    return 0;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatTokenCountCompact(value: string | number): string {
  const numericValue = parseNumericInput(value);
  if (numericValue === null) {
    return String(value);
  }

  const rounded = Math.round(numericValue);
  if (Math.abs(rounded) < 1000) {
    return new Intl.NumberFormat("en-US").format(rounded);
  }

  return COMPACT_TOKEN_FORMATTER.format(rounded);
}
