import { LitElement, html, css } from "lit"
import { customElement } from "lit/decorators.js"
import "./stat_bar.js"
import { traditionalConfig } from "../configs/traditional_config.js"

@customElement("static-module")
export class StaticModule extends LitElement {
  static styles = css`
    :host {
      display: block;
      flex: 1 1 0;
      min-width: 0;
      overflow: hidden;
      background: linear-gradient(135deg, #308792 0%, #0b788b 100%);
      border-radius: 1rem;
      padding: 0.5rem;
      color: white;
    }

    .content {
      font-size: 1rem;
      line-height: 1.6;
      margin-bottom: 1.5rem;
    }

    .status {
      font-size: 0.875rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 0.5rem;
    }

    .reservation-form {
      padding: 1rem;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      margin-top: 1rem;
    }

    .reservation-form h3 {
      margin: 0 0 1rem 0;
      font-size: 1.2rem;
    }

    .form-group {
      margin-bottom: 1rem;
    }

    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: bold;
    }

    .form-group select {
      width: 100%;
      padding: 0.5rem;
      border: none;
      border-radius: 0.25rem;
      background: rgba(255, 255, 255, 0.9);
      color: #333;
      font-size: 1rem;
    }

    .reserve-btn {
      width: 100%;
      padding: 0.75rem;
      background: rgba(255, 255, 255, 0.2);
      border: none;
      border-radius: 0.25rem;
      color: white;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      transition: background 0.3s;
    }

    .reserve-btn:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  `

  render() {
    return html`
      <stat-bar .title=${"Traditional app"} .time=${""} .tokens=${""} .configUrl=${"/traditional_config"} .configType=${"traditional"} .configData=${traditionalConfig}></stat-bar>
      <div class="reservation-form">
        <h3>Make a Reservation</h3>
        <div class="form-group">
          <label for="restaurant">Restaurant:</label>
          <select id="restaurant">
            <option value="italian">Bella Vista Italian</option>
            <option value="chinese">Golden Dragon Chinese</option>
            <option value="cafe">Central Perk Cafe</option>
          </select>
        </div>
        <div class="form-group">
          <label for="date">Date:</label>
          <select id="date">
            <option value="today">Today</option>
            <option value="tomorrow">Tomorrow</option>
            <option value="friday">This Friday</option>
          </select>
        </div>
        <div class="form-group">
          <label for="time">Time:</label>
          <select id="time">
            <option value="6pm">6:00 PM</option>
            <option value="7pm">7:00 PM</option>
            <option value="8pm">8:00 PM</option>
          </select>
        </div>
        <div class="form-group">
          <label for="guests">Number of Guests:</label>
          <select id="guests">
            <option value="2">2</option>
            <option value="4">4</option>
            <option value="6">6</option>
          </select>
        </div>
        <button class="reserve-btn" @click=${this.handleReserve}>Reserve Table</button>
      </div>
    `
  }

  handleReserve() {
    alert("Reservation request submitted! (This is a mock - no actual booking)")
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "static-module": StaticModule
  }
}
