import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function askAnthropic(prompt: string, system: string) {
  const result = await client.messages.create({
    model: "claude-3-5-sonnet-latest",
    max_tokens: 1000,
    system,
    messages: [{ role: "user", content: prompt }]
  });

  const text = result.content
    .map((item: any) => ("text" in item ? item.text : ""))
    .join("")
    .trim();

  return text;
}
