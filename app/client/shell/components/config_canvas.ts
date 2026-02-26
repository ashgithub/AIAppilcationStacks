import { LitElement, html, css } from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { AppConfigType, ConfigData, AgentAppConfig, LLMConfig, TraditionalConfig, EnhancedAgentAppConfig, ToolAssignments } from "../configs/types.js"
import { designTokensCSS, colors, radius, spacing } from "../theme/design-tokens.js"

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

    :host {
      display: block;
      font-family: var(--font-family);
      margin-top: var(--space-md);
    }

    button {
      padding: var(--space-sm);
      border: 1px solid var(--agent-bg-secondary);
      border-radius: var(--radius-sm);
      background: var(--agent-bg);
      color: var(--text-primary);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      transition: all var(--transition-normal);
    }

    button:hover {
      background: var(--neutral-500);
      box-shadow: var(--shadow-sm);
    }

    dialog {
      position: fixed;
      top: 80%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 90%;
      max-width: 600px;
      max-height: 80vh;
      overflow-y: auto;
      z-index: 1000;
      background: var(--chat-surface);
      border: none;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
      padding: var(--space-xl);
      color: var(--neutral-800);
    }

    dialog::backdrop {
      background: rgba(0, 0, 0, 0.5);
    }

    dialog h2 {
      margin-top: 0;
      color: var(--neutral-800);
    }

    dialog h3 {
      color: var(--neutral-800);
      margin-bottom: var(--space-md);
    }

    .form-group {
      margin-bottom: var(--space-lg);
    }

    label {
      display: block;
      margin-bottom: var(--space-sm);
      font-weight: var(--font-weight-bold);
      color: var(--neutral-700);
    }

    select, input, textarea {
      width: 100%;
      padding: var(--space-sm);
      border: 1px solid var(--neutral-300);
      border-radius: var(--radius-md);
      background: var(--neutral-white);
      color: var(--neutral-800);
      font-size: var(--font-size-base);
      box-sizing: border-box;
    }

    select:focus, input:focus, textarea:focus {
      outline: none;
      border-color: var(--color-info);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    input[type="number"] {
      width: auto;
      max-width: 200px;
    }

    textarea {
      resize: vertical;
      min-height: 100px;
    }

    .checkbox-group {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-md);
    }

    .checkbox-item {
      display: flex;
      align-items: center;
    }

    .checkbox-item input[type="checkbox"] {
      margin-right: var(--space-sm);
      accent-color: var(--color-info);
    }

    .checkbox-item label {
      font-weight: var(--font-weight-normal);
      color: var(--neutral-700);
    }

    .dialog-buttons {
      display: flex;
      gap: var(--space-md);
      justify-content: flex-end;
      margin-top: var(--space-xl);
    }

    .dialog-buttons button {
      padding: var(--space-sm) var(--space-lg);
      border: none;
      border-radius: var(--radius-md);
      font-size: var(--font-size-base);
      cursor: pointer;
      transition: background var(--transition-normal);
    }

    .send-btn {
      background: var(--color-success);
      color: var(--neutral-white);
    }

    .send-btn:hover {
      background: var(--color-success-dark);
    }

    .close-btn {
      background: var(--neutral-500);
      color: var(--neutral-white);
    }

    .close-btn:hover {
      background: var(--neutral-600);
    }

    .response {
      margin-top: var(--space-xl);
      padding: var(--space-md);
      border-radius: var(--radius-md);
      background: var(--neutral-50);
      border-left: 4px solid transparent;
    }

    .success {
      border-left-color: var(--color-success);
    }

    .error {
      border-left-color: var(--color-error);
      color: var(--color-error-dark);
    }

    /* Tab Styles */
    .tabs {
      display: flex;
      border-bottom: 2px solid var(--neutral-200);
      margin-bottom: var(--space-lg);
    }

    .tab-button {
      padding: var(--space-sm) var(--space-md);
      border: none;
      background: none;
      color: var(--neutral-500);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all var(--transition-normal);
      text-transform: capitalize;
    }

    .tab-button:hover {
      color: var(--neutral-700);
      background: var(--neutral-50);
    }

    .tab-button.active {
      color: var(--color-info);
      border-bottom-color: var(--color-info);
      background: rgba(59, 130, 246, 0.1);
    }

    .tab-content {
      margin-bottom: 2rem;
    }

    /* Tools Section Styles */
    .tools-section {
      border-top: 1px solid #e2e8f0;
      padding-top: 1.5rem;
      margin-top: 2rem;
    }

    .tools-section h3 {
      margin: 0 0 0.5rem 0;
      color: #1e293b;
      font-size: 1.125rem;
      font-weight: 600;
    }

    .tools-description {
      margin: 0 0 1.5rem 0;
      color: #64748b;
      font-size: 0.875rem;
      line-height: 1.4;
    }

    .tool-assignment {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem;
      background: #f8fafc;
      border-radius: 0.5rem;
      margin-bottom: 0.75rem;
      border: 1px solid #e2e8f0;
    }

    .tool-assignment:last-child {
      margin-bottom: 0;
    }

    .tool-name {
      font-weight: 500;
      color: #1e293b;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      background: #e2e8f0;
      padding: 0.25rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.875rem;
    }

    .tool-assignment select {
      width: auto;
      min-width: 200px;
      margin-left: 1rem;
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
      "get_restaurants",
      "get_cafes",
      "get_restaurant_data",
      "get_cafe_data"
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
        title = "Agent Team Configuration";
        const enhancedConfig = this.configData as EnhancedAgentAppConfig;
        const agentNames = Object.keys(enhancedConfig.agents);

        if (!this.activeTab && agentNames.length > 0) {
          this.activeTab = agentNames[0];
        }

        const activeAgent = enhancedConfig.agents[this.activeTab];

        content = html`
          <!-- Agent Tabs -->
          <div class="tabs">
            ${agentNames.map(agentName => html`
              <button
                class="tab-button ${this.activeTab === agentName ? 'active' : ''}"
                @click=${() => this.activeTab = agentName}
              >
                ${agentName.replace('_', ' ')}
              </button>
            `)}
          </div>

          <!-- Active Agent Configuration -->
          ${activeAgent ? html`
            <div class="tab-content">
              <div class="form-group">
                <label for="agent-model">Model:</label>
                <select
                  id="agent-model"
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
                <label for="agent-temperature">Temperature:</label>
                <input
                  id="agent-temperature"
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
                <label for="agent-name">Name:</label>
                <input
                  id="agent-name"
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
                <label for="agent-systemPrompt">System Prompt:</label>
                <textarea
                  id="agent-systemPrompt"
                  .value=${activeAgent.systemPrompt}
                  @input=${(e: Event) => {
                    const newConfig = { ...enhancedConfig };
                    newConfig.agents[this.activeTab].systemPrompt = (e.target as HTMLTextAreaElement).value;
                    this.configData = newConfig;
                  }}
                ></textarea>
              </div>
            </div>
          ` : ''}

          <!-- Tools Assignment Section -->
          <div class="tools-section">
            <h3>Tool Assignments</h3>
            <p class="tools-description">Assign tools to agents. Each tool can only be assigned to one agent.</p>
            ${availableTools.map(tool => {
              const assignedAgent = enhancedConfig.toolAssignments[tool];
              const availableAgents = agentNames.filter(agent => agent === assignedAgent || !Object.values(enhancedConfig.toolAssignments).includes(agent));

              return html`
                <div class="tool-assignment">
                  <span class="tool-name">${tool}</span>
                  <select
                    .value=${assignedAgent || ''}
                    @change=${(e: Event) => {
                      const selectedAgent = (e.target as HTMLSelectElement).value;
                      const newConfig = { ...enhancedConfig };

                      // Remove old assignment
                      if (assignedAgent) {
                        delete newConfig.toolAssignments[tool];
                        // Remove from agent's toolsEnabled
                        const agentTools = newConfig.agents[assignedAgent].toolsEnabled;
                        newConfig.agents[assignedAgent].toolsEnabled = agentTools.filter(t => t !== tool);
                      }

                      // Add new assignment
                      if (selectedAgent) {
                        newConfig.toolAssignments[tool] = selectedAgent;
                        // Add to agent's toolsEnabled
                        const agentTools = newConfig.agents[selectedAgent].toolsEnabled;
                        if (!agentTools.includes(tool)) {
                          newConfig.agents[selectedAgent].toolsEnabled = [...agentTools, tool];
                        }
                      }

                      this.configData = newConfig;
                    }}
                  >
                    <option value="">-- Not Assigned --</option>
                    ${availableAgents.map(agent => html`
                      <option value=${agent} ?selected=${assignedAgent === agent}>
                        ${agent.replace('_', ' ')}
                      </option>
                    `)}
                  </select>
                </div>
              `;
            })}
          </div>
        `;
        break;

      case 'llm':
        title = "LLM Configuration";
        const llmConfig = this.configData as LLMConfig;
        content = html`
          <div>
            <div class="form-group">
              <label for="llm-model">Model:</label>
              <select
                id="llm-model"
                .value=${llmConfig.model}
                @change=${(e: Event) => {
                  const newConfig = { ...llmConfig };
                  newConfig.model = (e.target as HTMLSelectElement).value;
                  this.configData = newConfig;
                }}
              >
                ${availableModels.map(model => html`
                  <option value=${model} ?selected=${llmConfig.model === model}>${model}</option>
                `)}
              </select>
            </div>

            <div class="form-group">
              <label for="llm-temperature">Temperature:</label>
              <input
                id="llm-temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                .value=${llmConfig.temperature.toString()}
                @input=${(e: Event) => {
                  const newConfig = { ...llmConfig };
                  newConfig.temperature = parseFloat((e.target as HTMLInputElement).value) || 0;
                  this.configData = newConfig;
                }}
              />
            </div>

            <div class="form-group">
              <label for="llm-name">Name:</label>
              <input
                id="llm-name"
                type="text"
                .value=${llmConfig.name}
                @input=${(e: Event) => {
                  const newConfig = { ...llmConfig };
                  newConfig.name = (e.target as HTMLInputElement).value;
                  this.configData = newConfig;
                }}
              />
            </div>

            <div class="form-group">
              <label for="llm-systemPrompt">System Prompt:</label>
              <textarea
                id="llm-systemPrompt"
                .value=${llmConfig.systemPrompt}
                @input=${(e: Event) => {
                  const newConfig = { ...llmConfig };
                  newConfig.systemPrompt = (e.target as HTMLTextAreaElement).value;
                  this.configData = newConfig;
                }}
              ></textarea>
            </div>

            <div class="form-group">
              <label>Tools Enabled:</label>
              <div class="checkbox-group">
                ${availableTools.map(tool => html`
                  <div class="checkbox-item">
                    <input
                      type="checkbox"
                      id="llm-${tool}"
                      .checked=${llmConfig.toolsEnabled.includes(tool)}
                      @change=${(e: Event) => this.handleLLMToolChange(tool, (e.target as HTMLInputElement).checked)}
                    />
                    <label for="llm-${tool}">${tool}</label>
                  </div>
                `)}
              </div>
            </div>
          </div>
        `;
        break;

      case 'traditional':
        title = "Application Configuration";
        const traditionalConfig = this.configData as TraditionalConfig;
        content = html`
          <div>
            <div class="form-group">
              <label for="db-type">Database Type:</label>
              <select
                id="db-type"
                .value=${traditionalConfig.databaseType}
                @change=${(e: Event) => this.handleTraditionalFieldChange('databaseType', (e.target as HTMLSelectElement).value)}
              >
                ${availableDBTypes.map(db => html`
                  <option value=${db} ?selected=${traditionalConfig.databaseType === db}>${db}</option>
                `)}
              </select>
            </div>

            <div class="form-group">
              <label for="business-branch">Business Branch:</label>
              <input
                id="business-branch"
                type="text"
                .value=${traditionalConfig.businessBranch}
                @input=${(e: Event) => this.handleTraditionalFieldChange('businessBranch', (e.target as HTMLInputElement).value)}
              />
            </div>

            <div class="form-group">
              <label for="api-endpoint">API Endpoint:</label>
              <input
                id="api-endpoint"
                type="text"
                .value=${traditionalConfig.apiEndpoint}
                @input=${(e: Event) => this.handleTraditionalFieldChange('apiEndpoint', (e.target as HTMLInputElement).value)}
              />
            </div>

            <div class="form-group">
              <label for="theme">Theme:</label>
              <select
                id="theme"
                .value=${traditionalConfig.theme}
                @change=${(e: Event) => this.handleTraditionalFieldChange('theme', (e.target as HTMLSelectElement).value)}
              >
                ${availableThemes.map(theme => html`
                  <option value=${theme} ?selected=${traditionalConfig.theme === theme}>${theme}</option>
                `)}
              </select>
            </div>
          </div>
        `;
        break;
    }

    return html`
      <button @click=${() => { this.open = true; this.shadowRoot?.querySelector('dialog')?.showModal(); }}>⚙️</button>
      <dialog ?open=${this.open} @close=${() => this.open = false}>
        <h3>${title}</h3>
        ${content}
        <div class="dialog-buttons">
          <button class="send-btn" @click=${this.send}>Send Configuration</button>
          <button class="close-btn" @click=${() => { this.open = false; this.shadowRoot?.querySelector('dialog')?.close(); }}>Close</button>
        </div>
        ${this.responseMessage ? html`
          <div class="response ${this.responseMessage.startsWith('Error') ? 'error' : 'success'}">
            ${this.responseMessage}
          </div>
        ` : ''}
      </dialog>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "agent-config-canvas": AgentConfigCanvas
  }
}