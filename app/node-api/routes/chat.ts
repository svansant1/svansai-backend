import { Router } from "express";
import { getCachedAnswer, setCachedAnswer } from "../services/cache/redisCache.js";
import { semanticRoute } from "../services/routing/semanticRouter.js";
import { tieredFallback } from "../services/providers/fallbackController.js";
import { logLearnedAnswer } from "../services/workflows/learningLogger.js";
import { emitStatus } from "../socket.js";

const router = Router();

router.post("/", async (req, res) => {
  const { message, sessionId } = req.body || {};
  const question = String(message || "").trim();

  if (!question) {
    return res.status(400).json({ error: "Message is required." });
  }

  emitStatus(sessionId, "cache-check");
  const cached = await getCachedAnswer(question);
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
  const routed = await semanticRoute(question);

  if (routed.strong && routed.matches[0]) {
    const answer = routed.matches[0].answer;
    await setCachedAnswer(question, answer);
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
  const system = "You are SVANSAI. Answer directly and naturally.";
  const prompt = `Question:\n${question}\n\nKnown context:\n${routed.matches.map((m: any) => `- ${m.answer}`).join("\n")}`;
  const fallback = await tieredFallback(prompt, system);

  if (fallback.answer) {
    await setCachedAnswer(question, fallback.answer);
    await logLearnedAnswer({
      question,
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
    answer: "I couldn't generate a strong answer just now.",
    routeUsed: "final-fallback",
    providerUsed: "local",
    confidence: 0,
    learned: false
  });
});

export default router;
