import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// GeoJSON Data (Markers around NYC)
const geojsonData: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { name: "Statue of Liberty" },
      geometry: {
        type: "Point",
        coordinates: [-74.0445, 40.6892],
      },
    },
    {
      type: "Feature",
      properties: { name: "Central Park" },
      geometry: {
        type: "Point",
        coordinates: [-73.9654, 40.7829],
      },
    },
    {
      type: "Feature",
      properties: { name: "Times Square" },
      geometry: {
        type: "Point",
        coordinates: [-73.9851, 40.758],
      },
    },
    {
      type: "Feature",
      properties: { name: "Brooklyn Bridge" },
      geometry: {
        type: "Point",
        coordinates: [-73.9969, 40.7061],
      },
    },
  ],
};

const map = new maplibregl.Map({
  container: "map",
  // style: "https://demotiles.maplibre.org/style.json",
  style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  center: [-74.006, 40.7328], // NYC
  zoom: 10,
});

map.on("load", () => {
  map.addSource("ny-markers", {
    type: "geojson",
    data: geojsonData,
  });

  map.addLayer({
    id: "ny-markers-layer",
    type: "circle",
    source: "ny-markers",
    paint: {
      "circle-radius": 8,
      "circle-color": "#ff0000",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff",
    },
  });

  // Popup on click
  map.on("click", "ny-markers-layer", (e) => {
    const coordinates = (e.features?.[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number];
    const name = e.features?.[0].properties?.name;

    new maplibregl.Popup()
      .setLngLat(coordinates)
      .setHTML(`<strong>${name}</strong>`)
      .addTo(map);
  });

  // Change cursor on hover
  map.on("mouseenter", "ny-markers-layer", () => {
    map.getCanvas().style.cursor = "pointer";
  });

  map.on("mouseleave", "ny-markers-layer", () => {
    map.getCanvas().style.cursor = "";
  });
});