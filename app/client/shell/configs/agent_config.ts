import { EnhancedAgentAppConfig, ToolAssignments } from "./types.js";

const agents = {
  "nl2graphDB_agent": {
    model: "xai.grok-4-fast-reasoning",
    temperature: 0.7,
    name: "nl2graphDB_agent",
    systemPrompt: "You are an agent expert in converting Natural Language to actual PGQL queries",
    toolsEnabled: ["talk2DB", "semantic_search"]
  },
  "rag_agent": {
    model: "openai.gpt-4.1",
    temperature: 0.7,
    name: "rag_agent",
    systemPrompt: "You are an agent expert in performing RAG pipelines and semantic searches",
    toolsEnabled: ["talk2DB", "semantic_search"]
  },
  "ui_assembly_agent": {
    model: "xai.grok-4-fast-reasoning",
    temperature: 0.7,
    name: "ui_assembly_agent",
    systemPrompt: "",
    toolsEnabled: []
  }
};

const toolAssignments: ToolAssignments = {
  "talk2DB": "nl2graphDB_agent",
  "semantic_search": "nl2graphDB_agent",
};

export const agentConfig: EnhancedAgentAppConfig = {
  agents,
  toolAssignments
};
