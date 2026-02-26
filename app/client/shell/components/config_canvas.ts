import { LitElement, html, css } from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { AppConfigType, ConfigData, AgentAppConfig, LLMConfig, TraditionalConfig, EnhancedAgentAppConfig, ToolAssignments } from "../configs/types.js"
import { designTokensCSS, buttonStyles, colors, radius, spacing } from "../theme/design-tokens.js"

@customElement("agent-config-canvas")
export class AgentConfigCanvas extends LitElement {
  @property({ type: Boolean }) accessor open = false;

  @property({ type: String })
  accessor serverURL = "http://localhost:10002/config"

  @property({ type: String })
  accessor configType: AppConfigType = 'agent';

  @property({ type: Object })
  accessor configData: ConfigData = {};

  @state() accessor activeTab: string = '';

  @state() accessor responseMessage = "";

  private handleAgentToolChange(agentName: string, tool: string, checked: boolean) {
    if (this.configType !== 'agent' || !this.configData) return;

    const agentConfig = this.configData as AgentAppConfig;
    if (checked) {
      agentConfig[agentName].toolsEnabled = [...agentConfig[agentName].toolsEnabled, tool];
    } else {
      agentConfig[agentName].toolsEnabled = agentConfig[agentName].toolsEnabled.filter(t => t !== tool);
    }
    this.configData = { ...agentConfig };
  }

  private handleLLMToolChange(tool: string, checked: boolean) {
    if (this.configType !== 'llm' || !this.configData) return;

    const llmConfig = this.configData as LLMConfig;
    if (checked) {
      llmConfig.toolsEnabled = [...llmConfig.toolsEnabled, tool];
    } else {
      llmConfig.toolsEnabled = llmConfig.toolsEnabled.filter(t => t !== tool);
    }
    this.configData = { ...llmConfig };
  }

  private handleTraditionalFieldChange(field: string, value: string) {
    if (this.configType !== 'traditional' || !this.configData) return;

    const traditionalConfig = this.configData as TraditionalConfig;
    traditionalConfig[field] = value;
    this.configData = { ...traditionalConfig };
  }

