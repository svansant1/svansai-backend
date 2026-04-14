export type ProviderName = "local" | "openai" | "anthropic" | "google" | "ollama";

export type ChatRequest = {
  message: string;
  sessionId?: string;
};

export type RetrievedMemory = {
  id: string;
  question: string;
  answer: string;
  source: string;
  confidence: number;
  score: number;
};
