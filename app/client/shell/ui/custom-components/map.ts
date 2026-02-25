import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { colors } from "../../theme/design-tokens.js";

interface MapMarker {
  name: string;
  lat: number;
  lng: number;
  description?: string;
}

@customElement('map-component')
export class MapComponent extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor centerLat: number = 40.7328;
  @property({ attribute: false }) accessor centerLng: number = -74.006;
  @property({ attribute: false }) accessor zoom: number = 10;

  private map: maplibregl.Map | null = null;
  private mapContainer!: HTMLElement;
  private resizeObserver: ResizeObserver | null = null;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        height: 400px;
        width: 100%;
        max-width: 600px;
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-lg);
        margin: var(--space-xs);
        background: var(--surface-primary);
      }

      .map-container {
        height: 100%;
        width: 100%;
        position: relative;
        box-sizing: border-box;
      }

      .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--text-muted);
        font-style: italic;
      }
    `,
  ];

  render() {
    const markers = this.getMarkers();

    // Update markers on the map when data is available and map is loaded
    if (this.map && this.map.isStyleLoaded() && markers.length > 0) {
      this.addMarkers();
    }

    return html`
      <div class="map-container">
        ${markers.length === 0 ? html`<div class="empty-state">No map data available</div>` : ''}
      </div>
    `;
  }

  firstUpdated() {
    this.mapContainer = this.shadowRoot!.querySelector('.map-container') as HTMLElement;
    this.initializeMap();

    this.resizeObserver = new ResizeObserver(() => {
      if (this.map) {
        this.map.resize();
      }
    });
    this.resizeObserver.observe(this);
  }

  updated(changedProperties: Map<string | number | symbol, unknown>) {
    super.updated(changedProperties);
    if (changedProperties.has('dataPath') || changedProperties.has('centerLat') || changedProperties.has('centerLng') || changedProperties.has('zoom')) {
      this.updateMap();
    }
  }

  private getCenter(): [number, number] {
    return [this.centerLng, this.centerLat];
  }

  private getMarkers(): MapMarker[] {
    let markers: MapMarker[] = [];

    if (this.dataPath && typeof this.dataPath === 'string') {
      if (this.processor) {
        let data = this.processor.getData(this.component, this.dataPath, this.surfaceId ?? 'default') as any;

        if (data instanceof Map) {
          data = Array.from(data.values());
        }

        if (Array.isArray(data)) {
          markers = data.map((item: any) => {
            let markerData: any = {};

            if (item instanceof Map) {
              // Handle A2UI Map structure: Map('name' -> 'New York', 'latitude' -> 40.7128, ...)
              for (const [key, value] of item.entries()) {
                if (key === 'name') markerData.name = value;
                if (key === 'latitude' || key === 'lat') markerData.lat = value;
                if (key === 'longitude' || key === 'lng') markerData.lng = value;
                if (key === 'description') markerData.description = value;
              }
            } else if (typeof item === 'object') {
              if (item.lat !== undefined && item.lng !== undefined) {
                // Handle direct structure: {lat, lng, name, description}
                markerData = item;
              } else if (item.valueMap && Array.isArray(item.valueMap)) {
                // Handle A2UI structure: {valueMap: [{key: 'name', valueString: ...}, ...]}
                item.valueMap.forEach((entry: any) => {
                  if (entry.key === 'name' && entry.valueString) markerData.name = entry.valueString;
                  if ((entry.key === 'lat' || entry.key === 'latitude') && entry.valueNumber !== undefined) markerData.lat = entry.valueNumber;
                  if ((entry.key === 'lng' || entry.key === 'longitude') && entry.valueNumber !== undefined) markerData.lng = entry.valueNumber;
                  if (entry.key === 'description' && entry.valueString) markerData.description = entry.valueString;
                });
              }
            }

            if (markerData.lat !== undefined && markerData.lng !== undefined) {
              return {
                name: markerData.name || markerData.title || 'Location',
                lat: parseFloat(markerData.lat),
                lng: parseFloat(markerData.lng),
                description: markerData.description || markerData.info || ''
              };
            }
            return null;
          }).filter(Boolean) as MapMarker[];
        }
      }
    }

    return markers;
  }

  private initializeMap() {
    if (!this.mapContainer) return;

    this.map = new maplibregl.Map({
      container: this.mapContainer,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
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
    if (this.map.isStyleLoaded()) {
      this.addMarkers();
    }
  }

  private addMarkers() {
    if (!this.map || !this.map.isStyleLoaded()) return;

    const markers = this.getMarkers();

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

      // Popup on click TODO: fix
      this.map.on("click", "markers-layer", (e) => {
        const coordinates = (e.features?.[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number];
        const name = e.features?.[0].properties?.name;

        const popup = new maplibregl.Popup({ anchor: 'top' })
          .setLngLat(coordinates)
          .setHTML(`<strong>${name}</strong>`);

        // Add to map first for positioning, then move to document.body
        popup.addTo(this.map!);
        const el = popup.getElement();
        if (el && el.parentNode) {
          el.parentNode.removeChild(el);
          document.body.appendChild(el);
        }
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
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }
    super.disconnectedCallback();
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}