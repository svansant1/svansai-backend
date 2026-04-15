import OpenAI from "openai";

export async function askOpenAI(prompt: string, system: string) {
  const apiKey = process.env.OPENAI_API_KEY;

  if (!apiKey) {
    console.error("OPENAI ERROR: missing OPENAI_API_KEY");
    return "";
  }

  try {
    console.log("OPENAI REQUEST START");
    console.log("OPENAI SYSTEM:", system);
    console.log("OPENAI PROMPT:", prompt);

    const client = new OpenAI({ apiKey });

    const result = await client.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.3,
      messages: [
        { role: "system", content: system },
        { role: "user", content: prompt },
      ],
    });

    console.log("OPENAI RAW RESPONSE:", JSON.stringify(result, null, 2));

    const text = result.choices?.[0]?.message?.content?.trim() || "";

    console.log("OPENAI FINAL TEXT:", text || "[empty]");

    return text;
  } catch (error) {
    console.error("OPENAI ERROR:", error);
    return "";
  }
}