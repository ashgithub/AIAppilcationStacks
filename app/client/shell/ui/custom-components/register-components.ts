import { componentRegistry } from "@a2ui/lit/ui";
import { RestaurantBarChart } from "./restaurant-bar.js";
import { BarGraph } from "./bar-graph.js";

export function registerShellComponents() {
  // Register RestaurantBarChart
  componentRegistry.register("RestaurantBarChart", RestaurantBarChart, "restaurant-bar-chart", {
    type: "object",
    properties: {
      restaurants: {
        oneOf: [
          {
            type: "array",
            items: {
              type: "object",
              properties: {
                name: { type: "string" },
                cuisine: { type: "string" },
                rating: { type: "number", minimum: 0, maximum: 5 },
                priceRange: { type: "string" },
                description: { type: "string" },
              },
              required: ["name", "cuisine", "rating", "priceRange", "description"],
            },
          },
          {
            type: "object",
            properties: {
              path: { type: "string" },
            },
            required: ["path"],
          },
        ],
      },
    },
    required: ["restaurants"],
  });

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