  static styles = css`
    ${designTokensCSS}
    ${buttonStyles}

    :host {
      display: flex;
      align-items: center;
      font-family: var(--font-family);
      margin: 0;
    }

    .trigger-btn {
      padding: var(--space-sm);
      border: 1px solid var(--agent-bg-secondary);
      border-radius: var(--radius-sm);
      background: var(--agent-bg);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      transition: all var(--transition-normal);
      line-height: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 32px;
      min-width: 32px;
      box-sizing: border-box;
    }

    .trigger-btn:hover {
      background: var(--neutral-500);
      box-shadow: var(--shadow-sm);
    }

    /* Sidebar Overlay */
    .sidebar-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 999;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0.3s ease;
    }

    .sidebar-overlay.open {
      opacity: 1;
      visibility: visible;
    }

    /* Sidebar Panel */
    .sidebar {
      position: fixed;
      top: 0;
      right: 0;
      width: 400px;
      max-width: 90vw;
      height: 100vh;
      background: var(--agent-bg);
      z-index: 1000;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      display: flex;
      flex-direction: column;
      box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
    }

    .sidebar.open {
      transform: translateX(0);
    }

    .sidebar-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--space-md) var(--space-lg);
      border-bottom: 1px solid var(--agent-bg-secondary);
      background: var(--agent-bg-secondary);
    }

    .sidebar-header h3 {
      margin: 0;
      color: var(--text-primary);
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
    }

    .close-btn {
      background: transparent;
      border: none;
      color: var(--text-secondary);
      font-size: var(--font-size-xl);
      cursor: pointer;
      padding: var(--space-xs);
      width: 32px;
      height: 32px;
      line-height: 1;
      border-radius: var(--radius-sm);
      transition: all 0.2s ease;
    }

    .close-btn:hover {
      color: var(--text-primary);
      background: var(--hover-overlay);
    }

    .sidebar-content {
      flex: 1;
      overflow-y: hidden;
      padding: var(--space-lg);
    }

    .sidebar-footer {
      padding: var(--space-md) var(--space-lg);
      border-top: 1px solid var(--agent-bg-secondary);
      display: flex;
      gap: var(--space-sm);
      justify-content: flex-end;
    }

    /* Form Styles */
    .form-group {
      margin-bottom: var(--space-lg);
    }

    label {
      display: block;
      margin-bottom: var(--space-xs);
      font-weight: var(--font-weight-medium);
      color: var(--text-secondary);
      font-size: var(--font-size-sm);
    }

    select, input, textarea {
      width: 100%;
      padding: var(--space-sm);
      border: 1px solid var(--agent-bg-secondary);
      border-radius: var(--radius-sm);
      background: var(--agent-bg-secondary);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      box-sizing: border-box;
      font-family: var(--font-family);
    }

    select:focus, input:focus, textarea:focus {
      outline: none;
      border-color: var(--color-info);
    }

    input[type="number"] {
      width: auto;
      max-width: 120px;
    }

    textarea {
      resize: vertical;
      min-height: 80px;
    }

    /* Tab Styles */
    .tabs {
      display: flex;
      gap: var(--space-xs);
      margin-bottom: var(--space-lg);
      flex-wrap: wrap;
    }

    .tabs .btn-pill {
      text-transform: capitalize;
    }

    .tabs .btn-pill.active {
      background: var(--color-info);
      color: var(--neutral-white);
      border-color: var(--color-info);
    }

    /* Tools Section */
    .tools-section {
      border-top: 1px solid var(--agent-bg-secondary);
      padding-top: var(--space-lg);
      margin-top: var(--space-lg);
    }

    .tools-section h4 {
      margin: 0 0 var(--space-xs) 0;
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-semibold);
    }

    .tools-description {
      margin: 0 0 var(--space-md) 0;
      color: var(--text-secondary);
      font-size: var(--font-size-xs);
    }

    .tool-assignment {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--space-sm);
      background: var(--agent-bg-secondary);
      border-radius: var(--radius-sm);
      margin-bottom: var(--space-xs);
    }

    .tool-name {
      font-weight: var(--font-weight-medium);
      color: var(--text-primary);
      font-family: monospace;
      font-size: var(--font-size-xs);
      background: var(--agent-bg);
      padding: var(--space-xs) var(--space-sm);
      border-radius: var(--radius-xs);
    }

    .tool-assignment select {
      width: auto;
      min-width: 140px;
    }

    /* Toggle Group */
    .toggle-group {
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }

    .toggle-item {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      cursor: pointer;
      user-select: none;
    }

    .toggle-item input {
      display: none;
    }

    .toggle-switch {
      position: relative;
      width: 36px;
      height: 20px;
      background: var(--neutral-600);
      border-radius: 10px;
      transition: background 0.2s ease;
      flex-shrink: 0;
    }

    .toggle-switch::after {
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      width: 16px;
      height: 16px;
      background: var(--neutral-white);
      border-radius: 50%;
      transition: transform 0.2s ease;
    }

    .toggle-item input:checked + .toggle-switch {
      background: var(--color-success);
    }

    .toggle-item input:checked + .toggle-switch::after {
      transform: translateX(16px);
    }

    .toggle-item:hover .toggle-switch {
      opacity: 0.9;
    }

    .toggle-label {
      font-weight: var(--font-weight-normal);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
    }

    /* Action Buttons - use buttonStyles */

    /* Response Message */
    .response {
      margin-top: var(--space-md);
      padding: var(--space-sm);
      border-radius: var(--radius-sm);
      font-size: var(--font-size-sm);
    }

    .response.success {
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid var(--color-success);
      color: var(--color-success);
    }

    .response.error {
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid var(--color-error);
      color: var(--color-error);
    }
  `
      
