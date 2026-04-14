import axios from "axios";

export async function askOllama(prompt: string, system: string) {
  const baseUrl = process.env.OLLAMA_BASE_URL || "http://localhost:11434";
  const { data } = await axios.post(`${baseUrl}/api/generate`, {
    model: "llama3",
    prompt: `${system}\n\n${prompt}`,
    stream: false
  });

  return data.response?.trim?.() || "";
}
