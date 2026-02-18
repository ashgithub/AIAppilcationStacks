import { componentRegistry } from "@a2ui/lit/ui";
import { BarGraph } from "./bar-graph.js";
import { LineGraph } from "./line-graph.js";
import { MapComponent } from "./map.js";
import { TimelineComponent } from "./timeline.js";
import { OutageTable } from "./outage-table.js";
import { KpiCard, KpiCardGroup } from "./kpi-card.js";

export function registerShellComponents() {
  // Register BarGraph
  componentRegistry.register("BarGraph", BarGraph, "bar-graph", {
    type: "object",
    properties: {
      dataPath: { type: "string" },
      labelPath: { type: "string" },
      orientation: { type: "string", enum: ["vertical", "horizontal"] },
      barWidth: { type: "number" },
      gap: { type: "number" },
    },
    required: ["dataPath", "labelPath"],
  });

  // Register LineGraph
  componentRegistry.register("LineGraph", LineGraph, "line-graph", {
    type: "object",
    properties: {
      dataPath: { type: "string", description: "Path to single series data (for backward compatibility)" },
      labelPath: { type: "string", description: "Path to x-axis labels array" },
      seriesPath: { type: "string", description: "Path to array of series objects [{name, values, color}]" },
      showPoints: { type: "boolean", description: "Show data points on the line" },
      showArea: { type: "boolean", description: "Fill area under the line" },
      strokeWidth: { type: "number", description: "Line stroke width" },
      animated: { type: "boolean", description: "Enable line drawing animation" },
    },
    required: ["labelPath"],
  });

  // Register MapComponent
  componentRegistry.register("MapComponent", MapComponent, "map-component", {
    type: "object",
    properties: {
      dataPath: { type: "string" },
      centerLat: { type: "number" },
      centerLng: { type: "number" },
      zoom: { type: "number" },
    },
    required: [],
  });

  // Register TimelineComponent
  componentRegistry.register("TimelineComponent", TimelineComponent, "timeline-component", {
    type: "object",
    properties: {
      dataPath: { type: "string" },
    },
    required: [],
  });

  // Register OutageTable
  componentRegistry.register("OutageTable", OutageTable, "outage-table", {
    type: "object",
    properties: {
      dataPath: { type: "string", description: "Path to array of outage records" },
      title: { type: "string", description: "Table title" },
      showPagination: { type: "boolean", description: "Show pagination controls" },
      pageSize: { type: "number", description: "Number of records per page" },
    },
    required: ["dataPath"],
  });

  // Register KpiCard
  componentRegistry.register("KpiCard", KpiCard, "kpi-card", {
    type: "object",
    properties: {
      dataPath: { type: "string", description: "Path to KPI data object" },
      label: { type: "string", description: "KPI label text" },
      value: { type: "number", description: "KPI value" },
      unit: { type: "string", description: "Unit suffix (e.g., %, kWh)" },
      change: { type: "number", description: "Percentage change from previous period" },
      changeLabel: { type: "string", description: "Change period label (e.g., vs last month)" },
      icon: { type: "string", description: "Icon character or emoji" },
      colorTheme: { type: "string", enum: ["cyan", "coral", "teal", "yellow", "purple", "green", "pink", "orange"] },
      compact: { type: "boolean", description: "Use compact sizing" },
    },
    required: [],
  });

  // Register KpiCardGroup
  componentRegistry.register("KpiCardGroup", KpiCardGroup, "kpi-card-group", {
    type: "object",
    properties: {
      dataPath: { type: "string", description: "Path to array of KPI data objects" },
      title: { type: "string", description: "Group title" },
      compact: { type: "boolean", description: "Use compact sizing for all cards" },
    },
    required: ["dataPath"],
  });

  console.log("Registered Shell Custom Components");
}
