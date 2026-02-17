import { componentRegistry } from "@a2ui/lit/ui";
import { BarGraph } from "./bar-graph.js";
import { MapComponent } from "./map.js";
import { TimelineComponent } from "./timeline.js";

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

  // Register MapComponent
  componentRegistry.register("MapComponent", MapComponent, "map-component", {
    type: "object",
    properties: {
      dataPath: { type: "string" },
      markersPath: { type: "string" },
      center: { type: "object" },
      centerLat: { type: "number" },
      centerLng: { type: "number" },
      zoom: { type: "number" },
      styleUrl: { type: "string" },
      markerColor: { type: "string" },
      title: { type: "string" },
    },
    required: [],
  });

  // Register TimelineComponent
  componentRegistry.register("TimelineComponent", TimelineComponent, "timeline-component", {
    type: "object",
    properties: {
      dataPath: { type: "string" },
      eventsPath: { type: "string" },
      dateFormat: { type: "string" },
      eventColor: { type: "string" },
      lineColor: { type: "string" },
      title: { type: "string" },
    },
    required: [],
  });

  console.log("Registered Shell Custom Components");
}
