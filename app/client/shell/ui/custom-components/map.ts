import { html, css } from "lit";
import { property, customElement, state } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";
import { v0_8 } from "@a2ui/lit";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { colors } from "../../theme/design-tokens.js";
import { ItemSelectEvent } from "./detail-modal.js";

interface MapMarker {
  name: string;
  lat: number;
  lng: number;
  description?: string;
  status?: string;
  details?: Record<string, any>;
}

@customElement('map-component')
export class MapComponent extends Root {
  @property({ attribute: false }) accessor dataPath: any = "";
  @property({ attribute: false }) accessor centerLat: number = 40.7328;
  @property({ attribute: false }) accessor centerLng: number = -74.006;
  @property({ attribute: false }) accessor zoom: number = 10;
  @property({ attribute: false }) accessor showInfoPanel: boolean = true;
  @property({ attribute: false }) accessor action: v0_8.Types.Action | null = null;
  // Backward fallback when no action is supplied in payload.
  @property({ attribute: false }) accessor flagActionName: string = "flag_circuit";

  @state() accessor selectedMarker: MapMarker | null = null;

  private map: maplibregl.Map | null = null;
  private mapContainer!: HTMLElement;
  private resizeObserver: ResizeObserver | null = null;

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        height: var(--map-component-height, 400px);
        width: 100%;
        max-width: 100%;
        min-width: 0;
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-lg);
        background: var(--surface-primary);
      }

      .map-wrapper {
        display: flex;
        height: 100%;
        width: 100%;
        min-width: 0;
      }

      .map-container {
        flex: 1;
        height: 100%;
        min-width: 0;
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

      /* Info panel */
      .map-info-panel {
        width: clamp(180px, 24vw, 280px);
        background: var(--surface-secondary);
        border-left: 1px solid var(--border-primary);
        padding: var(--space-md);
        overflow-y: auto;
        display: flex;
        flex-direction: column;
      }

      @media (max-width: 768px) {
        :host {
          height: auto;
          min-height: var(--map-component-mobile-min-height, 420px);
        }

        .map-wrapper {
          flex-direction: column;
        }

        .map-container {
          min-height: var(--map-component-mobile-map-height, 280px);
        }

        .map-info-panel {
          width: 100%;
          border-left: none;
          border-top: 1px solid var(--border-primary);
          max-height: 38vh;
        }
      }

      .info-panel-header {
        font-size: 14px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin-bottom: var(--space-md);
        padding-bottom: var(--space-sm);
        border-bottom: 1px solid var(--border-primary);
      }

      .info-panel-empty {
        color: var(--text-secondary);
        font-size: 12px;
        font-style: italic;
        text-align: center;
        padding: var(--space-md);
      }

      .marker-info {
        display: flex;
        flex-direction: column;
        gap: var(--space-sm);
      }

      .marker-name {
        font-size: 16px;
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
      }

      .marker-description {
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.4;
      }

      .marker-coords {
        font-size: 11px;
        color: var(--text-muted);
        font-family: var(--font-family-mono);
      }

      .marker-status {
        display: inline-block;
        padding: 4px 8px;
        border-radius: var(--radius-sm);
        font-size: 11px;
        font-weight: var(--font-weight-semibold);
        text-transform: uppercase;
        background: rgba(239, 68, 68, 0.15);
        color: var(--color-error);
        width: fit-content;
      }

      .marker-status.resolved {
        background: rgba(16, 185, 129, 0.15);
        color: var(--color-success);
      }

      .marker-status.pending {
        background: rgba(245, 158, 11, 0.15);
        color: var(--color-warning);
      }

      .marker-details {
        margin-top: var(--space-sm);
        padding-top: var(--space-sm);
        border-top: 1px dashed var(--border-subtle);
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
      }

      .marker-detail-item {
        display: grid;
        grid-template-columns: minmax(70px, 38%) minmax(0, 1fr);
        align-items: start;
        column-gap: var(--space-sm);
        font-size: 12px;
        padding: 2px 0;
      }

      .marker-detail-label {
        color: var(--text-secondary);
        line-height: 1.35;
      }

      .marker-detail-value {
        color: var(--text-primary);
        font-weight: var(--font-weight-medium);
        line-height: 1.4;
        min-width: 0;
        overflow-wrap: anywhere;
        word-break: break-word;
        text-align: left;
      }

      .marker-action-btn {
        margin-top: var(--space-md);
        padding: 8px 12px;
        background: var(--oracle-primary);
        color: white;
        border: none;
        border-radius: var(--radius-sm);
        font-size: 12px;
        cursor: pointer;
        transition: all var(--transition-normal);
        width: 100%;
      }

      .marker-action-btn:hover {
        opacity: 0.9;
        transform: translateY(-1px);
      }

      /* Marker list */
      .markers-list {
        display: flex;
        flex-direction: column;
        gap: var(--space-xs);
        margin-top: var(--space-sm);
      }

      .marker-list-item {
        display: flex;
        align-items: center;
        gap: var(--space-xs);
        padding: var(--space-xs) var(--space-sm);
        background: var(--surface-primary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all var(--transition-normal);
        font-size: 12px;
        color: var(--text-secondary);
      }

      .marker-list-item:hover {
        background: var(--hover-overlay);
        color: var(--text-primary);
      }

      .marker-list-item.active {
        background: var(--oracle-primary);
        color: white;
      }

      .marker-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--color-error);
      }
    `,
  ];

  render() {
    const markers = this.getMarkers();

    // Update markers on the map when data is available and map is loaded
    if (this.map && this.map.isStyleLoaded() && markers.length > 0) {
      this.addMarkers();
    }

    if (markers.length === 0) {
      return html`
        <div class="map-container">
          <div class="empty-state">No map data available</div>
        </div>
      `;
    }

    return html`
      <div class="map-wrapper">
        <div class="map-container"></div>
        ${this.showInfoPanel ? this.renderInfoPanel(markers) : ''}
      </div>
    `;
  }

  private renderInfoPanel(markers: MapMarker[]) {
    return html`
      <div class="map-info-panel">
        ${this.selectedMarker ? this.renderSelectedMarker() : this.renderMarkersList(markers)}
      </div>
    `;
  }

  private renderSelectedMarker() {
    const marker = this.selectedMarker!;
    return html`
      <div class="marker-info">
        <div class="marker-name">${marker.name}</div>
        ${marker.status ? html`
          <span class="marker-status ${this.getStatusClass(marker.status)}">${marker.status}</span>
        ` : ''}
        ${marker.description ? html`
          <div class="marker-description">${marker.description}</div>
        ` : ''}
        <div class="marker-coords">${marker.lat.toFixed(4)}, ${marker.lng.toFixed(4)}</div>
        ${marker.details ? html`
          <div class="marker-details">
            ${Object.entries(marker.details).map(([key, value]) => html`
              <div class="marker-detail-item">
                <span class="marker-detail-label">${this.formatLabel(key)}</span>
                <span class="marker-detail-value">${value}</span>
              </div>
            `)}
          </div>
        ` : ''}
        <button class="marker-action-btn" @click=${() => this.flyToMarker(marker)}>
          Center on Map
        </button>
        <button
          class="marker-action-btn"
          style="background: var(--color-warning); color: var(--surface-primary); margin-top: var(--space-xs);"
          @click=${() => this.flagMarker(marker)}
        >
          Flag Circuit
        </button>
        <button class="marker-action-btn" style="background: var(--surface-primary); color: var(--text-secondary); margin-top: var(--space-xs);" @click=${() => this.clearSelection()}>
          Back to List
        </button>
      </div>
    `;
  }

  private renderMarkersList(markers: MapMarker[]) {
    return html`
      <div class="info-panel-header">Locations (${markers.length})</div>
      <div class="markers-list">
        ${markers.map((marker, index) => html`
          <div 
            class="marker-list-item ${this.selectedMarker === marker ? 'active' : ''}"
            @click=${() => this.selectMarker(marker, index)}
          >
            <span class="marker-dot"></span>
            <span>${marker.name}</span>
          </div>
        `)}
      </div>
    `;
  }

  private selectMarker(marker: MapMarker, index: number) {
    this.selectedMarker = marker;
    this.flyToMarker(marker);
    this.dispatchEvent(new ItemSelectEvent(marker, index));
  }

  private clearSelection() {
    this.selectedMarker = null;
  }

  private flyToMarker(marker: MapMarker) {
    if (this.map) {
      this.map.flyTo({
        center: [marker.lng, marker.lat],
        zoom: Math.max(this.zoom, 12),
        duration: 1000
      });
    }
  }

  private getValidatedActionName(): string {
    const fallback = (this.flagActionName || "flag_circuit").trim();
    const candidate = (this.action?.name || fallback).trim();
    const safeActionNamePattern = /^[a-z][a-z0-9_]{1,63}$/;

    if (!safeActionNamePattern.test(candidate)) {
      console.warn(
        `[MapComponent] Invalid action name "${candidate}". Falling back to "${fallback}".`
      );
      return fallback;
    }

    return candidate;
  }

  private flagMarker(marker: MapMarker) {
    const markerContext: Record<string, unknown> = {
      markerName: marker.name,
      latitude: marker.lat,
      longitude: marker.lng,
      description: marker.description ?? "",
      status: marker.status ?? "",
      ...(marker.details ?? {}),
    };

    const contextEntries: NonNullable<v0_8.Types.Action["context"]> =
      Object.entries(markerContext).map(([key, value]) => {
        if (typeof value === "boolean") {
          return { key, value: { literalBoolean: value } };
        }
        if (typeof value === "number") {
          return { key, value: { literalNumber: value } };
        }
        return { key, value: { literalString: String(value) } };
      });

    const resolvedAction: v0_8.Types.Action = {
      name: this.getValidatedActionName(),
      context: [...(this.action?.context ?? []), ...contextEntries],
    };

    const evt = new v0_8.Events.StateEvent<"a2ui.action">({
      eventType: "a2ui.action",
      action: resolvedAction,
      dataContextPath: this.dataContextPath,
      sourceComponentId: this.id || "map-component",
      sourceComponent: this.component,
    });

    this.dispatchEvent(evt);
  }

  private formatLabel(key: string): string {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .trim();
  }

  private getStatusClass(status: string): string {
    const s = status.toLowerCase();
    if (s.includes('resolved') || s.includes('completed')) return 'resolved';
    if (s.includes('pending') || s.includes('investigating')) return 'pending';
    return '';
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
    this.resizeObserver.observe(this.mapContainer);
  }

  updated(changedProperties: Map<string | number | symbol, unknown>) {
    super.updated(changedProperties);
    if (changedProperties.has('dataPath') || changedProperties.has('centerLat') || changedProperties.has('centerLng') || changedProperties.has('zoom')) {
      this.updateMap();
    }

    if (changedProperties.has('showInfoPanel') && this.map) {
      // The map canvas needs an explicit resize when side panel visibility changes.
      requestAnimationFrame(() => this.map?.resize());
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
            let details: Record<string, any> = {};

            if (item instanceof Map) {
              // Handle A2UI Map structure: Map('name' -> 'New York', 'latitude' -> 40.7128, ...)
              const knownKeys = ['name', 'latitude', 'lat', 'longitude', 'lng', 'description', 'status'];
              for (const [key, value] of item.entries()) {
                if (key === 'name') markerData.name = value;
                else if (key === 'latitude' || key === 'lat') markerData.lat = value;
                else if (key === 'longitude' || key === 'lng') markerData.lng = value;
                else if (key === 'description') markerData.description = value;
                else if (key === 'status') markerData.status = value;
                else if (!knownKeys.includes(key)) {
                  // Collect unknown keys as details
                  details[key] = value;
                }
              }
            } else if (typeof item === 'object') {
              if (item.lat !== undefined && item.lng !== undefined) {
                // Handle direct structure: {lat, lng, name, description, status, details, ...}
                markerData = { ...item };
                // If there's a details field, use it; otherwise extract extra fields
                if (!item.details) {
                  const knownKeys = ['name', 'lat', 'latitude', 'lng', 'longitude', 'description', 'status', 'title', 'info'];
                  for (const key of Object.keys(item)) {
                    if (!knownKeys.includes(key)) {
                      details[key] = item[key];
                    }
                  }
                }
              } else if (item.valueMap && Array.isArray(item.valueMap)) {
                // Handle A2UI structure: {valueMap: [{key: 'name', valueString: ...}, ...]}
                const knownKeys = ['name', 'lat', 'latitude', 'lng', 'longitude', 'description', 'status'];
                item.valueMap.forEach((entry: any) => {
                  const key = entry.key;
                  const value = entry.valueString ?? entry.valueNumber ?? entry.valueBoolean;
                  
                  if (key === 'name' && entry.valueString) markerData.name = entry.valueString;
                  else if ((key === 'lat' || key === 'latitude') && entry.valueNumber !== undefined) markerData.lat = entry.valueNumber;
                  else if ((key === 'lng' || key === 'longitude') && entry.valueNumber !== undefined) markerData.lng = entry.valueNumber;
                  else if (key === 'description' && entry.valueString) markerData.description = entry.valueString;
                  else if (key === 'status' && entry.valueString) markerData.status = entry.valueString;
                  else if (!knownKeys.includes(key) && value !== undefined) {
                    // Collect unknown keys as details
                    details[key] = value;
                  }
                });
              }
            }

            if (markerData.lat !== undefined && markerData.lng !== undefined) {
              return {
                name: markerData.name || markerData.title || 'Location',
                lat: parseFloat(markerData.lat),
                lng: parseFloat(markerData.lng),
                description: markerData.description || markerData.info || '',
                status: markerData.status,
                details: Object.keys(details).length > 0 ? details : (markerData.details || undefined)
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

    // Remove existing layers and source
    if (this.map.getLayer('markers-layer')) {
      this.map.removeLayer('markers-layer');
    }
    if (this.map.getSource('markers')) {
      this.map.removeSource('markers');
    }

    if (markers.length > 0) {
      const geojson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: markers.map((marker, index) => ({
          type: "Feature",
          properties: { 
            name: marker.name, 
            description: marker.description,
            status: marker.status,
            index: index
          },
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
          "circle-radius": 10,
          "circle-color": colors.semantic.error,
          "circle-stroke-width": 3,
          "circle-stroke-color": "#ffffff",
        },
      });

      // Change cursor on hover
      this.map.on("mouseenter", "markers-layer", () => {
        if (this.map) {
          this.map.getCanvas().style.cursor = "pointer";
        }
      });

      this.map.on("mouseleave", "markers-layer", () => {
        if (this.map) {
          this.map.getCanvas().style.cursor = "";
        }
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
