import { LitElement, html, css, svg, nothing } from "lit"
import { customElement, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { designTokensCSS } from "../theme/design-tokens.js"
import { SERVER_URLS } from "../services/server-endpoints.js";

type SendTarget = "chat" | "both" | "agent";
type QuickQueryIcon = "pin" | "warning" | "metrics" | "status" | "shield" | "report";

interface QuickQuery {
  id: string;
  title: string;
  description: string;
  query: string;
  icon: QuickQueryIcon;
}

const QUICK_QUERIES: QuickQuery[] = [
  {
    id: "outage-causes",
    title: "Outage Causes",
    description: "Shows a map and bar graph to explain outages",
    query: "Show outage causes with map and bar graph breakdown.",
    icon: "pin",
  },
  {
    id: "latest-outage-zones",
    title: "Latest Outage Zones",
    description: "Display recent outage areas with severity levels",
    query: "Show the latest outage zones with severity levels.",
    icon: "warning",
  },
  {
    id: "performance-metrics",
    title: "Performance Metrics",
    description: "System performance dashboard with KPIs",
    query: "Show system performance metrics and KPI trends.",
    icon: "metrics",
  },
  {
    id: "real-time-status",
    title: "Real-time Status",
    description: "Live system health monitoring view",
    query: "Give me a real-time status summary of all modules.",
    icon: "status",
  },
  {
    id: "risk-summary",
    title: "Risk Summary",
    description: "Summarize top risks and current mitigation priority",
    query: "Summarize the top current outage risks and mitigation priorities.",
    icon: "shield",
  },
  {
    id: "incident-report",
    title: "Incident Brief",
    description: "Create a concise operational incident report",
    query: "Create a concise incident report with impact, root cause, and next steps.",
    icon: "report",
  },
];

// #region Component
@customElement("chat-input")
export class ChatInput extends LitElement {
  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @state()
  accessor #inputValue = ""

  @state()
  accessor #filterTerm = ""

  @state()
  accessor #drawerOpen = false

  @state()
  accessor #activeSuggestionIndex = -1

  @state()
  accessor #defaultTarget: SendTarget = "chat"

  private llmDefaultServer = SERVER_URLS.llm;
  private agentDefaultServer = SERVER_URLS.agent;
  readonly #drawerId = "quick-query-listbox";
  private filterDebounceTimer?: number;

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener("pointerdown", this.handlePointerDownOutside);
  }

  disconnectedCallback() {
    window.removeEventListener("pointerdown", this.handlePointerDownOutside);
    if (this.filterDebounceTimer) {
      window.clearTimeout(this.filterDebounceTimer);
    }
    super.disconnectedCallback();
  }

  // #region Styles
  static styles = css`
    ${designTokensCSS}

    :host {
      display: block;
      width: 100%;
      --composer-control-height: calc(var(--space-xl) + var(--space-xs));
      --composer-gap: var(--space-xs);
    }

    .composer-shell {
      position: relative;
      width: 100%;
    }

    .composer {
      display: flex;
      align-items: center;
      gap: var(--composer-gap);
      padding: var(--space-xs) var(--space-sm);
      background: var(--surface-primary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-sm);
      position: relative;
      z-index: 2;
    }

    .input-wrap {
      flex: 1;
      display: flex;
      align-items: center;
      height: var(--composer-control-height);
      padding: 0 var(--space-xs);
    }

    input {
      flex: 1;
      height: 100%;
      padding: 0;
      font-size: var(--font-size-sm);
      border: none;
      background: transparent;
      color: var(--text-primary);
      outline: none;
      font-family: var(--font-family);
      line-height: var(--line-height-normal);
    }

    input::placeholder {
      color: var(--text-secondary);
    }

    .send-targets {
      display: flex;
      gap: var(--space-xs);
      align-items: center;
      flex-shrink: 0;
    }

    .target-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-xs);
      min-width: calc(var(--space-2xl) + var(--space-sm));
      height: var(--composer-control-height);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      background: var(--surface-secondary);
      color: var(--text-primary);
      font-family: var(--font-family);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      line-height: var(--line-height-tight);
      padding: 0 var(--space-sm);
      cursor: pointer;
      transition: background-color var(--transition-normal), color var(--transition-normal), transform var(--transition-fast);
    }

    .target-btn:hover {
      background: var(--hover-overlay);
    }

    .target-btn.active[data-target="chat"] {
      background: var(--oracle-primary);
      color: var(--neutral-900);
    }

    .target-btn.active[data-target="both"] {
      background: var(--chat-bg);
      color: var(--neutral-white);
    }

    .target-btn.active[data-target="agent"] {
      color: var(--agent-accent);
      background: var(--module-agent-active);
    }

    .target-btn:active {
      transform: translateY(1px);
    }

    .target-btn svg {
      width: var(--font-size-sm);
      height: var(--font-size-sm);
    }

    .target-btn:focus-visible,
    .row-action:focus-visible {
      outline: none;
      box-shadow: 0 0 0 1px var(--focus-ring);
    }

    .drawer {
      position: absolute;
      left: 0;
      right: 0;
      bottom: calc(100% + var(--space-xs));
      max-height: 48vh;
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      background: var(--surface-primary);
      box-shadow: var(--shadow-md);
      overflow: hidden;
      z-index: 3;
      opacity: 0;
      transform: translateY(var(--space-xs));
      pointer-events: none;
      transition: opacity var(--transition-normal), transform var(--transition-normal);
    }

    .drawer.open {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }

    .drawer-header {
      position: sticky;
      top: 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
      padding: var(--space-sm) var(--space-sm);
      background: var(--surface-primary);
      border-bottom: 1px solid var(--border-subtle);
      z-index: 1;
    }

    .drawer-title {
      display: inline-flex;
      align-items: center;
      gap: var(--space-xs);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
    }

    .hint-chip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: calc(var(--space-md) + var(--space-xs));
      border-radius: var(--radius-sm);
      background: var(--surface-secondary);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      padding: 0 var(--space-xs);
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-medium);
      line-height: var(--line-height-tight);
      white-space: nowrap;
    }

    .listbox {
      margin: 0;
      padding: var(--space-xs) 0;
      list-style: none;
      max-height: 42vh;
      overflow-y: auto;
      overflow-x: hidden;
      width: auto;
    }

    .suggestion-row {
      display: flex;
      align-items: center;
      flex-wrap: nowrap;
      gap: var(--space-sm);
      width: calc(100% - (6 * var(--space-xs)));
      max-width: calc(100% - (6 * var(--space-xs)));
      margin: 0 var(--space-xs) var(--space-xs);
      padding: var(--space-xs) var(--space-sm);
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      background: transparent;
      color: inherit;
      text-align: left;
      cursor: pointer;
      position: relative;
      transition: background-color var(--transition-normal), border-color var(--transition-normal), transform var(--transition-fast);
    }

    .suggestion-row::after {
      content: "";
      position: absolute;
      left: var(--space-sm);
      right: var(--space-sm);
      bottom: calc(-1 * var(--space-xs));
      border-bottom: 1px solid var(--border-subtle);
    }

    .suggestion-row:hover {
      background: var(--hover-overlay);
      border-color: var(--border-subtle);
      transform: translateY(-1px);
    }

    .suggestion-row.active {
      background: var(--module-agent-active);
      border-color: var(--agent-border);
    }

    .suggestion-row.active::before {
      content: "";
      position: absolute;
      left: 0;
      top: var(--space-xs);
      bottom: var(--space-xs);
      width: 1px;
      background: var(--agent-accent);
      border-radius: var(--radius-full);
    }

    .suggestion-row:active {
      background: var(--active-overlay);
      transform: translateY(0);
    }

    .suggestion-row:last-child::after {
      content: none;
    }

    .icon-box {
      width: calc(var(--space-xl) + var(--space-xs));
      height: calc(var(--space-xl) + var(--space-xs));
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-sm);
      background: var(--surface-secondary);
      color: var(--agent-accent);
      border: 1px solid var(--border-subtle);
    }

    .icon-box svg {
      width: var(--font-size-base);
      height: var(--font-size-base);
      flex-shrink: 0;
    }

    .row-title {
      color: var(--text-primary);
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-bold);
      line-height: var(--line-height-tight);
      margin-bottom: 0;
    }

    .row-description {
      color: var(--text-secondary);
      font-size: var(--font-size-sm);
      line-height: var(--line-height-normal);
      font-weight: var(--font-weight-normal);
    }

    .row-copy {
      display: flex;
      flex-direction: column;
      gap: var(--space-xs);
      flex: 1;
      min-width: 0;
      overflow: hidden;
    }

    .row-title,
    .row-description {
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .row-title {
      white-space: nowrap;
    }

    .row-description {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .row-actions {
      display: inline-flex;
      align-items: center;
      gap: var(--space-xs);
      flex-shrink: 0;
      margin-left: auto;
      padding-left: var(--space-xs);
      border-left: 1px solid var(--border-subtle);
      white-space: nowrap;
    }

    .row-action {
      height: calc(var(--space-lg) + var(--space-xs));
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      padding: 0 var(--space-xs);
      background: transparent;
      color: var(--text-secondary);
      cursor: pointer;
      font-family: var(--font-family);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      transition: background-color var(--transition-normal), color var(--transition-normal), transform var(--transition-fast);
    }

    .row-action:hover {
      color: var(--text-primary);
      background: var(--hover-overlay);
    }

    .row-action[data-target="chat"] {
      color: var(--oracle-primary);
    }

    .row-action[data-target="agent"] {
      color: var(--agent-accent);
    }

    .row-action:active {
      transform: translateY(1px);
    }

    .empty-state {
      margin: var(--space-xs);
      border-radius: var(--radius-sm);
      border: 1px dashed var(--border-secondary);
      padding: var(--space-sm);
      color: var(--text-secondary);
      font-size: var(--font-size-sm);
    }

    @media (max-width: 600px) {
      .composer {
        align-items: center;
        flex-wrap: wrap;
      }

      .input-wrap {
        width: 100%;
      }

      .send-targets {
        width: 100%;
        justify-content: flex-end;
      }

      .target-btn {
        flex: 0 1 auto;
        min-width: 0;
      }

      .suggestion-row {
        flex-wrap: wrap;
        gap: var(--space-xs);
      }

      .row-actions {
        margin-left: 0;
        width: 100%;
        justify-content: flex-end;
        border-left: none;
        padding-left: 0;
      }

      .row-title {
        font-size: var(--font-size-sm);
      }

      .row-description {
        font-size: var(--font-size-xs);
      }
    }

    @media (prefers-reduced-motion: reduce) {
      .drawer,
      .suggestion-row,
      .target-btn,
      .row-action {
        transition: none;
      }
    }
  `
  // #endregion Styles

  // #region Actions
  private get filteredSuggestions(): QuickQuery[] {
    const term = this.#filterTerm.trim().toLowerCase();
    if (!term) return QUICK_QUERIES;

    const ranked = QUICK_QUERIES
      .map((query) => {
        const title = query.title.toLowerCase();
        const description = query.description.toLowerCase();
        const text = query.query.toLowerCase();

        let rank = Number.POSITIVE_INFINITY;
        if (title.startsWith(term)) rank = 0;
        else if (title.includes(term)) rank = 1;
        else if (description.includes(term)) rank = 2;
        else if (text.includes(term)) rank = 3;

        return { query, rank };
      })
      .filter((item) => item.rank !== Number.POSITIVE_INFINITY)
      .sort((a, b) => a.rank - b.rank || a.query.title.localeCompare(b.query.title));

    return ranked.map((item) => item.query);
  }

  private optionId(index: number): string {
    return `quick-option-${index}`;
  }

  private openDrawer() {
    this.#drawerOpen = true;
    if (this.filteredSuggestions.length > 0 && this.#activeSuggestionIndex < 0) {
      this.#activeSuggestionIndex = 0;
    }
  }

  private closeDrawer() {
    this.#drawerOpen = false;
    this.#activeSuggestionIndex = -1;
  }

  private scheduleFilterUpdate(nextValue: string) {
    if (this.filterDebounceTimer) {
      window.clearTimeout(this.filterDebounceTimer);
    }
    this.filterDebounceTimer = window.setTimeout(() => {
      this.#filterTerm = nextValue.trim();
      this.#activeSuggestionIndex = this.filteredSuggestions.length > 0 ? 0 : -1;
    }, 120);
  }

  private async sendQuery(rawQuery: string, target: SendTarget = this.#defaultTarget) {
    const query = rawQuery.trim();
    if (!query || !this.router) return;

    try {
      if (target === "chat" || target === "both") {
        this.router.sendTextMessage(this.llmDefaultServer, query);
      }
      if (target === "agent" || target === "both") {
        this.router.sendTextMessage(this.agentDefaultServer, query);
      }
      this.#inputValue = "";
      this.#filterTerm = "";
      this.closeDrawer();
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  }

  private handlePointerDownOutside = (event: PointerEvent) => {
    if (!this.#drawerOpen) return;
    if (!event.composedPath().includes(this)) {
      this.closeDrawer();
    }
  }

  private handleInputFocus() {
    this.openDrawer();
  }

  private handleInputChange(e: Event) {
    const nextValue = (e.target as HTMLInputElement).value;
    this.#inputValue = nextValue;
    this.scheduleFilterUpdate(nextValue);
    this.openDrawer();
  }

  private moveActiveSuggestion(delta: 1 | -1) {
    const items = this.filteredSuggestions;
    if (!items.length) {
      this.#activeSuggestionIndex = -1;
      return;
    }

    if (this.#activeSuggestionIndex < 0) {
      this.#activeSuggestionIndex = delta > 0 ? 0 : items.length - 1;
      return;
    }

    this.#activeSuggestionIndex =
      (this.#activeSuggestionIndex + delta + items.length) % items.length;
  }

  private handlePressKey(e: KeyboardEvent) {
    if (e.key === "Escape") {
      if (this.#drawerOpen) {
        e.preventDefault();
        this.closeDrawer();
      }
      return;
    }

    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!this.#drawerOpen) this.openDrawer();
      e.preventDefault();
      this.moveActiveSuggestion(e.key === "ArrowDown" ? 1 : -1);
      return;
    }

    if (e.key !== "Enter") return;

    e.preventDefault();

    if (e.ctrlKey || e.metaKey) {
      this.sendQuery(this.#inputValue, this.#defaultTarget);
      return;
    }

    if (this.#drawerOpen && this.#activeSuggestionIndex >= 0) {
      const selected = this.filteredSuggestions[this.#activeSuggestionIndex];
      if (selected) {
        this.sendQuery(selected.query, this.#defaultTarget);
        return;
      }
    }

    this.sendQuery(this.#inputValue, this.#defaultTarget);
  }

  private handleTargetClick(target: SendTarget) {
    this.#defaultTarget = target;
    this.sendQuery(this.#inputValue, target);
  }

  private handleRowSend(item: QuickQuery, target: SendTarget = this.#defaultTarget) {
    this.sendQuery(item.query, target);
  }

  private renderIcon(icon: QuickQueryIcon) {
    switch (icon) {
      case "pin":
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12Z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>`;
      case "warning":
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.3 3.9-8 13.8A2 2 0 0 0 4 20.7h16a2 2 0 0 0 1.7-3l-8-13.8a2 2 0 0 0-3.4 0Z"></path><path d="M12 9v5"></path><path d="M12 18h.01"></path></svg>`;
      case "metrics":
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V9"></path><path d="M10 20V4"></path><path d="M16 20v-7"></path><path d="M22 20H2"></path></svg>`;
      case "status":
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m13 2-9 12h6l-1 8 9-12h-6z"></path></svg>`;
      case "shield":
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 5 6v6c0 5 3.4 8.6 7 10 3.6-1.4 7-5 7-10V6z"></path><path d="m9.5 12 2 2 3-3.5"></path></svg>`;
      case "report":
      default:
        return svg`<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2h8l4 4v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"></path><path d="M16 2v4h4"></path><path d="M9 12h6"></path><path d="M9 16h6"></path></svg>`;
    }
  }

  private renderTargetIcon(target: SendTarget) {
    switch (target) {
      case "chat":
        return svg`<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"></path></svg>`;
      case "both":
        return svg`<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="8" height="8" rx="1"></rect><rect x="13" y="3" width="8" height="8" rx="1"></rect><rect x="8" y="13" width="8" height="8" rx="1"></rect></svg>`;
      case "agent":
      default:
        return svg`<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m13 2-9 12h6l-1 8 9-12h-6z"></path></svg>`;
    }
  }

  private renderTargetButton(target: SendTarget, label: string) {
    const isActive = this.#defaultTarget === target;
    return html`
      <button
        type="button"
        class="target-btn ${isActive ? "active" : ""}"
        data-target=${target}
        @click=${() => this.handleTargetClick(target)}
        aria-pressed=${isActive ? "true" : "false"}
      >
        <span aria-hidden="true">${this.renderTargetIcon(target)}</span>
        ${label}
      </button>
    `;
  }
  // #endregion Actions

  // #region Render
  render() {
    const suggestions = this.filteredSuggestions;
    const hasMatches = suggestions.length > 0;
    const label = this.#filterTerm.length > 0 ? "Matching queries" : "Suggested queries";

    return html`
      <div class="composer-shell">
        <div class="drawer ${this.#drawerOpen ? "open" : ""}" aria-hidden=${this.#drawerOpen ? "false" : "true"}>
          <div class="drawer-header">
            <span class="drawer-title">
              <span aria-hidden="true">${this.renderIcon("status")}</span>
              ${label}
            </span>
            <span class="hint-chip">&uarr;&darr; to navigate</span>
          </div>

          <ul class="listbox" id=${this.#drawerId} role="listbox" aria-label=${label}>
            ${hasMatches
              ? suggestions.map(
                  (item, index) => html`
                    <li
                      id=${this.optionId(index)}
                      class="suggestion-row ${this.#activeSuggestionIndex === index ? "active" : ""}"
                      role="option"
                      aria-selected=${this.#activeSuggestionIndex === index ? "true" : "false"}
                      @mouseenter=${() => (this.#activeSuggestionIndex = index)}
                      @click=${() => this.handleRowSend(item)}
                    >
                      <span class="icon-box" aria-hidden="true">${this.renderIcon(item.icon)}</span>
                      <span class="row-copy">
                        <div class="row-title">${item.title}</div>
                        <div class="row-description">${item.description}</div>
                      </span>
                      <span class="row-actions">
                        <button
                          type="button"
                          class="row-action"
                          data-target="chat"
                          @click=${(e: Event) => {
                            e.stopPropagation();
                            this.handleRowSend(item, "chat");
                          }}
                        >
                          Chat
                        </button>
                        <button
                          type="button"
                          class="row-action"
                          data-target="both"
                          @click=${(e: Event) => {
                            e.stopPropagation();
                            this.handleRowSend(item, "both");
                          }}
                        >
                          Both
                        </button>
                        <button
                          type="button"
                          class="row-action"
                          data-target="agent"
                          @click=${(e: Event) => {
                            e.stopPropagation();
                            this.handleRowSend(item, "agent");
                          }}
                        >
                          Agent
                        </button>
                      </span>
                    </li>
                  `,
                )
              : html`
                  <li class="empty-state" role="option" aria-selected="false">
                    <div>No matching queries</div>
                    <div>Press Enter to send your text</div>
                  </li>
                `}
          </ul>
        </div>

        <div class="composer">
          <div class="input-wrap">
            <input
              id="chat-composer-input"
              type="text"
              .value=${this.#inputValue}
              @focus=${this.handleInputFocus}
              @input=${this.handleInputChange}
              @keydown=${this.handlePressKey}
              role="combobox"
              aria-autocomplete="list"
              aria-expanded=${this.#drawerOpen ? "true" : "false"}
              aria-controls=${this.#drawerId}
              aria-activedescendant=${this.#activeSuggestionIndex >= 0
                ? this.optionId(this.#activeSuggestionIndex)
                : nothing}
              placeholder="Start typing to search queries or enter your own..."
            />
          </div>

          <div class="send-targets">
            ${this.renderTargetButton("chat", "Chat")}
            ${this.renderTargetButton("both", "Both")}
            ${this.renderTargetButton("agent", "Agent")}
          </div>
        </div>
      </div>
    `
  }
  // #endregion Render
}
// #endregion Component

// #region Element Registration
declare global {
  interface HTMLElementTagNameMap {
    "chat-input": ChatInput
  }
}
// #endregion Element Registration
