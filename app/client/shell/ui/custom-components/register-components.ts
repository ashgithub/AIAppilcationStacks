import { componentRegistry } from "@a2ui/lit/ui";
import { BarGraph } from "./bar-graph.js";

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

  console.log("Registered Shell Custom Components");
}
