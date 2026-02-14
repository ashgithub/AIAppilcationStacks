import { html, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { Root } from "@a2ui/lit/ui";

interface RestaurantData {
  name: string;
  cuisine: string;
  rating: number;
  priceRange: string;
  description: string;
}

@customElement('restaurant-bar-chart')
export class RestaurantBarChart extends Root {
  @property({ attribute: false }) accessor restaurants: any = [];

  static styles = [
    ...Root.styles,
    css`
      :host {
        display: block;
        background: #245fac;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        padding: 16px;
        margin: 8px;
        overflow-x: auto;
      }

      .bar-chart {
        width: 100%;
        font-family: Arial, sans-serif;
      }

      .bar-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        padding: 8px;
        border-radius: 4px;
        background: #f8f9fa;
      }

      .restaurant-name {
        font-weight: 600;
        color: #333;
        min-width: 200px;
        margin-right: 16px;
      }

      .bar-container {
        flex: 1;
        height: 20px;
        background: #e9ecef;
        border-radius: 10px;
        overflow: hidden;
        margin-right: 16px;
      }

      .bar {
        height: 100%;
        background: linear-gradient(90deg, #012f5f, #0978f7);
        border-radius: 10px;
        transition: width 0.3s ease;
      }

      .rating-number {
        font-weight: 500;
        color: #333;
        min-width: 40px;
        text-align: right;
      }

      .empty-state {
        text-align: center;
        color: #666;
        padding: 20px;
        font-style: italic;
      }
    `,
  ];

  render() {
    console.log('RestaurantBarChart render called with:', this.restaurants);
    console.log('surfaceId:', this.surfaceId);
    console.log('processor:', this.processor);
    let restaurantsData: RestaurantData[] = [];

    // Resolve "restaurants" if it is a path object
    const restaurantsAsAny = this.restaurants as any;
    let unresolvedRestaurants: any = this.restaurants;

    if (restaurantsAsAny && typeof restaurantsAsAny === 'object' && 'path' in restaurantsAsAny && restaurantsAsAny.path) {
      console.log('Resolving path:', restaurantsAsAny.path);
      console.log('this.component:', this.component);
      if (this.processor) {
        const resolved = this.processor.getData(this.component, restaurantsAsAny.path, this.surfaceId ?? 'default');
        console.log('Resolved data for /restaurants:', resolved);
        const rootData = this.processor.getData(this.component, '/', this.surfaceId ?? 'default');
        console.log('Root data:', rootData);
        console.log('All surfaces:', Array.from(this.processor.getSurfaces().keys()));
        if (resolved) {
          unresolvedRestaurants = resolved;
        } else if (rootData && typeof rootData === 'object' && 'restaurants' in rootData) {
          console.log('Using restaurants from root data');
          unresolvedRestaurants = (rootData as any).restaurants;
        }
      } else {
        console.log('No processor available');
      }
    }

    // Process the data: convert from valueMap structure to RestaurantData array
    let restaurantsArray: any[] = [];
    if (Array.isArray(unresolvedRestaurants)) {
      restaurantsArray = unresolvedRestaurants;
    } else if (unresolvedRestaurants instanceof Map) {
      // Handle Map-like objects (SignalMap)
      restaurantsArray = Array.from(unresolvedRestaurants.values());
    } else if (unresolvedRestaurants && typeof unresolvedRestaurants === 'object') {
      // Handle single object or other structures
      restaurantsArray = [unresolvedRestaurants];
    }

    restaurantsData = restaurantsArray.map(restaurantEntry => {
      const getVal = (k: string) => {
        if (restaurantEntry instanceof Map) return restaurantEntry.get(k);
        if (restaurantEntry.valueMap) {
          // valueMap is an array of {key, valueString/valueNumber/...}
          const entry = restaurantEntry.valueMap.find((item: any) => item.key === k);
          if (entry) {
            return entry.valueString ?? entry.valueNumber ?? entry.valueBoolean ?? '';
          }
        }
        return (restaurantEntry as any)?.[k] ?? '';
      };

      return {
        name: getVal('name'),
        cuisine: getVal('cuisine'),
        rating: parseFloat(getVal('rating')) || 0,
        priceRange: getVal('priceRange'),
        description: getVal('description'),
      };
    });

    if (!restaurantsData || restaurantsData.length === 0) {
      return html`
        <div class="empty-state">
          No restaurant data available
        </div>
      `;
    }

    return html`
      <div class="bar-chart">
        ${restaurantsData.map(restaurant => this.renderBarItem(restaurant))}
      </div>
    `;
  }

  private renderBarItem(restaurant: RestaurantData) {
    const barWidth = (restaurant.rating / 5) * 100;

    return html`
      <div class="bar-item">
        <div class="restaurant-name">${restaurant.name}</div>
        <div class="bar-container">
          <div class="bar" style="width: ${barWidth}%"></div>
        </div>
        <div class="rating-number">${restaurant.rating.toFixed(1)}</div>
      </div>
    `;
  }
}
