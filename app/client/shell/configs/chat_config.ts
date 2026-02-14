import { LLMConfig } from "./types.js";

export const chatConfig: LLMConfig = {
  model: "openai.gpt-4.1",
  temperature: 0.7,
  name: "chat_llm",
  systemPrompt: "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user queries.",
  toolsEnabled: []
};