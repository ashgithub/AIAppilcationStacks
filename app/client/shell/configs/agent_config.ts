import { EnhancedAgentAppConfig, ToolAssignments } from "./types.js";

const agents = {
  "place_finder_agent": {
    model: "xai.grok-4-fast-non-reasoning",
    temperature: 0.7,
    name: "place_finder_agent",
    systemPrompt: "You are an agent that is specialized on finding different restaurants/caffeterias depending on type of cuisine. Return your answer in the best way possible so other LLM can read the information and proceed. Only return a list of the names of restaurants/caffeterias found.",
    toolsEnabled: ["get_restaurants", "get_cafes"]
  },
  "data_finder_agent": {
    model: "openai.gpt-4.1",
    temperature: 0.7,
    name: "data_finder_agent",
    systemPrompt: "You are an agent expert in finding restaurant data.You will receive the information about a list of restaurants or caffeterias to find information about. Your job is to gather that information and pass the full data to a new agent that will respond to the user. Important, consider including links, image references and other UI data to be rendered during next steps. Consider that caffeteria or restaurant data should be complete, use tools as required according to context. Make sure to use the exact restaurant names from information.",
    toolsEnabled: ["get_restaurant_data", "get_cafe_data"]
  },
  "presenter_agent": {
    model: "xai.grok-4-fast-non-reasoning",
    temperature: 0.7,
    name: "presenter_agent",
    systemPrompt: "",
    toolsEnabled: []
  }
};

const toolAssignments: ToolAssignments = {
  "get_restaurants": "place_finder_agent",
  "get_cafes": "place_finder_agent",
  "get_restaurant_data": "data_finder_agent",
  "get_cafe_data": "data_finder_agent"
};

export const agentConfig: EnhancedAgentAppConfig = {
  agents,
  toolAssignments
};
