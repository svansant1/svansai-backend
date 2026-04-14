import { GoogleGenerativeAI } from "@google/generative-ai";

const client = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY || "");

export async function askGoogle(prompt: string, system: string) {
  const model = client.getGenerativeModel({ model: "gemini-1.5-flash" });
  const result = await model.generateContent(`${system}\n\n${prompt}`);
  return result.response.text().trim();
}
