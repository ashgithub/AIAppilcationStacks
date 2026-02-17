import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface MapMarker {
  name: string;
  lat: number;
  lng: number;
  description?: string;
}

@customElement('map-component')
export class MapComponent extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor markersPath: any = ""; // Keep for backward compatibility
  @property({ attribute: false }) accessor centerLat: number = 40.7328;
  @property({ attribute: false }) accessor centerLng: number = -74.006;
  @property({ attribute: false }) accessor center: any = null;
  @property({ attribute: false }) accessor zoom: number = 10;
  @property({ attribute: false }) accessor styleUrl: string = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
  @property({ attribute: false }) accessor markerColor: string = "#ff0000";
  @property({ attribute: false }) accessor title: string = "";

  private map: maplibregl.Map | null = null;
  private mapContainer: HTMLElement | null = null;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        height: 400px;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin: 8px;
      }

      .map-container {
        height: 100%;
        width: 100%;
      }

      .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #666;
        font-style: italic;
      }
    `,
  ];

  render() {
    let markers: MapMarker[] = [];

    // Use dataPath if provided (server preference), otherwise markersPath
    const dataSource = this.dataPath || this.markersPath;

    // Resolve data source
    if (dataSource && typeof dataSource === 'string') {
      if (this.processor) {
        let data = this.processor.getData(this.component, dataSource, this.surfaceId ?? 'default') as any;

        if (data instanceof Map) {
          data = Array.from(data.values());
        }

        if (Array.isArray(data)) {
          markers = data.map((item: any) => {
            if (typeof item === 'object' && item.lat !== undefined && item.lng !== undefined) {
              // Handle server payload structure: {info, lat, lng, title}
              return {
                name: item.title || item.location || 'Location',
                lat: parseFloat(item.lat),
                lng: parseFloat(item.lng),
                description: item.info || item.customers ? `${item.customers} affected` : item.title
              };
            }
            return null;
          }).filter(Boolean) as MapMarker[];
        }
      }
    }

    return html`
      <div class="map-container" ${this.mapContainer = this.mapContainer}>
        ${markers.length === 0 ? html`<div class="empty-state">No map data available</div>` : ''}
      </div>
    `;
  }

  firstUpdated() {
    this.initializeMap();
  }

  updated(changedProperties: Map<string | number | symbol, unknown>) {
    super.updated(changedProperties);
    if (changedProperties.has('dataPath') || changedProperties.has('markersPath') || changedProperties.has('centerLat') || changedProperties.has('centerLng') || changedProperties.has('center') || changedProperties.has('zoom') || changedProperties.has('styleUrl')) {
      this.updateMap();
    }
  }

  private getCenter(): [number, number] {
    if (this.center && typeof this.center === 'object' && this.center.lng !== undefined && this.center.lat !== undefined) {
      return [this.center.lng, this.center.lat];
    }
    return [this.centerLng, this.centerLat];
  }

  private initializeMap() {
    if (!this.mapContainer) return;

    this.map = new maplibregl.Map({
      container: this.mapContainer,
      style: this.styleUrl,
      center: this.getCenter(),
      zoom: this.zoom,
    });

    this.map.on('load', () => {
      this.addMarkers();
    });
  }

  private updateMap() {
    if (!this.map) return;

    this.map.setCenter(this.getCenter());
    this.map.setZoom(this.zoom);
    this.map.setStyle(this.styleUrl);

    // Re-add markers after style change
    this.map.on('style.load', () => {
      this.addMarkers();
    });
  }

  private addMarkers() {
    if (!this.map) return;

    let markers: MapMarker[] = [];

    // Use dataPath if provided (server preference), otherwise markersPath
    const dataSource = this.dataPath || this.markersPath;

    // Get current data
    if (dataSource && typeof dataSource === 'string') {
      if (this.processor) {
        let data = this.processor.getData(this.component, dataSource, this.surfaceId ?? 'default') as any;

        if (data instanceof Map) {
          data = Array.from(data.values());
        }

        if (Array.isArray(data)) {
          markers = data.map((item: any) => {
            if (typeof item === 'object' && item.lat !== undefined && item.lng !== undefined) {
              // Handle server payload structure: {info, lat, lng, title}
              return {
                name: item.title || item.location || 'Location',
                lat: parseFloat(item.lat),
                lng: parseFloat(item.lng),
                description: item.info || item.customers ? `${item.customers} affected` : item.title
              };
            }
            return null;
          }).filter(Boolean) as MapMarker[];
        }
      }
    }

    // Remove existing markers
    if (this.map.getSource('markers')) {
      this.map.removeLayer('markers-layer');
      this.map.removeSource('markers');
    }

    if (markers.length > 0) {
      const geojson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: markers.map(marker => ({
          type: "Feature",
          properties: { name: marker.name, description: marker.description },
          geometry: {
            type: "Point",
            coordinates: [marker.lng, marker.lat],
          },
        })),
      };

      this.map.addSource("markers", {
        type: "geojson",
        data: geojson,
      });

      this.map.addLayer({
        id: "markers-layer",
        type: "circle",
        source: "markers",
        paint: {
          "circle-radius": 8,
          "circle-color": "#ff0000",
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      // Popup on click
      this.map.on("click", "markers-layer", (e) => {
        const coordinates = (e.features?.[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number];
        const name = e.features?.[0].properties?.name;
        const description = e.features?.[0].properties?.description;

        new maplibregl.Popup()
          .setLngLat(coordinates)
          .setHTML(`<strong>${name}</strong><br>${description || ''}`)
          .addTo(this.map!);
      });

      // Change cursor on hover
      this.map.on("mouseenter", "markers-layer", () => {
        this.map!.getCanvas().style.cursor = "pointer";
      });

      this.map.on("mouseleave", "markers-layer", () => {
        this.map!.getCanvas().style.cursor = "";
      });
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}