      async send(): Promise<void> {
        let inputData: any = {};
        
        switch (this.configType) {
          case 'agent':
            const enhancedConfig = this.configData as EnhancedAgentAppConfig;
        inputData = Object.keys(enhancedConfig.agents).reduce((acc, agentName) => {
          acc[agentName] = {
            model: enhancedConfig.agents[agentName].model,
            temperature: enhancedConfig.agents[agentName].temperature,
            name: enhancedConfig.agents[agentName].name,
            system_prompt: enhancedConfig.agents[agentName].systemPrompt,
            tools_enabled: enhancedConfig.agents[agentName].toolsEnabled
          };
          return acc;
        }, {} as any);
        break;
      case 'llm':
        const llmConfig = this.configData as LLMConfig;
        inputData = {
          model: llmConfig.model,
          temperature: llmConfig.temperature,
          name: llmConfig.name,
          system_prompt: llmConfig.systemPrompt,
          tools_enabled: llmConfig.toolsEnabled
        };
        break;
      case 'traditional':
        inputData = this.configData as TraditionalConfig;
        break;
    }

    try {
      console.log(inputData)
      const response = await fetch(this.serverURL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(inputData)
      });

      const result = await response.json();

      if (result.status === "success") {
        this.responseMessage = result.message;
      } else {
        this.responseMessage = `Error: ${result.message}`;
      }
    } catch (error) {
      this.responseMessage = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
    }
  }

  render() {
    const availableModels = [
      "xai.grok-4",
      "xai.grok-4-fast-non-reasoning",
      "meta.llama-4-scout-17b-16e-instruct",
      "openai.gpt-4.1",
      "openai.gpt-oss-120b"
    ];

    const availableTools = [
      "query_database",
      "search_knowledge_base",
      "get_analytics",
      "generate_report"
    ];

    const availableDBTypes = [
      "MySQL",
      "PostgreSQL",
      "SQLite",
      "MongoDB"
    ];

    const availableThemes = [
      "default",
      "dark",
      "light"
    ];

    let title = "Configuration";
    let content: any = null;

    switch (this.configType) {
      case 'agent':
        title = "Agent Configuration";
        const enhancedConfig = this.configData as EnhancedAgentAppConfig;
        const agentNames = enhancedConfig?.agents ? Object.keys(enhancedConfig.agents) : [];

        if (!this.activeTab && agentNames.length > 0) {
          this.activeTab = agentNames[0];
        }

        const activeAgent = enhancedConfig?.agents?.[this.activeTab];

        content = html`
          ${agentNames.length > 0 ? html`
            <div class="tabs">
              ${agentNames.map(agentName => html`
                <button
                  class="btn btn-pill btn-secondary ${this.activeTab === agentName ? 'active' : ''}"
                  @click=${() => this.activeTab = agentName}
                >
                  ${agentName.replace(/_/g, ' ')}
                </button>
              `)}
            </div>

            ${activeAgent ? html`
              <div class="form-group">
                <label>Model</label>
                <select
                  .value=${activeAgent.model}
                  @change=${(e: Event) => {
                    const newConfig = { ...enhancedConfig };
                    newConfig.agents[this.activeTab].model = (e.target as HTMLSelectElement).value;
                    this.configData = newConfig;
                  }}
                >
                  ${availableModels.map(model => html`
                    <option value=${model} ?selected=${activeAgent.model === model}>${model}</option>
                  `)}
                </select>
              </div>

              <div class="form-group">
                <label>Temperature</label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  .value=${activeAgent.temperature.toString()}
                  @input=${(e: Event) => {
                    const newConfig = { ...enhancedConfig };
                    newConfig.agents[this.activeTab].temperature = parseFloat((e.target as HTMLInputElement).value) || 0;
                    this.configData = newConfig;
                  }}
                />
              </div>

              <div class="form-group">
                <label>Name</label>
                <input
                  type="text"
                  .value=${activeAgent.name}
                  @input=${(e: Event) => {
                    const newConfig = { ...enhancedConfig };
                    newConfig.agents[this.activeTab].name = (e.target as HTMLInputElement).value;
                    this.configData = newConfig;
                  }}
                />
              </div>

              <div class="form-group">
                <label>System Prompt</label>
                <textarea
                  .value=${activeAgent.systemPrompt}
                  @input=${(e: Event) => {
                    const newConfig = { ...enhancedConfig };
                    newConfig.agents[this.activeTab].systemPrompt = (e.target as HTMLTextAreaElement).value;
                    this.configData = newConfig;
                  }}
                ></textarea>
              </div>

              <div class="tools-section">
                <h4>Tool Assignments</h4>
                <p class="tools-description">Assign tools to this agent</p>
                ${availableTools.map(tool => {
                  const assignedAgent = enhancedConfig.toolAssignments?.[tool];
                  return html`
                    <div class="tool-assignment">
                      <span class="tool-name">${tool}</span>
                      <select
                        .value=${assignedAgent || ''}
                        @change=${(e: Event) => {
                          const selectedAgent = (e.target as HTMLSelectElement).value;
                          const newConfig = { ...enhancedConfig };
                          if (!newConfig.toolAssignments) newConfig.toolAssignments = {};

                          if (assignedAgent && newConfig.agents[assignedAgent]) {
                            const agentTools = newConfig.agents[assignedAgent].toolsEnabled;
                            newConfig.agents[assignedAgent].toolsEnabled = agentTools.filter(t => t !== tool);
                          }

                          if (selectedAgent) {
                            newConfig.toolAssignments[tool] = selectedAgent;
                            if (newConfig.agents[selectedAgent] && !newConfig.agents[selectedAgent].toolsEnabled.includes(tool)) {
                              newConfig.agents[selectedAgent].toolsEnabled = [...newConfig.agents[selectedAgent].toolsEnabled, tool];
                            }
                          } else {
                            delete newConfig.toolAssignments[tool];
                          }

                          this.configData = newConfig;
                        }}
                      >
                        <option value="">Unassigned</option>
                        ${agentNames.map(agent => html`
                          <option value=${agent} ?selected=${assignedAgent === agent}>
                            ${agent.replace(/_/g, ' ')}
                          </option>
                        `)}
                      </select>
                    </div>
                  `;
                })}
              </div>
            ` : ''}
          ` : html`<p style="color: var(--text-secondary)">No agents configured</p>`}
        `;
        break;

      case 'llm':
        title = "LLM Configuration";
        const llmConfig = this.configData as LLMConfig;
        content = html`
          <div class="form-group">
            <label>Model</label>
            <select
              .value=${llmConfig?.model || ''}
              @change=${(e: Event) => {
                const newConfig = { ...llmConfig };
                newConfig.model = (e.target as HTMLSelectElement).value;
                this.configData = newConfig;
              }}
            >
              ${availableModels.map(model => html`
                <option value=${model} ?selected=${llmConfig?.model === model}>${model}</option>
              `)}
            </select>
          </div>

          <div class="form-group">
            <label>Temperature</label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              .value=${llmConfig?.temperature?.toString() || '0.7'}
              @input=${(e: Event) => {
                const newConfig = { ...llmConfig };
                newConfig.temperature = parseFloat((e.target as HTMLInputElement).value) || 0;
                this.configData = newConfig;
              }}
            />
          </div>

          <div class="form-group">
            <label>Name</label>
            <input
              type="text"
              .value=${llmConfig?.name || ''}
              @input=${(e: Event) => {
                const newConfig = { ...llmConfig };
                newConfig.name = (e.target as HTMLInputElement).value;
                this.configData = newConfig;
              }}
            />
          </div>

          <div class="form-group">
            <label>System Prompt</label>
            <textarea
              .value=${llmConfig?.systemPrompt || ''}
              @input=${(e: Event) => {
                const newConfig = { ...llmConfig };
                newConfig.systemPrompt = (e.target as HTMLTextAreaElement).value;
                this.configData = newConfig;
              }}
            ></textarea>
          </div>

          <div class="form-group">
            <label>Tools Enabled</label>
            <div class="toggle-group">
              ${availableTools.map(tool => html`
                <label class="toggle-item">
                  <input
                    type="checkbox"
                    .checked=${llmConfig?.toolsEnabled?.includes(tool) || false}
                    @change=${(e: Event) => this.handleLLMToolChange(tool, (e.target as HTMLInputElement).checked)}
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">${tool}</span>
                </label>
              `)}
            </div>
          </div>
        `;
        break;

      case 'traditional':
        title = "App Settings";
        const traditionalConfig = this.configData as TraditionalConfig;
        content = html`
          <div class="form-group">
            <label>Database Type</label>
            <select
              .value=${traditionalConfig?.databaseType || ''}
              @change=${(e: Event) => this.handleTraditionalFieldChange('databaseType', (e.target as HTMLSelectElement).value)}
            >
              ${availableDBTypes.map(db => html`
                <option value=${db} ?selected=${traditionalConfig?.databaseType === db}>${db}</option>
              `)}
            </select>
          </div>

          <div class="form-group">
            <label>Business Branch</label>
            <input
              type="text"
              .value=${traditionalConfig?.businessBranch || ''}
              @input=${(e: Event) => this.handleTraditionalFieldChange('businessBranch', (e.target as HTMLInputElement).value)}
            />
          </div>

          <div class="form-group">
            <label>API Endpoint</label>
            <input
              type="text"
              .value=${traditionalConfig?.apiEndpoint || ''}
              @input=${(e: Event) => this.handleTraditionalFieldChange('apiEndpoint', (e.target as HTMLInputElement).value)}
            />
          </div>

          <div class="form-group">
            <label>Theme</label>
            <select
              .value=${traditionalConfig?.theme || ''}
              @change=${(e: Event) => this.handleTraditionalFieldChange('theme', (e.target as HTMLSelectElement).value)}
            >
              ${availableThemes.map(theme => html`
                <option value=${theme} ?selected=${traditionalConfig?.theme === theme}>${theme}</option>
              `)}
            </select>
          </div>
        `;
        break;
    }

    return html`
      <button class="trigger-btn" @click=${() => { this.open = true; }}>⚙️</button>
      
      <div class="sidebar-overlay ${this.open ? 'open' : ''}" @click=${() => { this.open = false; }}></div>
      
      <div class="sidebar ${this.open ? 'open' : ''}">
        <div class="sidebar-header">
          <h3>${title}</h3>
          <button class="close-btn" @click=${() => { this.open = false; }}>×</button>
        </div>
        
        <div class="sidebar-content">
          ${content}
          
          ${this.responseMessage ? html`
            <div class="response ${this.responseMessage.startsWith('Error') ? 'error' : 'success'}">
              ${this.responseMessage}
            </div>
          ` : ''}
        </div>
        
        <div class="sidebar-footer">
          <button class="btn btn-secondary" @click=${() => { this.open = false; }}>Cancel</button>
          <button class="btn btn-success" @click=${this.send}>Save</button>
        </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "agent-config-canvas": AgentConfigCanvas
  }
}