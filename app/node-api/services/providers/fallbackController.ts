import { askOpenAI } from "./openaiProvider.js";
import { askAnthropic } from "./anthropicProvider.js";
import { askGoogle } from "./googleProvider.js";
import { askOllama } from "./ollamaProvider.js";

export async function tieredFallback(prompt: string, system: string) {
  const order = ["openai", "anthropic", "google", "ollama"] as const;

  for (const provider of order) {
    try {
      let answer = "";

      if (provider === "openai") answer = await askOpenAI(prompt, system);
      if (provider === "anthropic") answer = await askAnthropic(prompt, system);
      if (provider === "google") answer = await askGoogle(prompt, system);
      if (provider === "ollama") answer = await askOllama(prompt, system);

      if (answer && answer.trim().length > 20) {
        return { provider, answer };
      }
    } catch {
      continue;
    }
  }

  return { provider: "local", answer: "" };
}
