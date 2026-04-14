import axios from "axios";

export async function semanticRoute(question: string) {
  const url = process.env.PYTHON_BRAIN_URL || "http://localhost:8001";

  try {
    const { data } = await axios.post(`${url}/retrieve`, { question, topK: 5 });
    const matches = data.matches || [];
    const confidence = matches[0]?.score ?? 0;
    return {
      strong: confidence >= 0.85,
      confidence,
      matches
    };
  } catch {
    return { strong: false, confidence: 0, matches: [] };
  }
}
