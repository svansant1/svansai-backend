import OpenAI from "openai";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function askOpenAI(prompt: string, system: string) {
  const result = await client.chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0.3,
    messages: [
      { role: "system", content: system },
      { role: "user", content: prompt }
    ]
  });

  return result.choices[0]?.message?.content?.trim() || "";
}
