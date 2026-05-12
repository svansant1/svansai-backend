import { Router } from "express";
import { getCachedAnswer, setCachedAnswer } from "../services/cache/redisCache.js";
import { semanticRoute } from "../services/routing/semanticRouter.js";
import { tieredFallback } from "../services/providers/fallbackController.js";
import { logLearnedAnswer } from "../services/workflows/learningLogger.js";
import { emitStatus } from "../socket.js";

const router = Router();

router.post("/", async (req, res) => {
  const { message, sessionId } = req.body || {};
  const userMessage = String(message || "").trim();

  if (!userMessage) {
    return res.status(400).json({ error: "Message is required." });
  }

  emitStatus(sessionId, "cache-check");
  const cached = await getCachedAnswer(userMessage);
  if (cached) {
    emitStatus(sessionId, "cache-hit");
    return res.json({
      answer: cached,
      routeUsed: "redis",
      providerUsed: "local",
      confidence: 1,
      learned: false
    });
  }

  emitStatus(sessionId, "semantic-route");
  const routed = await semanticRoute(userMessage);

  if (routed.strong && routed.matches[0]) {
    const answer = routed.matches[0].answer;
    await setCachedAnswer(userMessage, answer);
    emitStatus(sessionId, "local-memory-hit");
    return res.json({
      answer,
      routeUsed: "vector-memory",
      providerUsed: "local",
      confidence: routed.confidence,
      learned: false
    });
  }

  emitStatus(sessionId, "fallback-provider");
  const system = [
    "You are SVANSAI. Answer directly and naturally.",
    "The user may send a question, statement, instruction, greeting, correction, opinion, or fragment.",
    "Respond to the actual message and continue the conversation without requiring the user to rephrase it as a question."
  ].join(" ");
  const prompt = `User message:\n${userMessage}\n\nKnown context:\n${routed.matches.map((m: any) => `- ${m.answer}`).join("\n")}`;
  const fallback = await tieredFallback(prompt, system);

  if (fallback.answer) {
    await setCachedAnswer(userMessage, fallback.answer);
    await logLearnedAnswer({
      question: userMessage,
      answer: fallback.answer,
      provider: fallback.provider,
      confidence: 0.78
    });
    emitStatus(sessionId, "learned");
    return res.json({
      answer: fallback.answer,
      routeUsed: "provider-fallback",
      providerUsed: fallback.provider,
      confidence: 0.78,
      learned: true
    });
  }

  emitStatus(sessionId, "fallback-failed");
  return res.json({
    answer: "I received your message, but I couldn't generate a strong response just now. Try sending it again and I’ll respond directly.",
    routeUsed: "final-fallback",
    providerUsed: "local",
    confidence: 0,
    learned: false
  });
});

export default router;
