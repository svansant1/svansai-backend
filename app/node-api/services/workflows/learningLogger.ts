import axios from "axios";

export async function logLearnedAnswer(payload: {
  question: string;
  answer: string;
  provider: string;
  confidence: number;
}) {
  const url = process.env.PYTHON_BRAIN_URL || "http://localhost:8001";
  await axios.post(`${url}/learn`, payload);
}
